"""Shared enums and type aliases."""

from enum import StrEnum


class CarpetBoostMode(StrEnum):
    AUTO = "auto"
    PERFORMANCE = "performance"
    ECO = "eco"


class CleaningPasses(StrEnum):
    AUTO = "auto"
    ONE = "one"
    TWO = "two"


class StateField(StrEnum):
    CLEAN_MISSION_STATUS = "clean_mission_status"
    BIN = "bin"
    BAT_PCT = "bat_pct"
    POSE = "pose"
    NAME = "name"
    SIGNAL = "signal"
