"""
Avionté API Client
Main client for making API requests to Avionté
"""
import asyncio
import logging
import time
from typing import Optional, Dict, Any, List
import httpx
from .auth import AvionteAuth
from .exceptions import (
    AvionteException,
    AvionteAuthError,
    AvionteAPIError,
    AvionteRateLimitError,
    AvionteNotFoundError,
    AvionteNetworkError,
)

logger = logging.getLogger(__name__)


class AvionteClient:
    """Main client for interacting with Avionté API"""
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize Avionté API client
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (exponential backoff)
        """
        self.auth = AvionteAuth(client_id, client_secret, base_url)
        self.base_url = base_url or self.auth.base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # HTTP client will be created per request to handle async properly
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client
    
    async def close(self) -> None:
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def _handle_error_response(self, response: httpx.Response) -> None:
        """
        Handle error responses from API
        
        Args:
            response: HTTP response object
            
        Raises:
            Appropriate Avionté exception based on status code
        """
        status_code = response.status_code
        try:
            error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        except Exception:
            error_data = {"message": response.text[:500] if response.text else "Unknown error"}
        
        if status_code == 401:
            self.auth.clear_token()  # Clear invalid token
            raise AvionteAuthError(
                "Authentication failed",
                status_code=status_code,
                response_data=error_data
            )
        elif status_code == 404:
            raise AvionteNotFoundError(
                error_data.get("message", "Resource not found"),
                status_code=status_code,
                response_data=error_data
            )
        elif status_code == 429:
            retry_after = response.headers.get("Retry-After", "60")
            raise AvionteRateLimitError(
                f"Rate limit exceeded. Retry after {retry_after} seconds",
                status_code=status_code,
                response_data=error_data
            )
        elif 400 <= status_code < 500:
            raise AvionteAPIError(
                error_data.get("message", f"Client error: {status_code}"),
                status_code=status_code,
                response_data=error_data
            )
        elif status_code >= 500:
            raise AvionteAPIError(
                error_data.get("message", f"Server error: {status_code}"),
                status_code=status_code,
                response_data=error_data
            )
        else:
            raise AvionteAPIError(
                error_data.get("message", f"Unexpected error: {status_code}"),
                status_code=status_code,
                response_data=error_data
            )
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Make an API request with retry logic
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (relative to base_url)
            params: Query parameters
            json_data: JSON request body
            headers: Additional headers
            retry_count: Current retry attempt number
            
        Returns:
            Response JSON data
            
        Raises:
            Avionté exceptions for various error conditions
        """
        # Ensure we have a valid token
        try:
            await self.auth.get_access_token()
        except AvionteAuthError:
            # If auth fails, don't retry
            raise
        
        # Build URL
        url = f"{self.base_url}{endpoint}"
        
        # Get auth headers
        auth_headers = self.auth.get_auth_headers()
        if headers:
            auth_headers.update(headers)
        
        client = await self._get_client()
        
        try:
            # Make request
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=auth_headers
            )
            
            # Handle successful response
            if 200 <= response.status_code < 300:
                if response.headers.get("content-type", "").startswith("application/json"):
                    return response.json()
                elif response.status_code == 204:  # No content
                    return {}
                else:
                    return {"data": response.text}
            
            # Handle error response
            self._handle_error_response(response)
            
        except (AvionteAuthError, AvionteRateLimitError, AvionteNotFoundError):
            # Don't retry these errors
            raise
        except (AvionteAPIError, AvionteNetworkError) as e:
            # Retry on network errors and some API errors
            if retry_count < self.max_retries:
                delay = self.retry_delay * (2 ** retry_count)  # Exponential backoff
                logger.warning(f"Request failed, retrying in {delay}s (attempt {retry_count + 1}/{self.max_retries}): {str(e)}")
                await asyncio.sleep(delay)
                return await self._request(method, endpoint, params, json_data, headers, retry_count + 1)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in API request: {str(e)}")
            raise AvionteAPIError(f"Unexpected error: {str(e)}")
    
    # Convenience methods
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request"""
        return await self._request("GET", endpoint, params=params)
    
    async def post(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a POST request"""
        return await self._request("POST", endpoint, json_data=json_data, params=params)
    
    async def put(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a PUT request"""
        return await self._request("PUT", endpoint, json_data=json_data, params=params)
    
    async def patch(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a PATCH request"""
        return await self._request("PATCH", endpoint, json_data=json_data, params=params)
    
    async def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a DELETE request"""
        return await self._request("DELETE", endpoint, params=params)
    
    async def health_check(self) -> bool:
        """
        Check API health
        
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            response = await self.get("/health")
            return response.get("status", "").lower() == "ok" or response.get("healthy", False)
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
