"""
Chatwoot API Client for SurfRehab v2
Copy your existing ChatwootClient implementation here
"""

import os
import logging
import httpx
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ChatwootClient:
    """Chatwoot API client for conversation data"""
    
    def __init__(self):
        self.api_token = os.getenv('CHATWOOT_API_TOKEN')
        self.account_id = os.getenv('CHATWOOT_ACCOUNT_ID')
        self.base_url = os.getenv('CHATWOOT_BASE_URL', 'https://app.chatwoot.com')
        
        if not self.api_token or not self.account_id:
            raise ValueError("CHATWOOT_API_TOKEN and CHATWOOT_ACCOUNT_ID environment variables required")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Chatwoot API connection and credentials"""
        try:
            headers = {
                "api_access_token": self.api_token,
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test with profile endpoint (lightweight)
                response = await client.get(
                    f"{self.base_url}/api/v1/accounts/{self.account_id}/profile",
                    headers=headers
                )
                
                if response.status_code == 200:
                    profile_data = response.json()
                    return {
                        "success": True,
                        "message": "Chatwoot connection successful",
                        "account_info": {
                            "id": profile_data.get("id"),
                            "name": profile_data.get("name"),
                            "email": profile_data.get("email"),
                            "account_id": self.account_id
                        }
                    }
                elif response.status_code == 401:
                    return {
                        "success": False,
                        "error": "Invalid Chatwoot API token"
                    }
                elif response.status_code == 403:
                    return {
                        "success": False,
                        "error": "Chatwoot API token does not have required permissions"
                    }
                elif response.status_code == 404:
                    return {
                        "success": False,
                        "error": "Chatwoot account not found - check account ID"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Chatwoot API error: {response.status_code} - {response.text}"
                    }
                    
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Connection timeout to Chatwoot API"
            }
        except Exception as e:
            logger.error(f"Chatwoot connection test failed: {e}")
            return {
                "success": False,
                "error": f"Connection test failed: {str(e)}"
            }
    
    async def get_conversations(self, status: str = "open", limit: int = 100, page: int = 1) -> Dict[str, Any]:
        """Get conversations from Chatwoot API with pagination"""
        try:
            headers = {
                "api_access_token": self.api_token,
                "Content-Type": "application/json"
            }
            
            params = {
                "status": status,
                "per_page": min(limit, 100),  # Reasonable limit
                "page": page
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations",
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
                        "error": f"Failed to fetch conversations: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get conversations: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_conversation_messages(self, conversation_id: int) -> Dict[str, Any]:
        """Get messages for a specific conversation"""
        try:
            headers = {
                "api_access_token": self.api_token,
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/messages",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "data": response.json()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to fetch messages: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get conversation messages: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_contacts(self, limit: int = 100, page: int = 1) -> Dict[str, Any]:
        """Get contacts from Chatwoot API with pagination"""
        try:
            headers = {
                "api_access_token": self.api_token,
                "Content-Type": "application/json"
            }
            
            params = {
                "per_page": min(limit, 100),
                "page": page
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/accounts/{self.account_id}/contacts",
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
                        "error": f"Failed to fetch contacts: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get contacts: {e}")
            return {
                "success": False,
                "error": str(e)
            } 