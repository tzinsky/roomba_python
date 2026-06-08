from __future__ import annotations

from roomba_python.client import RobotClient


def _payload() -> dict:
    return {
        "state": {
            "reported": {
                "cleanMissionStatus": {
                    "cycle": "clean",
                    "phase": "run",
                    "error": 0,
                },
                "bin": {"present": True, "full": False},
                "batPct": 90,
            }
        }
    }


def test_state_listener_invoked_on_payload_update() -> None:
    client = RobotClient("blid", "password", "192.168.1.2")
    updates: list[int | None] = []

    def on_state(state) -> None:
        updates.append(state.bat_pct)

    client.add_state_listener(on_state)
    client._on_payload(_payload())

    assert updates == [90]


def test_mission_listener_invoked_on_payload_update() -> None:
    client = RobotClient("blid", "password", "192.168.1.2")
    missions: list[int | None] = []

    def on_mission(mission) -> None:
        missions.append(mission.bat_pct)

    client.add_mission_listener(on_mission)
    client._on_payload(_payload())

    assert missions == [90]
