"""
Custom exceptions for the mios ml_service.
"""

class MiosError(Exception):
    """Base exception for all Mios-related errors."""
    pass

class MiosConnectionError(MiosError):
    """Raised when a connection to a Mios agent fails (refused, timeout, reset)."""
    pass

class MiosProtocolError(MiosError):
    """Raised when the Mios agent returns an unexpected or malformed response."""
    pass

class MiosTimeoutError(MiosConnectionError):
    """Raised when a Mios operation times out."""
    pass
