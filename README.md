# roomba_python

[![CI](https://github.com/tzinsky/roomba_python/actions/workflows/ci.yml/badge.svg)](https://github.com/tzinsky/roomba_python/actions/workflows/ci.yml)
[![Package](https://github.com/tzinsky/roomba_python/actions/workflows/package.yml/badge.svg)](https://github.com/tzinsky/koalazak/roomba_python/actions/workflows/package.yml)

A reduced-scope implementation of the dorita980 Node.JS project https://github.com/koalazak/dorita980) for Roomba control.

## Status

This repository currently contains the initial project structure and typed API skeleton.

## Planned API surface

- Connection lifecycle: `connect`, `disconnect`, `is_connected`
- Commands: `clean`, `pause`, `resume`, `dock`, `stop`
- Reads: `get_state`, `get_mission`, `get_basic_mission`
- Preferences patch: `set_preferences`
- Discovery: `discover_robots`, `get_robot_public_info`

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```

## Usage examples

Common runnable flows are available in `examples/`:

- `examples/connect_lifecycle.py` - connect/disconnect lifecycle
- `examples/command_execution.py` - command execution (`clean`, `pause`, `resume`, `dock`)
- `examples/preferences_update.py` - preferences update using typed patch model
- `examples/mission_read.py` - mission read flow (`get_basic_mission`)
- `examples/discovery_flow.py` - discovery and public info flow
- `examples/basic_usage.py` - compact all-in-one starter

## Reference docs

See the conversion docs in this project:

- `docs/reduced-python-api-spec.md`
- `docs/reduced-python-api-openapi-like.yaml`
- `docs/reduced-python-api-openapi-companion.md`
- `docs/node-to-python-conversion-plan.md`
- `docs/node-to-python-method-mapping.md`
- `docs/error-handling-boundary-map.md`
- `docs/alpha-release-checklist.md`
