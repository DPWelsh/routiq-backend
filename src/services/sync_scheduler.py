"""
Sync Scheduler Service
Automated sync scheduling and management for organizations
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import db
from src.services.cliniko_sync_service import ClinikoSyncService

logger = logging.getLogger(__name__)

class SyncScheduler:
    def __init__(self):
        self.sync_service = ClinikoSyncService()
        self.running_syncs: Dict[str, bool] = {}
        self.last_sync_times: Dict[str, datetime] = {}
        
    async def get_organizations_needing_sync(self, sync_interval_minutes: int = 30) -> List[str]:
        """
        Get list of organizations that need syncing based on their sync interval
        """
        try:
            cutoff_time = datetime.now() - timedelta(minutes=sync_interval_minutes)
            
            with db.get_cursor() as cursor:
                # Get organizations with Cliniko service enabled
                query = """
                SELECT DISTINCT os.organization_id
                FROM service_integrations os
                WHERE os.service_name = 'cliniko'
                AND os.enabled = true
                AND (
                    NOT EXISTS (
                        SELECT 1 FROM active_patients ap 
                        WHERE ap.organization_id = os.organization_id 
                        AND ap.updated_at > %s
                    )
                    OR os.organization_id NOT IN (
                        SELECT DISTINCT organization_id FROM active_patients
                    )
                )
                """
                
                cursor.execute(query, [cutoff_time])
                rows = cursor.fetchall()
                
                return [row['organization_id'] for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get organizations needing sync: {e}")
            return []
    
    async def sync_organization_safe(self, organization_id: str) -> bool:
        """
        Safely sync an organization with error handling and duplicate prevention
        """
        if self.running_syncs.get(organization_id, False):
            logger.info(f"Sync already running for organization {organization_id}, skipping")
            return False
            
        try:
            self.running_syncs[organization_id] = True
            logger.info(f"Starting automated sync for organization {organization_id}")
            
            await self.sync_service.sync_all_patients(organization_id)
            
            self.last_sync_times[organization_id] = datetime.now()
            logger.info(f"Automated sync completed successfully for organization {organization_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Automated sync failed for organization {organization_id}: {e}")
            return False
            
        finally:
            self.running_syncs[organization_id] = False
    
    async def run_scheduled_syncs(self, sync_interval_minutes: int = 30):
        """
        Run scheduled syncs for all organizations that need it
        """
        try:
            organizations = await self.get_organizations_needing_sync(sync_interval_minutes)
            
            if not organizations:
                logger.debug("No organizations need syncing at this time")
                return
                
            logger.info(f"Found {len(organizations)} organizations needing sync")
            
            # Run syncs concurrently but with reasonable limits
            sync_tasks = []
            for org_id in organizations:
                task = asyncio.create_task(self.sync_organization_safe(org_id))
                sync_tasks.append(task)
                
                # Limit concurrent syncs to avoid overwhelming the system
                if len(sync_tasks) >= 3:
                    await asyncio.gather(*sync_tasks, return_exceptions=True)
                    sync_tasks = []
            
            # Run remaining tasks
            if sync_tasks:
                await asyncio.gather(*sync_tasks, return_exceptions=True)
                
        except Exception as e:
            logger.error(f"Error in scheduled sync runner: {e}")
    
    async def start_scheduler(self, sync_interval_minutes: int = 30):
        """
        Start the continuous sync scheduler
        """
        logger.info(f"Starting sync scheduler with {sync_interval_minutes} minute intervals")
        
        while True:
            try:
                await self.run_scheduled_syncs(sync_interval_minutes)
                
                # Wait for the sync interval before next run
                await asyncio.sleep(sync_interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                # Wait 5 minutes before retrying on error
                await asyncio.sleep(300)
    
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