from __future__ import annotations

import json

import pytest

from roomba_python.errors import AuthenticationError, ConnectionError, ProtocolError, PublishError
from roomba_python.transport import MqttTransport


class _FakePublishResult:
    def __init__(self, rc: int = 0, publish_ok: bool = True) -> None:
        self.rc = rc
        self._publish_ok = publish_ok

    def wait_for_publish(self, timeout: float | None = None) -> bool:
        del timeout
        return self._publish_ok


class _FakeMessage:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload


class _FakeMqttClient:
    def __init__(self) -> None:
        self.on_connect = None
        self.on_disconnect = None
        self.on_message = None
        self._publish_calls: list[tuple[str, str]] = []
        self._subscribe_calls: list[str] = []
        self._publish_result = _FakePublishResult(0)

    def username_pw_set(self, username: str, password: str) -> None:
        del username, password

    def tls_set_context(self, context) -> None:
        del context

    def tls_insecure_set(self, value: bool) -> None:
        del value

    def reconnect_delay_set(self, min_delay: int, max_delay: int) -> None:
        del min_delay, max_delay

    def connect(self, host: str, port: int, keepalive: int) -> None:
        del host, port, keepalive
        if self.on_connect:
            self.on_connect(self, None, None, 0, None)

    def loop_start(self) -> None:
        return

    def loop_stop(self) -> None:
        return

    def subscribe(self, topic: str) -> None:
        self._subscribe_calls.append(topic)

    def disconnect(self) -> None:
        if self.on_disconnect:
            self.on_disconnect(self, None, None, 0, None)

    def publish(self, topic: str, payload: str) -> _FakePublishResult:
        self._publish_calls.append((topic, payload))
        return self._publish_result


def test_transport_connect_and_subscribe() -> None:
    fake_client = _FakeMqttClient()
    transport = MqttTransport(
        host="192.168.1.10",
        port=8883,
        blid="blid",
        password="password",
        mqtt_client=fake_client,
    )

    transport.connect(timeout=1)

    assert transport.connected is True
    assert fake_client._subscribe_calls == ["#"]


def test_transport_connect_auth_failure() -> None:
    fake_client = _FakeMqttClient()

    def _reject_connect(host: str, port: int, keepalive: int) -> None:
        del host, port, keepalive
        if fake_client.on_connect:
            fake_client.on_connect(fake_client, None, None, 5, None)

    fake_client.connect = _reject_connect  # type: ignore[method-assign]

    transport = MqttTransport(
        host="192.168.1.10",
        port=8883,
        blid="blid",
        password="password",
        mqtt_client=fake_client,
    )

    with pytest.raises(AuthenticationError):
        transport.connect(timeout=1)

    assert "code 5" in str(transport.last_error)


def test_publish_fails_when_disconnected() -> None:
    transport = MqttTransport(
        host="192.168.1.10",
        port=8883,
        blid="blid",
        password="password",
        mqtt_client=_FakeMqttClient(),
    )

    with pytest.raises(PublishError):
        transport.publish("cmd", {"command": "clean"})


def test_publish_error_includes_rc_code() -> None:
    fake_client = _FakeMqttClient()
    fake_client._publish_result = _FakePublishResult(rc=1)
    transport = MqttTransport(
        host="192.168.1.10",
        port=8883,
        blid="blid",
        password="password",
        mqtt_client=fake_client,
    )
    transport.connect(timeout=1)

    with pytest.raises(PublishError) as exc_info:
        transport.publish("cmd", {"command": "clean"})
    assert "rc=1" in str(exc_info.value)


def test_publish_timeout_raises_error() -> None:
    fake_client = _FakeMqttClient()
    fake_client._publish_result = _FakePublishResult(rc=0, publish_ok=False)
    transport = MqttTransport(
        host="192.168.1.10",
        port=8883,
        blid="blid",
        password="password",
        mqtt_client=fake_client,
    )
    transport.connect(timeout=1)

    with pytest.raises(PublishError):
        transport.publish("cmd", {"command": "clean"}, timeout=0.01)


def test_publish_command_and_delta_payloads() -> None:
    fake_client = _FakeMqttClient()
    transport = MqttTransport(
        host="192.168.1.10",
        port=8883,
        blid="blid",
        password="password",
        mqtt_client=fake_client,
    )
    transport.connect(timeout=1)

    command_payload = transport.publish_command("clean", timeout=1)
    delta_payload = transport.publish_delta({"binPause": True}, timeout=1)

    assert command_payload["command"] == "clean"
    assert delta_payload == {"state": {"binPause": True}}

    topics = [call[0] for call in fake_client._publish_calls]
    assert topics == ["cmd", "delta"]

    command_raw = json.loads(fake_client._publish_calls[0][1])
    delta_raw = json.loads(fake_client._publish_calls[1][1])
    assert command_raw["initiator"] == "localApp"
    assert delta_raw == {"state": {"binPause": True}}


def test_subscription_continuity_after_reconnect() -> None:
    fake_client = _FakeMqttClient()
    transport = MqttTransport(
        host="192.168.1.10",
        port=8883,
        blid="blid",
        password="password",
        mqtt_client=fake_client,
    )
    transport.connect(timeout=1)
    assert fake_client._subscribe_calls == ["#"]

    fake_client.on_disconnect(fake_client, None, None, 7, None)
    assert transport.reconnect_failures == 1

    fake_client.on_connect(fake_client, None, None, 0, None)
    assert fake_client._subscribe_calls == ["#", "#"]


def test_transport_records_protocol_error_on_bad_json() -> None:
    fake_client = _FakeMqttClient()
    transport = MqttTransport(
        host="192.168.1.10",
        port=8883,
        blid="blid",
        password="password",
        mqtt_client=fake_client,
    )
    transport.set_payload_handler(lambda _payload: None)
    transport.connect(timeout=1)

    fake_client.on_message(fake_client, None, _FakeMessage(b"{not-json"))

    assert isinstance(transport.last_error, ProtocolError)


def test_connect_error_mapping_from_oserror() -> None:
    fake_client = _FakeMqttClient()

    def _broken_connect(host: str, port: int, keepalive: int) -> None:
        del host, port, keepalive
        raise OSError("network down")

    fake_client.connect = _broken_connect  # type: ignore[method-assign]

    transport = MqttTransport(
        host="192.168.1.10",
        port=8883,
        blid="blid",
        password="password",
        mqtt_client=fake_client,
    )

    with pytest.raises(ConnectionError):
        transport.connect(timeout=1)
