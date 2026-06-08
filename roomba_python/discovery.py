"""UDP discovery helpers for locating robots on the LAN."""

from __future__ import annotations

import json
import socket
import time
from typing import Final

from .errors import TimeoutError as DoritaTimeoutError
from .models import RobotDiscoveryInfo

_DISCOVERY_MESSAGE: Final[bytes] = b"irobotmcs"


def discover_robots(
    *,
    timeout: float = 2.0,
    broadcast_ip: str = "255.255.255.255",
    port: int = 5678,
) -> list[RobotDiscoveryInfo]:
    deadline = time.time() + timeout
    found: dict[tuple[str, str], RobotDiscoveryInfo] = {}

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(0.2)
        sock.bind(("", port))
        sock.sendto(_DISCOVERY_MESSAGE, (broadcast_ip, port))

        while time.time() < deadline:
            try:
                msg, _addr = sock.recvfrom(4096)
            except TimeoutError:
                continue
            info = _parse_discovery_payload(msg)
            if info is not None:
                found[(info.hostname, info.ip)] = info

    return list(found.values())


def get_robot_public_info(
    ip: str,
    *,
    timeout: float = 2.0,
    port: int = 5678,
) -> RobotDiscoveryInfo:
    deadline = time.time() + timeout

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(0.2)
        sock.bind(("", port))
        sock.sendto(_DISCOVERY_MESSAGE, (ip, port))

        while time.time() < deadline:
            try:
                msg, _addr = sock.recvfrom(4096)
            except TimeoutError:
                continue
            info = _parse_discovery_payload(msg)
            if info is not None:
                if info.blid is None and "-" in info.hostname:
                    info.blid = info.hostname.split("-", 1)[1]
                return info

    raise DoritaTimeoutError(f"No robot response received from {ip} before timeout")


def _parse_discovery_payload(raw: bytes) -> RobotDiscoveryInfo | None:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        return None

    hostname = payload.get("hostname")
    ip = payload.get("ip")
    if not hostname or not ip:
        return None
    if not (hostname.startswith("Roomba-") or hostname.startswith("iRobot-")):
        return None

    return RobotDiscoveryInfo.model_validate(payload)
