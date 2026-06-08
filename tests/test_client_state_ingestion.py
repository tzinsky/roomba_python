from __future__ import annotations

import threading
import time

import pytest

from roomba_python.client import RobotClient
from roomba_python.errors import TimeoutError
from roomba_python.types import StateField


def _mission_payload() -> dict:
    return {
        "state": {
            "reported": {
                "cleanMissionStatus": {
                    "cycle": "clean",
                    "phase": "run",
                    "error": 0,
                    "notReady": 0,
                    "mssnM": 7,
                    "sqft": 50,
                    "initiator": "localApp",
                    "nMssn": 100,
                },
                "bin": {"present": True, "full": False},
                "batPct": 82,
                "pose": {"theta": 10, "point": {"x": 1, "y": -2}},
                "name": "Dorita",
                "signal": {"rssi": -47, "snr": 31},
            }
        }
    }


def test_telemetry_updates_state_and_normalizes_fields() -> None:
    client = RobotClient("blid", "password", "192.168.1.2")

    client._on_payload(_mission_payload())

    state = client.get_state(
        [StateField.CLEAN_MISSION_STATUS, StateField.BAT_PCT, StateField.BIN],
        timeout=0.1,
    )

    assert state.clean_mission_status is not None
    assert state.clean_mission_status.not_ready == 0
    assert state.clean_mission_status.mssn_m == 7
    assert state.clean_mission_status.n_mssn == 100
    assert state.bat_pct == 82
    assert state.pose is not None
    assert state.pose.point.x == 1
    assert state.name == "Dorita"
    assert state.signal is not None
    assert state.signal.rssi == -47


def test_raw_payload_preserved_in_state() -> None:
    client = RobotClient("blid", "password", "192.168.1.2")
    payload = _mission_payload()

    client._on_payload(payload)

    state = client.get_state(timeout=0.1)
    assert state.raw == payload


def test_get_state_timeout_lists_missing_fields() -> None:
    client = RobotClient("blid", "password", "192.168.1.2")

    with pytest.raises(TimeoutError) as exc_info:
        client.get_state([StateField.BAT_PCT], timeout=0.01)

    assert "bat_pct" in str(exc_info.value)


def test_get_state_waits_for_field_then_returns() -> None:
    client = RobotClient("blid", "password", "192.168.1.2")

    def delayed_payload() -> None:
        time.sleep(0.02)
        client._on_payload({"state": {"reported": {"batPct": 55}}})

    threading.Thread(target=delayed_payload, daemon=True).start()

    state = client.get_state([StateField.BAT_PCT], timeout=0.2)
    assert state.bat_pct == 55
