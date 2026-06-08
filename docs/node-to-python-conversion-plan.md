# Node.js to Python Conversion Plan (Reduced API)

**Project:** dorita980
**Goal:** Port the current Node.js local-control component to a Python package with a smaller, stable API surface.

## 1. Objectives

- Replace Node.js runtime usage for core robot control with a Python implementation.
- Preserve behavior for a reduced feature set only.
- Keep the design implementation-ready for future expansion.

## 2. Reduced API Target

The Python API should support only:

- Connection lifecycle: `connect`, `disconnect`, `is_connected`
- Commands: `clean`, `pause`, `resume`, `dock`, `stop`
- Reads: `get_state`, `get_mission`, `get_basic_mission`
- Preferences patch: `set_preferences`
- Discovery helpers: `discover_robots`, `get_robot_public_info`

Out of scope for first release:

- Cloud APIs
- Full v1 parity
- Complete legacy command coverage

## 3. Source-to-Target Mapping

Node source behavior to mirror:

- Entry API selection in `index.js`
- Local MQTT/TLS control in `lib/v2/local.js`
- UDP discovery in `lib/discovery.js`
- Preference mapping conventions used by local v2 methods

Planned Python package:

- `roomba_python.client`
- `roomba_python.models`
- `roomba_python.discovery`
- `roomba_python.transport`
- `roomba_python.errors`

## 4. Migration Strategy

### Phase 0: Contract Freeze

- Finalize reduced API signatures and model shapes.
- Use the existing spec documents as source of truth:
  - `docs/reduced-python-api-spec.md`
  - `docs/reduced-python-api-openapi-like.yaml`
  - `docs/reduced-python-api-openapi-companion.md`

### Phase 1: Project Skeleton

- Create Python package layout and `pyproject.toml`.
- Add dependency baseline (expected):
  - `paho-mqtt`
  - `pydantic` (or dataclasses alternative)
  - `pytest`
- Add lint/format config and CI test entry command.

### Phase 2: Core Transport

- Implement MQTT/TLS client wrapper:
  - Connection setup
  - Publish abstraction for command and delta topics
  - Message subscription and telemetry ingestion
  - Graceful disconnect and reconnect behavior
- Add configuration support for TLS legacy and custom ciphers.

### Phase 3: State Engine

- Implement in-memory normalized state cache.
- Convert inbound telemetry keys to snake_case.
- Preserve raw telemetry payload in `RobotState.raw`.
- Implement wait-for-fields behavior used by `get_state` and mission reads.

### Phase 4: Command Layer

- Implement `clean`, `pause`, `resume`, `dock`, `stop`.
- Implement `set_preferences` patch mapping to delta payload shape.
- Return strict `CommandResult` model for all command calls.

### Phase 5: Discovery Layer

- Implement UDP discovery broadcast helper.
- Implement single-IP public info helper.
- Return `RobotDiscoveryInfo` typed model.

### Phase 6: Error Handling

- Implement typed exceptions:
  - `ValidationError`
  - `ConnectionError`
  - `AuthenticationError`
  - `PublishError`
  - `TimeoutError`
  - `ProtocolError`
- Normalize lower-level library errors into public exceptions.

### Phase 7: Tests and Validation

- Unit tests for:
  - Payload builders
  - Preferences patch mapping
  - State normalization and field waiting
  - Error mapping and exception boundary conversion
- Integration tests for:
  - Connect/disconnect
  - Publish ack path
  - Telemetry ingestion flow
  - Reconnect behavior after unexpected disconnect
  - Subscription continuity after reconnect
  - Publish timeout and publish rc failure handling
  - Malformed telemetry payload handling at protocol boundaries
- Validate responses against schema objects in the OpenAPI-like document.

### Phase 8: Documentation and Release

- Add Python usage examples for common flows.
  - Example set should include: connect/disconnect lifecycle, command execution, preferences update, mission read, and discovery flow.
  - Keep runnable examples in `examples/` and reference them from `README.md`.
- Publish migration notes from Node method names to Python methods.
  - Include a Node.js to Python method mapping table in docs.
  - Include unsupported/changed behavior notes for reduced scope.
- Tag first alpha release for feedback.

### Phase Completion Status (as of 2026-06-05)

- Phase 0 (Contract Freeze): complete.
- Phase 1 (Project Skeleton): complete.
- Phase 2 (Core Transport): complete.
- Phase 3 (State Engine): complete with telemetry normalization, raw payload preservation, and wait-for-fields behavior.
- Phase 4 (Command Layer): complete for reduced API scope (`clean`, `pause`, `resume`, `dock`, `stop`, `set_preferences`).
- Phase 5 (Discovery Layer): complete with typed discovery responses.
- Phase 6 (Error Handling): complete, including boundary conversion mapping and dedicated documentation.
- Phase 7 (Tests and Validation): complete, including core, integration-style, and schema conformance coverage.
- Phase 8 (Documentation and Release): complete for implementation deliverables, including runnable examples, migration notes, and alpha release checklist.

### Verification Artifacts

- Command layer coverage: `tests/test_command_layer.py`
- Discovery coverage: `tests/test_discovery.py`
- State engine coverage: `tests/test_client_state_ingestion.py`, `tests/test_client_listeners.py`
- Transport boundary coverage: `tests/test_transport.py`
- Schema conformance coverage: `tests/test_schema_conformance.py`
- Error boundary documentation: `docs/error-handling-boundary-map.md`
- Alpha release runbook: `docs/alpha-release-checklist.md`

## 5. Milestones and Exit Criteria

### Milestone A: Transport Ready

- Can establish MQTT/TLS session and receive telemetry updates.

### Milestone B: Functional Reduced API

- All reduced methods implemented and returning typed models.

### Milestone C: Quality Gate

- Test suite passes for core behavior and error paths.
- Public API documented and consistent with schema docs.

### Milestone D: Alpha Release

- Package installable.
- Core usage flow works on at least one supported robot family.

## 6. Risks and Mitigations

- TLS incompatibilities on some firmware/node history equivalents.
  - Mitigation: configurable cipher and legacy TLS flags.
- Telemetry field variability by robot model.
  - Mitigation: optional fields plus wait-for-fields timeout handling.
- Drift between implementation and published schema.
  - Mitigation: schema validation in tests and release checklist.

## 7. Suggested Timeline

- Week 1: Phase 0-2
- Week 2: Phase 3-4
- Week 3: Phase 5-7
- Week 4: Phase 8 and alpha release hardening

## 8. Definition of Done

- Reduced Python API implemented with typed responses.
- Required discovery and command workflows functional.
- Error behavior predictable and documented.
- Specs, companion docs, and code behavior are aligned.
