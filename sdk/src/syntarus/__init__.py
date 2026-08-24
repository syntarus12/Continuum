"""Official Syntarus project-scoped memory clients."""

from .client import AsyncMemoryClient, MemoryClient
from .exceptions import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    EventFailedError,
    PermissionDenied,
    RateLimitError,
    SyntarusError,
)

__all__ = [
    "AsyncMemoryClient", "MemoryClient", "SyntarusError", "AuthenticationError",
    "PermissionDenied", "RateLimitError", "APIConnectionError", "APITimeoutError",
    "EventFailedError",
]
