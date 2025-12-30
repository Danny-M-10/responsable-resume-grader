"""
Avionté API Client
Handles authentication and API interactions with Avionté
"""

import os
import time
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from config import AvionteConfig

logger = logging.getLogger(__name__)


class AvionteClient:
    """Client for interacting with Avionté API"""
    
    def __init__(self):
        """Initialize Avionté API client"""
        self.base_url = AvionteConfig.get_base_url()
        self.api_key = AvionteConfig.get_api_key()
        self.client_id = AvionteConfig.get_client_id()
        self.client_secret = AvionteConfig.get_client_secret()
        self.scope = AvionteConfig.get_scope()
        self.tenant = AvionteConfig.get_tenant()
        self.front_office_tenant_id = AvionteConfig.get_front_office_tenant_id()
        
        # Token cache
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
        # Rate limiting
        self._last_request_time: Optional[float] = None
        self._min_request_interval = 0.1  # Minimum 100ms between requests
        
    def _get_access_token(self) -> str:
        """
        Get access token using OAuth 2.0 client credentials flow.
        Caches token and refreshes before expiry.
        
        Returns:
            Access token string
            
        Raises:
            ValueError: If credentials are not configured
            requests.RequestException: If API request fails
        """
        # Check if we have a valid cached token
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at - timedelta(minutes=5):  # Refresh 5 min before expiry
                return self._access_token
        
        # Validate configuration
        if not self.api_key or not self.client_id or not self.client_secret:
            raise ValueError("Avionté API credentials not configured. Please set AVIONTE_API_KEY, AVIONTE_CLIENT_ID, and AVIONTE_CLIENT_SECRET environment variables.")
        
        # Request new token
        token_url = f"{self.base_url}/authorize/token"
        
        headers = {
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'x-api-key': self.api_key
        }
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': self.scope
        }
        
        try:
            response = requests.post(token_url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            self._access_token = token_data.get('access_token')
            
            # Parse expiry (typically expires_in is in seconds)
            expires_in = token_data.get('expires_in', 3600)  # Default to 1 hour
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            logger.info("Successfully obtained Avionté access token")
            return self._access_token
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Failed to get Avionté access token: HTTP {e.response.status_code} - {e.response.text}")
            raise ValueError(f"Avionté authentication failed: {e.response.status_code}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Avionté access token: {e}")
            raise ValueError(f"Avionté API request failed: {str(e)}") from e
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None, json_data: Optional[Dict] = None,
                     max_retries: int = 3) -> Dict[str, Any]:
        """
        Make authenticated API request with rate limiting and retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (relative to base_url)
            params: Query parameters
            data: Form data
            json_data: JSON body
            max_retries: Maximum number of retry attempts
            
        Returns:
            Response JSON as dictionary
            
        Raises:
            ValueError: If request fails after retries
        """
        # Rate limiting
        if self._last_request_time:
            elapsed = time.time() - self._last_request_time
            if elapsed < self._min_request_interval:
                time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
        
        # Get access token
        token = self._get_access_token()
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            'accept': 'application/json',
            'x-api-key': self.api_key,
            'Authorization': f'Bearer {token}'
        }
        
        # Add tenant header (required for Front Office API)
        if self.front_office_tenant_id:
            headers['FrontOfficeTenantId'] = str(self.front_office_tenant_id)
        elif self.tenant:
            headers['Tenant'] = self.tenant
        
        # Add content-type for POST/PUT requests
        if method in ['POST', 'PUT', 'PATCH']:
            if json_data:
                headers['content-type'] = 'application/json'
            elif data:
                headers['content-type'] = 'application/x-www-form-urlencoded'
        
        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                if method == 'GET':
                    response = requests.get(url, headers=headers, params=params, timeout=30)
                elif method == 'POST':
                    if json_data:
                        response = requests.post(url, headers=headers, params=params, json=json_data, timeout=30)
                    else:
                        response = requests.post(url, headers=headers, params=params, data=data, timeout=30)
                elif method == 'PUT':
                    if json_data:
                        response = requests.put(url, headers=headers, params=params, json=json_data, timeout=30)
                    else:
                        response = requests.put(url, headers=headers, params=params, data=data, timeout=30)
                elif method == 'PATCH':
                    if json_data:
                        response = requests.patch(url, headers=headers, params=params, json=json_data, timeout=30)
                    else:
                        response = requests.patch(url, headers=headers, params=params, data=data, timeout=30)
                elif method == 'DELETE':
                    response = requests.delete(url, headers=headers, params=params, timeout=30)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Handle rate limiting (429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    if attempt < max_retries - 1:
                        wait_time = retry_after * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Rate limited. Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}")
                        time.sleep(wait_time)
                        continue
                    else:
                        response.raise_for_status()
                
                # Handle other errors
                response.raise_for_status()
                
                # Return JSON response
                if response.content:
                    return response.json()
                return {}
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    # Token might be expired, clear cache and retry once
                    if attempt == 0:
                        logger.warning("Token expired, refreshing...")
                        self._access_token = None
                        self._token_expires_at = None
                        continue
                    logger.error(f"Avionté API authentication failed: {e.response.status_code} - {e.response.text}")
                    raise ValueError(f"Avionté authentication failed: {e.response.status_code}") from e
                elif e.response.status_code == 429 and attempt < max_retries - 1:
                    continue  # Already handled above
                else:
                    logger.error(f"Avionté API request failed: HTTP {e.response.status_code} - {e.response.text}")
                    if attempt == max_retries - 1:
                        raise ValueError(f"Avionté API request failed after {max_retries} attempts: {e.response.status_code}") from e
                    # Exponential backoff for other errors
                    wait_time = (2 ** attempt) * 1  # 1s, 2s, 4s
                    time.sleep(wait_time)
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Avionté API network error: {e}")
                if attempt == max_retries - 1:
                    raise ValueError(f"Avionté API network error after {max_retries} attempts: {str(e)}") from e
                wait_time = (2 ** attempt) * 1
                time.sleep(wait_time)
        
        raise ValueError(f"Avionté API request failed after {max_retries} attempts")
    
    def test_connection(self) -> bool:
        """
        Test connection to Avionté API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to get access token
            self._get_access_token()
            return True
        except Exception as e:
            logger.error(f"Avionté connection test failed: {e}")
            return False
    
    def get_talents(self, filters: Optional[Dict[str, Any]] = None, 
                   limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Fetch talents (candidates) from Avionté using query-multiple-talents endpoint.
        
        Note: The Avionté API doesn't have a simple GET endpoint for listing all talents.
        This method uses query-multiple-talents with empty criteria to get talents.
        
        Args:
            filters: Optional filters (query criteria)
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            List of talent dictionaries
        """
        endpoint = "/front-office/v1/talent/query-multiple-talents"
        
        # Build query criteria
        query_criteria = filters or {}
        if limit:
            query_criteria.setdefault('limit', limit)
        if offset:
            query_criteria.setdefault('offset', offset)
        
        try:
            response = self._make_request('POST', endpoint, json_data=query_criteria)
            # Response format may vary - handle both list and object with data property
            if isinstance(response, list):
                return response
            elif isinstance(response, dict) and 'data' in response:
                return response['data']
            elif isinstance(response, dict) and 'talents' in response:
                return response['talents']
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to fetch talents: {e}")
            raise
    
    def get_talent_by_id(self, talent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific talent by ID using query-multiple-talents.
        
        Args:
            talent_id: Talent ID
            
        Returns:
            Talent dictionary or None if not found
        """
        # Use query-multiple-talents with specific talent ID
        talents = self.query_multiple_talents([talent_id])
        if talents:
            return talents[0]
        return None
    
    def query_multiple_talents(self, talent_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Query multiple talents by their IDs.
        
        Args:
            talent_ids: List of talent IDs
            
        Returns:
            List of talent dictionaries
        """
        endpoint = "/front-office/v1/talent/query-multiple-talents"
        
        # Build query criteria with talent IDs
        query_criteria = {
            'talentIds': talent_ids
        }
        
        try:
            response = self._make_request('POST', endpoint, json_data=query_criteria)
            if isinstance(response, list):
                return response
            elif isinstance(response, dict) and 'data' in response:
                return response['data']
            elif isinstance(response, dict) and 'talents' in response:
                return response['talents']
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to query talents: {e}")
            return []
    
    def get_talent_documents(self, talent_id: str) -> List[Dict[str, Any]]:
        """
        Get documents (resumes) for a talent.
        
        Args:
            talent_id: Talent ID
            
        Returns:
            List of document dictionaries
        """
        endpoint = f"/front-office/v1/talent/{talent_id}/documents"
        
        try:
            response = self._make_request('GET', endpoint)
            if isinstance(response, list):
                return response
            elif isinstance(response, dict) and 'data' in response:
                return response['data']
            elif isinstance(response, dict) and 'documents' in response:
                return response['documents']
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to fetch documents for talent {talent_id}: {e}")
            return []
    
    def get_talent_document_content(self, talent_id: str, document_id: str) -> Optional[bytes]:
        """
        Download document content.
        
        Args:
            talent_id: Talent ID
            document_id: Document ID
            
        Returns:
            Document content as bytes, or None if not found
        """
        endpoint = f"/front-office/v1/talent/{talent_id}/documents/{document_id}/content"
        
        try:
            token = self._get_access_token()
            url = f"{self.base_url}{endpoint}"
            headers = {
                'x-api-key': self.api_key,
                'Authorization': f'Bearer {token}'
            }
            
            # Add tenant header
            if self.front_office_tenant_id:
                headers['FrontOfficeTenantId'] = str(self.front_office_tenant_id)
            elif self.tenant:
                headers['Tenant'] = self.tenant
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            return response.content
        except Exception as e:
            logger.error(f"Failed to download document {document_id} for talent {talent_id}: {e}")
            return None
    
    def get_jobs(self, filters: Optional[Dict[str, Any]] = None,
                limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Fetch jobs from Avionté using get-job-postings endpoint.
        
        Args:
            filters: Optional filters/query criteria
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            List of job dictionaries
        """
        endpoint = "/front-office/v1/job/get-job-postings"
        
        # Build query criteria
        query_criteria = filters or {}
        if limit:
            query_criteria.setdefault('limit', limit)
        if offset:
            query_criteria.setdefault('offset', offset)
        
        try:
            response = self._make_request('POST', endpoint, json_data=query_criteria)
            if isinstance(response, list):
                return response
            elif isinstance(response, dict) and 'data' in response:
                return response['data']
            elif isinstance(response, dict) and 'jobs' in response:
                return response['jobs']
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to fetch jobs: {e}")
            raise
    
    def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job dictionary or None if not found
        """
        endpoint = f"/front-office/v1/job/{job_id}"
        
        try:
            response = self._make_request('GET', endpoint)
            return response
        except Exception as e:
            logger.error(f"Failed to fetch job {job_id}: {e}")
            return None
    
    def query_multiple_jobs(self, job_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Query multiple jobs by their IDs.
        
        Args:
            job_ids: List of job IDs
            
        Returns:
            List of job dictionaries
        """
        endpoint = "/front-office/v1/job/query-multiple-jobs"
        
        # Build query criteria with job IDs
        query_criteria = {
            'jobIds': job_ids
        }
        
        try:
            response = self._make_request('POST', endpoint, json_data=query_criteria)
            if isinstance(response, list):
                return response
            elif isinstance(response, dict) and 'data' in response:
                return response['data']
            elif isinstance(response, dict) and 'jobs' in response:
                return response['jobs']
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to query jobs: {e}")
            return []

