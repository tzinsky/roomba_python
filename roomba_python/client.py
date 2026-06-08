"""Reduced-scope RobotClient skeleton."""

from __future__ import annotations

import threading
import time
import uuid
from collections.abc import Callable
from typing import Any

from .errors import TimeoutError, ValidationError
from .models import (
    BinStatus,
    CleanMissionStatus,
    CommandResult,
    MissionSnapshot,
    Pose,
    PreferencesPatch,
    RobotState,
    SignalInfo,
)
from .transport import MqttTransport
from .types import CarpetBoostMode, CleaningPasses, StateField


class RobotClient:
    """High-level reduced API client for local robot control."""

    def __init__(
        self,
        blid: str,
        password: str,
        host: str,
        *,
        port: int = 8883,
        emit_interval: float = 0.8,
        connect_timeout: float = 10.0,
        command_timeout: float = 5.0,
        tls_legacy: bool | None = None,
        ciphers: str | None = None,
    ) -> None:
        self._emit_interval = emit_interval
        self._connect_timeout = connect_timeout
        self._command_timeout = command_timeout
        self._state = RobotState()
        self._state_lock = threading.Lock()
        self._state_listeners: dict[str, Callable[[RobotState], None]] = {}
        self._mission_listeners: dict[str, Callable[[MissionSnapshot], None]] = {}

        self._transport = MqttTransport(
            host=host,
            port=port,
            blid=blid,
            password=password,
            tls_legacy=tls_legacy,
            ciphers=ciphers,
        )
        self._transport.set_payload_handler(self._on_payload)

    def connect(self) -> None:
        self._transport.connect(timeout=self._connect_timeout)

    def disconnect(self) -> None:
        self._transport.disconnect()

    def is_connected(self) -> bool:
        return self._transport.connected

    def clean(self) -> CommandResult:
        return self._send_cmd("clean")

    def pause(self) -> CommandResult:
        return self._send_cmd("pause")

    def resume(self) -> CommandResult:
        return self._send_cmd("resume")

    def dock(self) -> CommandResult:
        return self._send_cmd("dock")

    def stop(self) -> CommandResult:
        return self._send_cmd("stop")

    def set_preferences(self, patch: PreferencesPatch) -> CommandResult:
        if patch.is_empty():
            raise ValidationError("Preferences patch must include at least one field")

        payload = self._transport.publish_delta(
            _map_preferences_patch(patch), timeout=self._command_timeout
        )
        return CommandResult(
            ok=True,
            topic="delta",
            command="set_preferences",
            sent_at_unix=int(time.time()),
            request_payload=payload,
        )

    def get_state(
        self,
        required_fields: list[StateField] | None = None,
        *,
        timeout: float | None = None,
    ) -> RobotState:
        deadline = None if timeout is None else (time.time() + timeout)

        while required_fields:
            with self._state_lock:
                missing = [
                    field
                    for field in required_fields
                    if getattr(self._state, field.value) is None
                ]
            if not missing:
                break
            if deadline is not None and time.time() >= deadline:
                missing_values = ", ".join(field.value for field in missing)
                raise TimeoutError(f"Required fields unavailable before timeout: {missing_values}")
            time.sleep(0.05)

        with self._state_lock:
            return self._state.model_copy(deep=True)

    def get_mission(self, *, timeout: float | None = None) -> MissionSnapshot:
        state = self.get_state(
            [StateField.CLEAN_MISSION_STATUS, StateField.BIN, StateField.BAT_PCT], timeout=timeout
        )
        return MissionSnapshot(
            clean_mission_status=state.clean_mission_status,
            bin=state.bin,
            bat_pct=state.bat_pct,
            pose=state.pose,
            observed_at_unix=int(time.time()),
        )

    def get_basic_mission(self, *, timeout: float | None = None) -> MissionSnapshot:
        state = self.get_state(
            [StateField.CLEAN_MISSION_STATUS, StateField.BIN, StateField.BAT_PCT], timeout=timeout
        )
        return MissionSnapshot(
            clean_mission_status=state.clean_mission_status,
            bin=state.bin,
            bat_pct=state.bat_pct,
            pose=None,
            observed_at_unix=int(time.time()),
        )

    def add_state_listener(self, callback: Callable[[RobotState], None]) -> str:
        listener_id = str(uuid.uuid4())
        self._state_listeners[listener_id] = callback
        return listener_id

    def add_mission_listener(self, callback: Callable[[MissionSnapshot], None]) -> str:
        listener_id = str(uuid.uuid4())
        self._mission_listeners[listener_id] = callback
        return listener_id

    def remove_listener(self, listener_id: str) -> None:
        self._state_listeners.pop(listener_id, None)
        self._mission_listeners.pop(listener_id, None)

    def _send_cmd(self, command: str) -> CommandResult:
        payload = self._transport.publish_command(command, timeout=self._command_timeout)
        return CommandResult(
            ok=True,
            topic="cmd",
            command=command,
            sent_at_unix=int(payload["time"]),
            request_payload=payload,
        )

    def _on_payload(self, payload: dict[str, Any]) -> None:
        reported = _extract_reported(payload)
        updates = _map_reported_to_state(reported)

        mission_snapshot: MissionSnapshot | None = None
        with self._state_lock:
            for key, value in updates.items():
                setattr(self._state, key, value)
            self._state.raw = payload
            state_snapshot = self._state.model_copy(deep=True)

            if self._state.clean_mission_status is not None:
                mission_snapshot = MissionSnapshot(
                    clean_mission_status=self._state.clean_mission_status,
                    bin=self._state.bin,
                    bat_pct=self._state.bat_pct,
                    pose=self._state.pose,
                    observed_at_unix=int(time.time()),
                )

        for callback in list(self._state_listeners.values()):
            try:
                callback(state_snapshot)
            except Exception:
                continue

        if mission_snapshot is not None:
            for callback in list(self._mission_listeners.values()):
                try:
                    callback(mission_snapshot)
                except Exception:
                    continue


def _extract_reported(payload: dict[str, Any]) -> dict[str, Any]:
    state = payload.get("state")
    if isinstance(state, dict):
        reported = state.get("reported")
        if isinstance(reported, dict):
            return reported

    reported = payload.get("reported")
    if isinstance(reported, dict):
        return reported

    return {}


def _map_reported_to_state(reported: dict[str, Any]) -> dict[str, Any]:
    updates: dict[str, Any] = {}

    clean_mission_status = reported.get("cleanMissionStatus")
    if isinstance(clean_mission_status, dict):
        updates["clean_mission_status"] = CleanMissionStatus.model_validate(
            {
                "cycle": clean_mission_status.get("cycle", "unknown"),
                "phase": clean_mission_status.get("phase", "unknown"),
                "error": int(clean_mission_status.get("error", 0)),
                "not_ready": clean_mission_status.get("notReady"),
                "mssn_m": clean_mission_status.get("mssnM"),
                "sqft": clean_mission_status.get("sqft"),
                "initiator": clean_mission_status.get("initiator"),
                "n_mssn": clean_mission_status.get("nMssn"),
            }
        )

    bin_status = reported.get("bin")
    if isinstance(bin_status, dict):
        updates["bin"] = BinStatus.model_validate(
            {
                "present": bin_status.get("present"),
                "full": bin_status.get("full"),
            }
        )

    if "batPct" in reported:
        updates["bat_pct"] = int(reported["batPct"])

    pose = reported.get("pose")
    if isinstance(pose, dict):
        point = pose.get("point")
        if isinstance(point, dict) and "x" in point and "y" in point and "theta" in pose:
            updates["pose"] = Pose.model_validate(
                {
                    "theta": int(pose["theta"]),
                    "point": {"x": int(point["x"]), "y": int(point["y"])},
                }
            )

    if "name" in reported and isinstance(reported["name"], str):
        updates["name"] = reported["name"]

    signal = reported.get("signal")
    if isinstance(signal, dict):
        updates["signal"] = SignalInfo.model_validate(
            {
                "rssi": signal.get("rssi"),
                "snr": signal.get("snr"),
            }
        )

    return updates


def _map_preferences_patch(patch: PreferencesPatch) -> dict[str, Any]:
    mapped: dict[str, Any] = {}

    if patch.carpet_boost_mode is not None:
        if patch.carpet_boost_mode == CarpetBoostMode.AUTO:
            mapped["carpetBoost"] = True
            mapped["vacHigh"] = False
        elif patch.carpet_boost_mode == CarpetBoostMode.PERFORMANCE:
            mapped["carpetBoost"] = False
            mapped["vacHigh"] = True
        elif patch.carpet_boost_mode == CarpetBoostMode.ECO:
            mapped["carpetBoost"] = False
            mapped["vacHigh"] = False

    if patch.edge_clean_enabled is not None:
        mapped["openOnly"] = not patch.edge_clean_enabled

    if patch.cleaning_passes is not None:
        if patch.cleaning_passes == CleaningPasses.AUTO:
            mapped["noAutoPasses"] = False
            mapped["twoPass"] = False
        elif patch.cleaning_passes == CleaningPasses.ONE:
            mapped["noAutoPasses"] = True
            mapped["twoPass"] = False
        elif patch.cleaning_passes == CleaningPasses.TWO:
            mapped["noAutoPasses"] = True
            mapped["twoPass"] = True

    if patch.always_finish is not None:
        mapped["binPause"] = not patch.always_finish

    return mapped
