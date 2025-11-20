"""Base API client with retry logic."""

import logging
from typing import Dict, Any, Optional
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)


class APIException(Exception):
    """Base API exception."""
    
    def __init__(self, status_code: int = 0, message: str = "API request failed"):
        self.status_code = status_code
        self.message = f"{message} (status: {status_code})" if status_code else message
        super().__init__(self.message)


class BaseAPIClient:
    """Base client for making HTTP requests with retry logic."""

    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        print(f"------- {base_url}")
        """
        Initialize base API client.

        Args:
            base_url: Base URL for API requests
            auth_token: Optional authentication token for API requests
        """
        self.base_url = base_url
        self.auth_token = auth_token
        self._client: Optional[httpx.AsyncClient] = None
        self._headers = {
            "Content-Type": "application/json",
        }
        if auth_token:
            self._headers["Authorization"] = f"Bearer {auth_token}"

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self):
        """Ensure the async client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers=self._headers,
                timeout=30.0,
                follow_redirects=True,
            )

    async def close(self):
        """Close the async client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def set_auth_token(self, token: str):
        """Set authentication token."""
        self.auth_token = token
        self._headers["Authorization"] = f"Bearer {token}"
        if self._client is not None:
            self._client.headers.update({"Authorization": f"Bearer {token}"})

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, APIException)),
        reraise=True,
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters

        Returns:
            Response JSON data

        Raises:
            APIException: When request fails
        """
        await self._ensure_client()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            logger.debug(f"{method} {url}")
            response = await self._client.request(
                method=method,
                url=url,
                json=data,
                params=params,
            )
            
            # Raise for HTTP errors
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            status_code = e.response.status_code
            try:
                error_data = e.response.json()
                error_message = error_data.get("message", str(e))
            except:
                error_message = str(e)
            raise APIException(status_code=status_code, message=error_message)
            
        except httpx.HTTPError as e:
            logger.error(f"Request error: {e}")
            raise APIException(message=f"Request failed: {str(e)}")
