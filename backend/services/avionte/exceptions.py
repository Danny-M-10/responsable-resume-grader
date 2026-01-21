"""
Custom exceptions for Avionté API integration
"""
from typing import Optional, Dict, Any


class AvionteException(Exception):
    """Base exception for all Avionté API errors"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
        super().__init__(self.message)


class AvionteAuthError(AvionteException):
    """Authentication or authorization error"""
    pass


class AvionteAPIError(AvionteException):
    """General API error"""
    pass


class AvionteRateLimitError(AvionteException):
    """Rate limit exceeded error"""
    pass


class AvionteNotFoundError(AvionteException):
    """Resource not found error"""
    pass


class AvionteValidationError(AvionteException):
    """Request validation error"""
    pass


class AvionteNetworkError(AvionteException):
    """Network connectivity error"""
    pass
