"""
Cliniko API Client for SurfRehab v2
Copy your existing ClinikoActivePatientsFinder implementation here
"""

import os
import logging
import httpx
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ClinikoClient:
    """Cliniko API client for patient data"""
    
    def __init__(self):
        self.api_key = os.getenv('CLINIKO_API_KEY')
        self.region = os.getenv('CLINIKO_REGION', 'au4')
        self.base_url = f"https://api.{self.region}.cliniko.com/v1"
        
        if not self.api_key:
            raise ValueError("CLINIKO_API_KEY environment variable required")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Cliniko API connection and credentials"""
        try:
            headers = {
                "Authorization": f"Basic {self.api_key}",
                "User-Agent": "RoutIQ Backend API/2.0",
                "Accept": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test with account info endpoint (lightweight)
                response = await client.get(
                    f"{self.base_url}/account",
                    headers=headers
                )
                
                if response.status_code == 200:
                    account_data = response.json()
                    return {
                        "success": True,
                        "message": "Cliniko connection successful",
                        "account_info": {
                            "id": account_data.get("id"),
                            "name": account_data.get("name"),
                            "region": self.region,
                            "timezone": account_data.get("time_zone")
                        }
                    }
                elif response.status_code == 401:
                    return {
                        "success": False,
                        "error": "Invalid Cliniko API key"
                    }
                elif response.status_code == 403:
                    return {
                        "success": False,
                        "error": "Cliniko API key does not have required permissions"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Cliniko API error: {response.status_code} - {response.text}"
                    }
                    
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Connection timeout to Cliniko API"
            }
        except Exception as e:
            logger.error(f"Cliniko connection test failed: {e}")
            return {
                "success": False,
                "error": f"Connection test failed: {str(e)}"
            }
    
    async def get_active_patients(self) -> List[Dict[str, Any]]:
        """
        Get active patients from Cliniko API
        
        TODO: Copy your existing implementation from ClinikoActivePatientsFinder
        This should return a list of patient dictionaries with:
        - id, name, phone, email
        - recent_appointment_count, upcoming_appointment_count, total_appointment_count
        - last_appointment_date, recent_appointments, upcoming_appointments
        - search_date_from, search_date_to
        """
        
        # Placeholder - replace with your actual implementation
        logger.warning("ClinikoClient.get_active_patients() is a placeholder - implement from existing code")
        return []
    
    async def get_patients(self, limit: int = 100, page: int = 1) -> Dict[str, Any]:
        """Get patients from Cliniko API with pagination"""
        try:
            headers = {
                "Authorization": f"Basic {self.api_key}",
                "User-Agent": "RoutIQ Backend API/2.0",
                "Accept": "application/json"
            }
            
            params = {
                "per_page": min(limit, 100),  # Cliniko max is 100
                "page": page
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/patients",
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "data": response.json()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to fetch patients: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get patients: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_appointments(self, limit: int = 100, page: int = 1) -> Dict[str, Any]:
        """Get appointments from Cliniko API with pagination"""
        try:
            headers = {
                "Authorization": f"Basic {self.api_key}",
                "User-Agent": "RoutIQ Backend API/2.0", 
                "Accept": "application/json"
            }
            
            params = {
                "per_page": min(limit, 100),
                "page": page
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/appointments",
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "data": response.json()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to fetch appointments: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get appointments: {e}")
            return {
                "success": False,
                "error": str(e)
            } 