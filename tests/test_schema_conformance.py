from __future__ import annotations

from pathlib import Path

import yaml
from jsonschema import validate

from roomba_python.models import (
    BinStatus,
    CleanMissionStatus,
    CommandResult,
    MissionSnapshot,
    Pose,
    PosePoint,
    RobotState,
)


def _load_openapi_like_spec() -> dict:
    root = Path(__file__).resolve().parent.parent
    spec_path = root / "docs" / "reduced-python-api-openapi-like.yaml"
    with spec_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _schema_for(spec: dict, schema_name: str) -> dict:
    return {
        "$schema": spec.get("jsonSchemaDialect", "https://json-schema.org/draft/2020-12/schema"),
        "$ref": f"#/components/schemas/{schema_name}",
        "components": spec["components"],
    }


def test_robot_state_matches_openapi_schema() -> None:
    spec = _load_openapi_like_spec()
    schema = _schema_for(spec, "RobotState")

    state = RobotState(
        clean_mission_status=CleanMissionStatus(cycle="clean", phase="run", error=0),
        bin=BinStatus(present=True, full=False),
        bat_pct=80,
        pose=Pose(theta=10, point=PosePoint(x=2, y=-3)),
        name="Dorita",
        raw={"state": {"reported": {"batPct": 80}}},
    )

    validate(instance=state.model_dump(), schema=schema)


def test_mission_snapshot_matches_openapi_schema() -> None:
    spec = _load_openapi_like_spec()
    schema = _schema_for(spec, "MissionSnapshot")

    mission = MissionSnapshot(
        clean_mission_status=CleanMissionStatus(cycle="clean", phase="run", error=0),
        bin=BinStatus(present=True, full=False),
        bat_pct=76,
        pose=Pose(theta=15, point=PosePoint(x=12, y=8)),
        observed_at_unix=1760000000,
    )

    validate(instance=mission.model_dump(), schema=schema)


def test_command_result_matches_openapi_schema() -> None:
    spec = _load_openapi_like_spec()
    schema = _schema_for(spec, "CommandResult")

    result = CommandResult(
        ok=True,
        topic="cmd",
        command="clean",
        sent_at_unix=1760000000,
        request_payload={"command": "clean", "time": 1760000000, "initiator": "localApp"},
    )

    validate(instance=result.model_dump(), schema=schema)


def test_error_response_shape_matches_openapi_schema() -> None:
    spec = _load_openapi_like_spec()
    schema = _schema_for(spec, "ErrorResponse")

    payload = {
        "code": "protocol_error",
        "message": "Unable to parse MQTT payload JSON",
        "details": {"topic": "#"},
    }

    validate(instance=payload, schema=schema)
