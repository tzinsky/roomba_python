"""dorita980-py public package exports."""

from .client import RobotClient
from .discovery import discover_robots, get_robot_public_info
from .errors import (
    AuthenticationError,
    ConnectionError,
    DoritaError,
    ProtocolError,
    PublishError,
    TimeoutError,
    ValidationError,
)

__all__ = [
    "AuthenticationError",
    "ConnectionError",
    "DoritaError",
    "ProtocolError",
    "PublishError",
    "RobotClient",
    "TimeoutError",
    "ValidationError",
    "discover_robots",
    "get_robot_public_info",
]
