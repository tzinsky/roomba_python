from __future__ import annotations

import builtins
import json

import pytest

from roomba_python.discovery import discover_robots, get_robot_public_info
from roomba_python.errors import TimeoutError as DoritaTimeoutError


class _FakeSocket:
    def __init__(self, responses: list[bytes]) -> None:
        self._responses = list(responses)
        self.sent: list[tuple[bytes, tuple[str, int]]] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        del exc_type, exc, tb
        return False

    def setsockopt(self, level: int, optname: int, value: int) -> None:
        del level, optname, value

    def settimeout(self, timeout: float) -> None:
        del timeout

    def bind(self, addr: tuple[str, int]) -> None:
        del addr

    def sendto(self, message: bytes, addr: tuple[str, int]) -> None:
        self.sent.append((message, addr))

    def recvfrom(self, size: int):
        del size
        if not self._responses:
            raise builtins.TimeoutError("socket timed out")
        return self._responses.pop(0), ("192.168.1.10", 5678)


def _payload(hostname: str, ip: str) -> bytes:
    return json.dumps({"hostname": hostname, "ip": ip, "robotname": "Dorita"}).encode("utf-8")


def _patch_socket(monkeypatch: pytest.MonkeyPatch, fake_socket: _FakeSocket) -> None:
    monkeypatch.setattr(
        "roomba_python.discovery.socket.socket",
        lambda *_args, **_kwargs: fake_socket,
    )


def test_discover_robots_returns_unique_typed_results(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        _payload("Roomba-AAA", "192.168.1.10"),
        _payload("Roomba-AAA", "192.168.1.10"),
        _payload("iRobot-BBB", "192.168.1.11"),
    ]

    fake_socket = _FakeSocket(responses)

    _patch_socket(monkeypatch, fake_socket)
    time_values = iter([0.0, 0.01, 0.02, 0.03, 1.0])
    monkeypatch.setattr("roomba_python.discovery.time.time", lambda: next(time_values))

    robots = discover_robots(timeout=0.5)

    assert len(robots) == 2
    assert {r.hostname for r in robots} == {"Roomba-AAA", "iRobot-BBB"}
    assert fake_socket.sent[0][0] == b"irobotmcs"


def test_get_robot_public_info_sets_blid_from_hostname(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_socket = _FakeSocket([_payload("Roomba-ABCDEF", "192.168.1.12")])

    _patch_socket(monkeypatch, fake_socket)
    time_values = iter([0.0, 0.01, 0.02])
    monkeypatch.setattr("roomba_python.discovery.time.time", lambda: next(time_values))

    robot = get_robot_public_info("192.168.1.12", timeout=0.5)

    assert robot.hostname == "Roomba-ABCDEF"
    assert robot.ip == "192.168.1.12"
    assert robot.blid == "ABCDEF"


def test_get_robot_public_info_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_socket = _FakeSocket([])

    _patch_socket(monkeypatch, fake_socket)
    time_values = iter([0.0, 0.4, 0.8])
    monkeypatch.setattr("roomba_python.discovery.time.time", lambda: next(time_values))

    with pytest.raises(DoritaTimeoutError):
        get_robot_public_info("192.168.1.20", timeout=0.5)
