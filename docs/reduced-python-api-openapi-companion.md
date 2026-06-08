# Companion Guide: Reduced Python API OpenAPI-like Schema

This guide is a human-readable companion to the strict schema in:

- `docs/reduced-python-api-openapi-like.yaml`

It summarizes each operation, provides example payloads, and maps behavior to the intended Python client API.

## 1. Purpose and Framing

The OpenAPI-like document models a Python client API using RPC-style paths.  
It is not intended to imply HTTP transport in production.

Runtime transport is:

- MQTT over TLS for robot commands and telemetry
- UDP for discovery

## 2. Operation Index

### Robot Client Operations

- `POST /client/connect`
- `POST /client/disconnect`
- `GET /client/is-connected`
- `POST /client/commands/clean`
- `POST /client/commands/pause`
- `POST /client/commands/resume`
- `POST /client/commands/dock`
- `POST /client/commands/stop`
- `PATCH /client/preferences`
- `POST /client/state`
- `GET /client/mission`
- `GET /client/mission/basic`

### Discovery Operations

- `GET /discovery/robots`
- `GET /discovery/robot-public-info`

## 3. Connection Lifecycle Examples

### 3.1 Connect Request

```json
{
  "blid": "0123456789ABCDEF",
  "password": ":1:1700000000:example-secret",
  "host": "192.168.1.104",
  "port": 8883,
  "emit_interval": 0.8,
  "connect_timeout": 10.0,
  "command_timeout": 5.0,
  "tls_legacy": null,
  "ciphers": null
}
```

### 3.2 Connect Success Response

```json
{
  "connected": true
}
```

### 3.3 Disconnect Success Response

```json
{
  "connected": false
}
```

### 3.4 Is Connected Response

```json
{
  "connected": true
}
```

## 4. Command Operation Examples

All core command endpoints produce `CommandResult`.

### 4.1 Clean

Request body: none

Example success:

```json
{
  "ok": true,
  "topic": "cmd",
  "command": "clean",
  "sent_at_unix": 1765000000,
  "request_payload": {
    "command": "clean",
    "time": 1765000000,
    "initiator": "localApp"
  }
}
```

### 4.2 Pause, Resume, Dock, Stop

Request body: none

Behavior is identical to clean, except:

- `command` and `request_payload.command` are one of `pause`, `resume`, `dock`, `stop`

## 5. Preferences Patch Example

Endpoint: `PATCH /client/preferences`

### 5.1 Request (one-field patch)

```json
{
  "cleaning_passes": "two"
}
```

### 5.2 Request (multi-field patch)

```json
{
  "carpet_boost_mode": "performance",
  "edge_clean_enabled": true,
  "always_finish": false
}
```

### 5.3 Success Response

```json
{
  "ok": true,
  "topic": "delta",
  "command": "set_preferences",
  "sent_at_unix": 1765000001,
  "request_payload": {
    "state": {
      "carpetBoost": false,
      "vacHigh": true,
      "openOnly": false,
      "binPause": true
    }
  }
}
```

### 5.4 Validation Error Example

```json
{
  "code": "validation_error",
  "message": "Preferences patch must include at least one field",
  "details": null
}
```

## 6. State and Mission Examples

### 6.1 Get State Request

Endpoint: `POST /client/state`

```json
{
  "required_fields": ["clean_mission_status", "bat_pct", "bin"],
  "timeout": 5.0
}
```

### 6.2 Get State Success Response

```json
{
  "clean_mission_status": {
    "cycle": "none",
    "phase": "charge",
    "error": 0,
    "not_ready": 0,
    "mssn_m": 12,
    "sqft": 0,
    "initiator": "localApp",
    "n_mssn": 321
  },
  "bin": {
    "present": true,
    "full": false
  },
  "bat_pct": 96,
  "pose": null,
  "name": "Dorita",
  "signal": {
    "rssi": -49,
    "snr": 35
  },
  "raw": {
    "cleanMissionStatus": {
      "cycle": "none",
      "phase": "charge",
      "error": 0
    }
  }
}
```

### 6.3 Get Mission Success Response

Endpoint: `GET /client/mission?timeout=3.0`

```json
{
  "clean_mission_status": {
    "cycle": "clean",
    "phase": "run",
    "error": 0,
    "not_ready": 0,
    "mssn_m": 7,
    "sqft": 85,
    "initiator": "localApp",
    "n_mssn": 322
  },
  "bin": {
    "present": true,
    "full": false
  },
  "bat_pct": 78,
  "pose": {
    "theta": 33,
    "point": {
      "x": 142,
      "y": -18
    }
  },
  "observed_at_unix": 1765000010
}
```

### 6.4 Timeout Error Example

```json
{
  "code": "timeout_error",
  "message": "Required fields unavailable before timeout",
  "details": {
    "required_fields": ["pose"]
  }
}
```

## 7. Discovery Examples

### 7.1 Discover Robots

Endpoint: `GET /discovery/robots?timeout=2.0&broadcast_ip=255.255.255.255&port=5678`

Example response:

```json
[
  {
    "ver": "2",
    "hostname": "Roomba-0123456789ABCDEF",
    "robotname": "Dorita",
    "ip": "192.168.1.104",
    "mac": "12:34:56:78:9a:bc",
    "sw": "v2.4.16-126",
    "sku": "R98----",
    "nc": 0,
    "proto": "mqtt",
    "blid": null
  }
]
```

### 7.2 Get Robot Public Info

Endpoint: `GET /discovery/robot-public-info?ip=192.168.1.104&timeout=2.0&port=5678`

Example response:

```json
{
  "ver": "2",
  "hostname": "Roomba-0123456789ABCDEF",
  "robotname": "Dorita",
  "ip": "192.168.1.104",
  "mac": "12:34:56:78:9a:bc",
  "sw": "v2.4.16-126",
  "sku": "R98----",
  "nc": 0,
  "proto": "mqtt",
  "blid": "0123456789ABCDEF"
}
```

## 8. Error Model Cheatsheet

Possible error codes:

- `validation_error`
- `connection_error`
- `authentication_error`
- `publish_error`
- `timeout_error`
- `protocol_error`

Generic error shape:

```json
{
  "code": "publish_error",
  "message": "Unable to publish command",
  "details": {
    "topic": "cmd"
  }
}
```

## 9. Schema-to-Python Mapping

The RPC-style operation IDs map directly to Python methods:

- `connect` -> `RobotClient.connect()`
- `disconnect` -> `RobotClient.disconnect()`
- `isConnected` -> `RobotClient.is_connected()`
- `clean` -> `RobotClient.clean()`
- `pause` -> `RobotClient.pause()`
- `resume` -> `RobotClient.resume()`
- `dock` -> `RobotClient.dock()`
- `stop` -> `RobotClient.stop()`
- `setPreferences` -> `RobotClient.set_preferences()`
- `getState` -> `RobotClient.get_state()`
- `getMission` -> `RobotClient.get_mission()`
- `getBasicMission` -> `RobotClient.get_basic_mission()`
- `discoverRobots` -> `discover_robots()`
- `getRobotPublicInfo` -> `get_robot_public_info()`

## 10. Validation Notes for Implementers

- Treat the schema as strict for public inputs (`additionalProperties: false` in key request types).
- Keep public field names in snake_case.
- Preserve unnormalized telemetry in `RobotState.raw`.
- Remember that command success indicates publish acknowledgement, not mission completion.
