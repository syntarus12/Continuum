"""Typed API errors. Exception messages intentionally omit request secrets."""


class SyntarusError(Exception):
    """Base exception raised for an unsuccessful Syntarus API response."""


class AuthenticationError(SyntarusError):
    """The project API key is invalid, expired, or revoked."""


class PermissionDenied(SyntarusError):
    """The project API key does not have the required scope."""


class RateLimitError(SyntarusError):
    """The project API key has exceeded its request budget."""

    def __init__(self, message: str, *, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class APIConnectionError(SyntarusError):
    """The Syntarus API could not be reached."""


class APITimeoutError(APIConnectionError):
    """The Syntarus API did not respond before the configured timeout."""


class EventFailedError(SyntarusError):
    """An accepted asynchronous memory event reached a terminal failure."""

    def __init__(self, event: dict):
        self.event = event
        detail = event.get("last_error") or f"event ended with status {event.get('status')}"
        super().__init__(str(detail))
