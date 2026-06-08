# Reduced Python API Specification

**Version:** 0.1 (draft)  
**Project:** dorita980 Python migration (reduced scope)

## 1. Scope and Non-Goals

This specification defines a minimal Python API for local LAN control of supported robots.

### In Scope

- Connection lifecycle
- Core commands: `clean`, `pause`, `resume`, `dock`, `stop`
- Mission and state reads
- Preferences patch
- UDP discovery helpers

### Out of Scope (v0.1)

- Cloud login and cloud command APIs
- Full legacy v1 parity
- Complete telemetry parity across all firmware fields

## 2. Package Layout

Package name: `roomba_python`

Public modules:

- `roomba_python.client`
- `roomba_python.models`
- `roomba_python.discovery`
- `roomba_python.errors`
- `roomba_python.types`

## 3. Public API Signatures

### 3.1 Robot Client

```python
class RobotClient:
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
    ) -> None: ...

    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def is_connected(self) -> bool: ...

    def clean(self) -> CommandResult: ...
    def pause(self) -> CommandResult: ...
    def resume(self) -> CommandResult: ...
    def dock(self) -> CommandResult: ...
    def stop(self) -> CommandResult: ...

    def set_preferences(self, patch: PreferencesPatch) -> CommandResult: ...

    def get_state(
        self,
        required_fields: list[StateField] | None = None,
        *,
        timeout: float | None = None,
    ) -> RobotState: ...

    def get_mission(self, *, timeout: float | None = None) -> MissionSnapshot: ...
    def get_basic_mission(self, *, timeout: float | None = None) -> MissionSnapshot: ...

    def add_state_listener(
        self,
        callback: Callable[[RobotState], None],
    ) -> str: ...

    def add_mission_listener(
        self,
        callback: Callable[[MissionSnapshot], None],
    ) -> str: ...

    def remove_listener(self, listener_id: str) -> None: ...
```

### 3.2 Discovery Helpers

```python
def discover_robots(
    *,
    timeout: float = 2.0,
    broadcast_ip: str = "255.255.255.255",
    port: int = 5678,
) -> list[RobotDiscoveryInfo]: ...

def get_robot_public_info(
    ip: str,
    *,
    timeout: float = 2.0,
    port: int = 5678,
) -> RobotDiscoveryInfo: ...
```

## 4. Response and Request Models

### 4.1 CommandResult

```python
class CommandResult(BaseModel):
    ok: bool
    topic: Literal["cmd", "delta"]
    command: str
    sent_at_unix: int
    request_payload: dict[str, Any]
```

### 4.2 Mission Models

```python
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
```

### 4.3 State Model

```python
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
    raw: dict[str, Any] = {}
```

### 4.4 Preferences Patch

```python
class CarpetBoostMode(str, Enum):
    auto = "auto"
    performance = "performance"
    eco = "eco"

class CleaningPasses(str, Enum):
    auto = "auto"
    one = "one"
    two = "two"

class PreferencesPatch(BaseModel):
    carpet_boost_mode: CarpetBoostMode | None = None
    edge_clean_enabled: bool | None = None
    cleaning_passes: CleaningPasses | None = None
    always_finish: bool | None = None
```

Delta mapping:

- `carpet_boost_mode=auto` -> `{"carpetBoost": true, "vacHigh": false}`
- `carpet_boost_mode=performance` -> `{"carpetBoost": false, "vacHigh": true}`
- `carpet_boost_mode=eco` -> `{"carpetBoost": false, "vacHigh": false}`
- `edge_clean_enabled=true` -> `{"openOnly": false}`
- `edge_clean_enabled=false` -> `{"openOnly": true}`
- `cleaning_passes=auto` -> `{"noAutoPasses": false, "twoPass": false}`
- `cleaning_passes=one` -> `{"noAutoPasses": true, "twoPass": false}`
- `cleaning_passes=two` -> `{"noAutoPasses": true, "twoPass": true}`
- `always_finish=true` -> `{"binPause": false}`
- `always_finish=false` -> `{"binPause": true}`

## 5. Field Naming Contract

- Public Python models use `snake_case`.
- Incoming robot payload keys are normalized from `camelCase` to `snake_case`.
- Raw unmodified payload is retained in `RobotState.raw`.

## 6. StateField Enum

```python
class StateField(str, Enum):
    clean_mission_status = "clean_mission_status"
    bin = "bin"
    bat_pct = "bat_pct"
    pose = "pose"
    name = "name"
    signal = "signal"
```

## 7. Command Transport Contract

- Command methods publish to topic `cmd` with payload:
  - `{"command": "<name>", "time": <unix-int>, "initiator": "localApp"}`
- `set_preferences` publishes to topic `delta` with payload:
  - `{"state": {...mapped patch fields...}}`
- Command success indicates publish acknowledgement, not task completion on robot.
- Mission progress and completion are observed via telemetry updates.

## 8. Error Model

```python
class DoritaError(Exception): ...
class ValidationError(DoritaError): ...
class ConnectionError(DoritaError): ...
class AuthenticationError(DoritaError): ...
class PublishError(DoritaError): ...
class TimeoutError(DoritaError): ...
class ProtocolError(DoritaError): ...
```

Behavior by method:

- `connect` raises `ConnectionError` or `AuthenticationError` on handshake/login failure.
- Command methods raise `PublishError` if publish fails.
- `get_state`, `get_mission`, `get_basic_mission` raise `TimeoutError` on timeout.
- `set_preferences` raises `ValidationError` if patch is empty.

## 9. Timeout and Retry Rules

- `connect_timeout` default: `10.0` seconds
- `command_timeout` default: `5.0` seconds
- `get_state(timeout=None)` waits indefinitely
- No automatic command retry in v0.1
- Reconnect policy:
  - Allowed for telemetry subscription stream
  - In-flight command calls fail fast on disconnect

## 10. Listener Semantics

- `add_state_listener` callback is called on every parsed state update.
- `add_mission_listener` callback is called at most once per `emit_interval` with latest mission snapshot.
- Listener exceptions are caught and logged.
- `remove_listener` is idempotent.

## 11. Minimal Usage Contract

Typical sequence:

1. Instantiate `RobotClient`.
2. Call `connect()`.
3. Issue commands and/or read mission/state.
4. Call `disconnect()`.

The same client instance may be reused across multiple connect and disconnect cycles.

## 12. Versioning Policy

- API stability target starts at `0.x` for rapid iteration.
- Breaking changes are allowed before `1.0`.
- At `1.0`, method names and model fields in this document become stable contract.
