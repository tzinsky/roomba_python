from __future__ import annotations

import pytest

from roomba_python.client import RobotClient
from roomba_python.errors import ValidationError
from roomba_python.models import CommandResult, PreferencesPatch
from roomba_python.types import CleaningPasses


class _FakeTransport:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        blid: str,
        password: str,
        tls_legacy=None,
        ciphers=None,
    ) -> None:
        del host, port, blid, password, tls_legacy, ciphers
        self.connected = False
        self.payload_handler = None
        self.command_calls: list[tuple[str, float | None]] = []
        self.delta_calls: list[tuple[dict, float | None]] = []

    def set_payload_handler(self, handler) -> None:
        self.payload_handler = handler

    def connect(self, timeout: float) -> None:
        del timeout
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def publish_command(self, command: str, *, timeout: float | None = None) -> dict:
        self.command_calls.append((command, timeout))
        return {"command": command, "time": 1760000000, "initiator": "localApp"}

    def publish_delta(self, patch: dict, *, timeout: float | None = None) -> dict:
        self.delta_calls.append((patch, timeout))
        return {"state": patch}


def _client_with_fake_transport(monkeypatch: pytest.MonkeyPatch) -> RobotClient:
    monkeypatch.setattr("roomba_python.client.MqttTransport", _FakeTransport)
    return RobotClient("blid", "password", "192.168.1.2", command_timeout=3.5)


@pytest.mark.parametrize("method_name", ["clean", "pause", "resume", "dock", "stop"])
def test_command_methods_return_strict_command_result(
    monkeypatch: pytest.MonkeyPatch,
    method_name: str,
) -> None:
    client = _client_with_fake_transport(monkeypatch)

    result = getattr(client, method_name)()
    assert isinstance(result, CommandResult)
    assert result.topic == "cmd"
    assert result.command == method_name
    assert result.sent_at_unix == 1760000000
    assert result.request_payload["initiator"] == "localApp"

    assert client._transport.command_calls == [(method_name, 3.5)]


def test_set_preferences_maps_and_returns_result(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client_with_fake_transport(monkeypatch)

    patch = PreferencesPatch(cleaning_passes=CleaningPasses.ONE)
    result = client.set_preferences(patch)

    assert isinstance(result, CommandResult)
    assert result.topic == "delta"
    assert result.command == "set_preferences"
    assert result.request_payload == {"state": {"noAutoPasses": True, "twoPass": False}}
    assert client._transport.delta_calls == [({"noAutoPasses": True, "twoPass": False}, 3.5)]


def test_set_preferences_empty_patch_raises_validation_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client_with_fake_transport(monkeypatch)

    with pytest.raises(ValidationError):
        client.set_preferences(PreferencesPatch())


def test_connect_disconnect_lifecycle(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client_with_fake_transport(monkeypatch)
    assert client.is_connected() is False

    client.connect()
    assert client.is_connected() is True

    client.disconnect()
    assert client.is_connected() is False
