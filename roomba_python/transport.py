"""MQTT transport wrapper used by RobotClient."""

from __future__ import annotations

import json
import os
import ssl
import threading
import time
from collections.abc import Callable
from typing import Any

import paho.mqtt.client as mqtt

from .errors import AuthenticationError, ConnectionError, ProtocolError, PublishError


class MqttTransport:
    """Small wrapper around paho-mqtt for predictable client behavior."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        blid: str,
        password: str,
        keepalive: int = 60,
        tls_legacy: bool | None = None,
        ciphers: str | None = None,
        reconnect_min_delay: int = 1,
        reconnect_max_delay: int = 30,
        subscribe_topics: tuple[str, ...] = ("#",),
        mqtt_client: mqtt.Client | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._keepalive = keepalive
        self._subscribe_topics = subscribe_topics
        self._connected = threading.Event()
        self._connect_done = threading.Event()
        self._disconnecting = False
        self._connect_error: Exception | None = None
        self._last_error: Exception | None = None
        self._reconnect_failures = 0
        self._on_payload: Callable[[dict[str, Any]], None] | None = None

        if mqtt_client is None:
            mqtt_client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION2,
                client_id=blid,
                clean_session=False,
                protocol=mqtt.MQTTv311,
            )
        self._client = mqtt_client
        self._client.username_pw_set(username=blid, password=password)

        tls_ciphers = ciphers if ciphers is not None else os.getenv("ROBOT_CIPHERS")
        tls_context = _build_tls_context(tls_legacy=tls_legacy, ciphers=tls_ciphers)
        self._client.tls_set_context(tls_context)
        self._client.tls_insecure_set(True)
        self._client.reconnect_delay_set(reconnect_min_delay, reconnect_max_delay)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

    @property
    def connected(self) -> bool:
        return self._connected.is_set()

    @property
    def reconnect_failures(self) -> int:
        return self._reconnect_failures

    @property
    def last_error(self) -> Exception | None:
        return self._last_error

    def set_payload_handler(self, handler: Callable[[dict[str, Any]], None]) -> None:
        self._on_payload = handler

    def connect(self, timeout: float) -> None:
        self._connect_error = None
        self._last_error = None
        self._disconnecting = False
        self._connect_done.clear()
        self._connected.clear()

        try:
            self._client.connect(self._host, self._port, self._keepalive)
            self._client.loop_start()
        except Exception as exc:  # pragma: no cover
            raise _map_connect_error(exc) from exc

        if not self._connect_done.wait(timeout=timeout):
            self._client.loop_stop()
            raise ConnectionError("Timeout waiting for MQTT connection")

        if self._connect_error is not None:
            self._client.loop_stop()
            raise self._connect_error

        if not self._connected.is_set():
            raise ConnectionError("Timeout waiting for MQTT connection")

    def disconnect(self) -> None:
        self._disconnecting = True
        if self.connected:
            self._client.disconnect()
        self._client.loop_stop()
        self._connected.clear()
        self._connect_done.clear()

    def publish_command(self, command: str, *, timeout: float | None = None) -> dict[str, Any]:
        payload = {
            "command": command,
            "time": int(time.time()),
            "initiator": "localApp",
        }
        self.publish("cmd", payload, timeout=timeout)
        return payload

    def publish_delta(
        self,
        state_patch: dict[str, Any],
        *,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        payload = {"state": state_patch}
        self.publish("delta", payload, timeout=timeout)
        return payload

    def publish(self, topic: str, payload: dict[str, Any], *, timeout: float | None = None) -> None:
        if not self.connected:
            raise PublishError("Unable to publish: transport is not connected")

        result = self._client.publish(topic, json.dumps(payload))
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise PublishError(
                f"Unable to publish to topic '{topic}': rc={result.rc}"
            )

        if timeout is not None:
            try:
                published = result.wait_for_publish(timeout=timeout)
            except TypeError:
                published = result.wait_for_publish()
            if published is False:
                raise PublishError(f"Timed out publishing to topic '{topic}'")

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: Any,
        reason_code: Any,
        properties: Any,
    ) -> None:
        del client, userdata, flags, properties
        reason = _reason_code_value(reason_code)
        if reason != 0:
            if reason in (4, 5):
                self._connect_error = AuthenticationError(
                    f"MQTT rejected credentials with code {reason}"
                )
            else:
                self._connect_error = ConnectionError(
                    f"MQTT rejected connection with code {reason}"
                )
            self._last_error = self._connect_error
            self._connect_done.set()
            return

        for topic in self._subscribe_topics:
            self._client.subscribe(topic)

        self._connected.set()
        self._connect_done.set()

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        disconnect_flags: Any,
        reason_code: Any,
        properties: Any,
    ) -> None:
        del client, userdata, disconnect_flags, properties
        reason = _reason_code_value(reason_code)
        self._connected.clear()
        if not self._disconnecting and self._connect_done.is_set():
            if reason != 0:
                self._reconnect_failures += 1
                self._last_error = ConnectionError(
                    f"Unexpected disconnect from broker: code {reason}"
                )
            # paho loop handles reconnect attempts according to reconnect_delay_set.
            return

    def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        del client, userdata
        if self._on_payload is None:
            return

        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except UnicodeDecodeError as exc:
            self._last_error = ProtocolError("Unable to decode MQTT payload as UTF-8")
            del exc
            return
        except json.JSONDecodeError as exc:
            self._last_error = ProtocolError("Unable to parse MQTT payload JSON")
            del exc
            return

        if isinstance(payload, dict):
            try:
                self._on_payload(payload)
            except Exception as exc:
                self._last_error = ProtocolError(
                    f"Payload handler failed: {type(exc).__name__}: {exc}"
                )
        else:
            self._last_error = ProtocolError("MQTT payload must decode to a JSON object")


def _build_tls_context(tls_legacy: bool | None, ciphers: str | None) -> ssl.SSLContext:
    # Robots use self-signed certificates, so cert chain verification must be
    # disabled. This mirrors Node.js dorita980 `strictSSL: false` /
    # `rejectUnauthorized: false` behaviour.
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    legacy_requested = tls_legacy
    if legacy_requested is None:
        legacy_requested = os.getenv("ROBOT_TLS_LEGACY", "1") != "0"

    legacy_flag = getattr(ssl, "OP_LEGACY_SERVER_CONNECT", None)
    if legacy_requested and legacy_flag is not None:
        context.options |= legacy_flag

    if ciphers:
        context.set_ciphers(ciphers)

    return context


def _reason_code_value(reason_code: Any) -> int:
    """Extract integer value from paho-mqtt ReasonCode or plain int."""
    # paho-mqtt v2 uses ReasonCode objects; v1 uses plain integers.
    if isinstance(reason_code, int):
        return reason_code
    val = getattr(reason_code, "value", None)
    if isinstance(val, int):
        return val
    try:
        return int(reason_code)
    except (TypeError, ValueError):
        return 0


def _map_connect_error(exc: Exception) -> ConnectionError:
    if isinstance(exc, ssl.SSLError):
        return ConnectionError(f"TLS failure while connecting to MQTT broker: {exc}")
    if isinstance(exc, OSError):
        return ConnectionError(f"Network failure while connecting to MQTT broker: {exc}")
    return ConnectionError(f"Failed to connect MQTT transport: {exc}")
