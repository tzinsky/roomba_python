"""Public exception hierarchy for dorita980-py."""


class DoritaError(Exception):
    """Base class for all public package errors."""


class ValidationError(DoritaError):
    """Raised when user input fails validation."""


class ConnectionError(DoritaError):
    """Raised when MQTT/TLS session cannot be established or maintained."""


class AuthenticationError(ConnectionError):
    """Raised when robot credentials are rejected."""


class PublishError(DoritaError):
    """Raised when a command cannot be published."""


class TimeoutError(DoritaError):
    """Raised when required telemetry fields are not observed in time."""


class ProtocolError(DoritaError):
    """Raised when incoming data cannot be parsed or mapped safely."""
