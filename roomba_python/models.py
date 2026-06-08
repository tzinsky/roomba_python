"""Pydantic models for the reduced API contract."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from .types import CarpetBoostMode, CleaningPasses


class CommandResult(BaseModel):
    ok: bool
    topic: Literal["cmd", "delta"]
    command: str
    sent_at_unix: int
    request_payload: dict[str, Any]


class PosePoint(BaseModel):
    x: int
    y: int


class Pose(BaseModel):
    theta: int
    point: PosePoint


class CleanMissionStatus(BaseModel):
    cycle: str
    phase: str
    error: int
    not_ready: int | None = None
    mssn_m: int | None = None
    sqft: int | None = None
    initiator: str | None = None
    n_mssn: int | None = None


class BinStatus(BaseModel):
    present: bool | None = None
    full: bool | None = None


class MissionSnapshot(BaseModel):
    clean_mission_status: CleanMissionStatus
    bin: BinStatus | None = None
    bat_pct: int | None = None
    pose: Pose | None = None
    observed_at_unix: int


class SignalInfo(BaseModel):
    rssi: int | None = None
    snr: int | None = None


class RobotState(BaseModel):
    clean_mission_status: CleanMissionStatus | None = None
    bin: BinStatus | None = None
    bat_pct: int | None = None
    pose: Pose | None = None
    name: str | None = None
    signal: SignalInfo | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class PreferencesPatch(BaseModel):
    carpet_boost_mode: CarpetBoostMode | None = None
    edge_clean_enabled: bool | None = None
    cleaning_passes: CleaningPasses | None = None
    always_finish: bool | None = None

    def is_empty(self) -> bool:
        return not any(
            [
                self.carpet_boost_mode is not None,
                self.edge_clean_enabled is not None,
                self.cleaning_passes is not None,
                self.always_finish is not None,
            ]
        )


class RobotDiscoveryInfo(BaseModel):
    hostname: str
    ip: str
    ver: str | None = None
    robotname: str | None = None
    mac: str | None = None
    sw: str | None = None
    sku: str | None = None
    nc: int | None = None
    proto: str | None = None
    blid: str | None = None
