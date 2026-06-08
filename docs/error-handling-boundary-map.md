# Error Handling Boundary Map

This document defines how lower-level failures are normalized into public `roomba_python` exceptions.

## Public Exception Types

- `ValidationError`
- `ConnectionError`
- `AuthenticationError`
- `PublishError`
- `TimeoutError`
- `ProtocolError`

## Boundary Conversion Rules

### 1. Client input and API validation

Origin:

- `RobotClient.set_preferences()` and other public method argument checks

Mapped to:

- `ValidationError`

Examples:

- Empty preferences patch
- Invalid user-provided value combinations

### 2. Connection and transport initialization

Origin:

- MQTT connect failures
- TLS handshake errors
- Network socket errors during initial connect

Mapped to:

- `AuthenticationError` when broker rejects credentials
- `ConnectionError` for network/TLS/connect-path failures

### 3. Command publish path

Origin:

- MQTT publish return code indicates failure
- Publish acknowledgement timeout
- Publish attempted when disconnected

Mapped to:

- `PublishError`

Notes:

- Error messages include relevant topic and return-code context where available.

### 4. Telemetry protocol boundary

Origin:

- Payload cannot be decoded from UTF-8
- Payload cannot be parsed as JSON
- Parsed payload shape is not a JSON object
- Payload handler raises while processing telemetry

Mapped to:

- `ProtocolError`

Notes:

- Transport stores protocol-boundary failures in `last_error` to preserve client stability.

### 5. Wait-for-fields and operation timing

Origin:

- State/mission polling exceeds timeout before required fields are present
- Discovery request exceeds timeout without robot response

Mapped to:

- `TimeoutError`

## Reconnect and Runtime State

Runtime disconnects and reconnect attempts are tracked by transport internals:

- `reconnect_failures`: counter of unexpected disconnect events
- `last_error`: latest mapped boundary error when available

These are intended for diagnostics, testing, and observability in reduced-scope releases.

## Guidance for Future Changes

- Always map lower-level library errors to public exception types at module boundaries.
- Preserve source error context with exception chaining where practical.
- Keep error messages actionable and include protocol/topic/reason-code context.
- Add or update tests whenever a new boundary conversion path is introduced.
