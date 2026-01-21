"""
Avionté API Authentication and Token Management
"""
import os
import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
from .exceptions import AvionteAuthError, AvionteNetworkError

logger = logging.getLogger(__name__)


class AvionteAuth:
    """Handles Avionté API authentication and token management"""
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize Avionté authentication
        
        Args:
            client_id: OAuth client ID (or from env AVIONTE_CLIENT_ID)
            client_secret: OAuth client secret (or from env AVIONTE_CLIENT_SECRET)
            base_url: API base URL (or from env AVIONTE_API_BASE_URL, default: https://api.avionte.com)
        """
        self.client_id = client_id or os.getenv("AVIONTE_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("AVIONTE_CLIENT_SECRET", "")
        self.base_url = base_url or os.getenv("AVIONTE_API_BASE_URL", "https://api.avionte.com")
        
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.token_type: str = "Bearer"
        
        if not self.client_id or not self.client_secret:
            logger.warning("Avionté credentials not configured. Set AVIONTE_CLIENT_ID and AVIONTE_CLIENT_SECRET environment variables.")
    
    def is_configured(self) -> bool:
        """Check if authentication is properly configured"""
        return bool(self.client_id and self.client_secret)
    
    async def get_access_token(self, force_refresh: bool = False) -> str:
        """
        Get a valid access token, refreshing if necessary
        
        Args:
            force_refresh: Force token refresh even if current token is valid
            
        Returns:
            Access token string
            
        Raises:
            AvionteAuthError: If authentication fails
            AvionteNetworkError: If network request fails
        """
        # Check if we have a valid token
        if not force_refresh and self.access_token and self.token_expires_at:
            # Refresh if token expires within 5 minutes
            if datetime.now() < (self.token_expires_at - timedelta(minutes=5)):
                return self.access_token
        
        # Request new token
        await self._request_token()
        return self.access_token
    
    async def _request_token(self) -> None:
        """
        Request a new access token from Avionté API
        
        Raises:
            AvionteAuthError: If authentication fails
            AvionteNetworkError: If network request fails
        """
        if not self.is_configured():
            raise AvionteAuthError("Avionté credentials not configured")
        
        token_url = f"{self.base_url}/authorize/token"
        
        # Avionté typically uses OAuth2 client credentials flow
        # Adjust payload based on actual API requirements
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(token_url, data=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get("access_token")
                    expires_in = data.get("expires_in", 3600)  # Default to 1 hour
                    
                    if not self.access_token:
                        raise AvionteAuthError("Access token not found in response", response_data=data)
                    
                    # Calculate expiration time
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                    self.token_type = data.get("token_type", "Bearer")
                    
                    logger.info("Successfully obtained Avionté access token")
                elif response.status_code == 401:
                    raise AvionteAuthError(
                        "Authentication failed: Invalid client credentials",
                        status_code=401,
                        response_data=response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    )
                else:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    raise AvionteAuthError(
                        f"Failed to obtain access token: {response.status_code}",
                        status_code=response.status_code,
                        response_data=error_data
                    )
        except httpx.TimeoutException as e:
            raise AvionteNetworkError(f"Request timeout while obtaining token: {str(e)}")
        except httpx.RequestError as e:
            raise AvionteNetworkError(f"Network error while obtaining token: {str(e)}")
        except AvionteAuthError:
            raise
        except Exception as e:
            raise AvionteAuthError(f"Unexpected error during authentication: {str(e)}")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authorization headers for API requests
        
        Returns:
            Dictionary with Authorization header
        """
        if not self.access_token:
            raise AvionteAuthError("No access token available. Call get_access_token() first.")
        
        return {
            "Authorization": f"{self.token_type} {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
    
    def clear_token(self) -> None:
        """Clear the current access token (force refresh on next request)"""
        self.access_token = None
        self.token_expires_at = None
