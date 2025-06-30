"""
Sync Scheduler Service
Automated sync scheduling and management for organizations
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import db
from src.services.comprehensive_cliniko_sync import ComprehensiveClinikoSync

logger = logging.getLogger(__name__)

class SyncScheduler:
    def __init__(self):
        self.sync_service = ComprehensiveClinikoSync()
        self.running_syncs: Dict[str, bool] = {}
        self.last_sync_times: Dict[str, datetime] = {}
        
    async def get_organizations_needing_sync(self, sync_interval_minutes: int = 240) -> List[str]:
        """
        Get list of organizations that need syncing based on their sync interval
        Only returns orgs that haven't been synced recently to prevent duplicates
        """
        try:
            cutoff_time = datetime.now() - timedelta(minutes=sync_interval_minutes)
            
            with db.get_cursor() as cursor:
                # Get organizations that haven't been synced recently
                query = """
                SELECT DISTINCT p.organization_id 
                FROM patients p
                LEFT JOIN service_integrations si ON p.organization_id = si.organization_id 
                    AND si.service_name = 'cliniko' AND si.is_active = true
                WHERE p.is_active = true 
                AND p.organization_id IS NOT NULL
                AND (
                    si.last_sync_at IS NULL 
                    OR si.last_sync_at < %s
                    OR si.organization_id IS NULL
                )
                """
                
                cursor.execute(query, [cutoff_time])
                rows = cursor.fetchall()
                
                # Filter out organizations that are currently syncing or have synced very recently
                filtered_orgs = []
                for row in rows:
                    org_id = row['organization_id']
                    
                    # Skip if currently syncing
                    if self.running_syncs.get(org_id, False):
                        continue
                    
                    # Skip if synced very recently (within 30 minutes)
                    last_sync = self.last_sync_times.get(org_id)
                    if last_sync and (datetime.now() - last_sync).total_seconds() < 1800:
                        continue
                    
                    filtered_orgs.append(org_id)
                
                return filtered_orgs
                
        except Exception as e:
            logger.error(f"Failed to get organizations needing sync: {e}")
            return []
    
    async def sync_organization_safe(self, organization_id: str, force_full: bool = False) -> bool:
        """
        Safely sync an organization with error handling and duplicate prevention
        Uses incremental sync by default for efficiency
        """
        if self.running_syncs.get(organization_id, False):
            logger.info(f"Sync already running for organization {organization_id}, skipping")
            return False
            
        try:
            self.running_syncs[organization_id] = True
            logger.info(f"Starting automated sync for organization {organization_id} (incremental={not force_full})")
            
            # Use incremental sync by default for efficiency
            if force_full:
                result = self.sync_service.sync_all_data(organization_id)
            else:
                result = self.sync_service.sync_incremental(organization_id)
            
            # Check if sync was successful
            if not result.get("success", False):
                raise Exception(f"Sync failed: {result.get('errors', ['Unknown error'])}")
            
            self.last_sync_times[organization_id] = datetime.now()
            
            # Log efficiency info
            sync_type = result.get("sync_type", "unknown")
            if sync_type == "skipped_recent":
                logger.info(f"Automated sync skipped for organization {organization_id} (recent sync)")
            else:
                efficiency_info = result.get("efficiency_gain", "")
                logger.info(f"Automated sync completed successfully for organization {organization_id} ({sync_type}) {efficiency_info}")
            
            return True
            
        except Exception as e:
            logger.error(f"Automated sync failed for organization {organization_id}: {e}")
            return False
            
        finally:
            self.running_syncs[organization_id] = False
    
    async def run_scheduled_syncs(self, sync_interval_minutes: int = 240, force_full: bool = False):
        """
        Run scheduled syncs for all organizations that need it
        Default 4-hour interval for incremental syncs
        """
        try:
            organizations = await self.get_organizations_needing_sync(sync_interval_minutes)
            
            if not organizations:
                logger.debug("No organizations need syncing at this time")
                return
                
            sync_type = "full" if force_full else "incremental"
            logger.info(f"Found {len(organizations)} organizations needing {sync_type} sync")
            
            # Run syncs sequentially to avoid overwhelming Cliniko API
            successful_syncs = 0
            for org_id in organizations:
                success = await self.sync_organization_safe(org_id, force_full)
                if success:
                    successful_syncs += 1
                
                # Small delay between syncs to be respectful to API
                if len(organizations) > 1:
                    await asyncio.sleep(30)  # 30 second delay between org syncs
            
            logger.info(f"Scheduled sync completed: {successful_syncs}/{len(organizations)} organizations synced successfully")
                
        except Exception as e:
            logger.error(f"Error in scheduled sync runner: {e}")
    
    async def run_full_sync_all(self):
        """
        Force a full sync for all organizations (useful for maintenance)
        """
        logger.info("Starting full sync for all organizations...")
        await self.run_scheduled_syncs(sync_interval_minutes=0, force_full=True)
    
    async def start_scheduler(self, sync_interval_minutes: int = 240):
        """
        Start the continuous sync scheduler
        Default 4-hour interval for better efficiency
        """
        logger.info(f"Starting sync scheduler with {sync_interval_minutes} minute intervals")
        
        while True:
            try:
                # Check if it's time for a daily full sync (run at 2 AM local time)
                current_hour = datetime.now().hour
                force_full = (current_hour == 2)  # 2 AM full sync
                
                if force_full:
                    logger.info("Running daily full sync (2 AM)")
                
                await self.run_scheduled_syncs(sync_interval_minutes, force_full)
                
                # Wait for the sync interval before next run
                await asyncio.sleep(sync_interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                # Wait 10 minutes before retrying on error
                await asyncio.sleep(600)
    
    def get_sync_status(self, organization_id: str) -> Dict[str, any]:
        """
        Get sync status for an organization
        """
        return {
            "organization_id": organization_id,
            "sync_running": self.running_syncs.get(organization_id, False),
            "last_sync_time": self.last_sync_times.get(organization_id),
            "scheduler_active": True
        }

# Global scheduler instance
scheduler = SyncScheduler() 