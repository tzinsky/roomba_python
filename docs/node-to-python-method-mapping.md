# Node.js to Python Method Mapping (Reduced Scope)

This document maps commonly used dorita980 Node.js methods to the reduced-scope Python API in `roomba_python`.

## Direct Method Mapping

| Node.js (dorita980) | Python (roomba_python) | Notes |
| --- | --- | --- |
| `new dorita980.Local(blid, password, ip)` | `RobotClient(blid, password, host)` | Constructor args are equivalent for reduced local use. |
| `myRobot.on('connect', cb)` | `client.connect()` | Python uses direct method call instead of event for connect lifecycle. |
| `myRobot.end()` | `client.disconnect()` | Closes active MQTT/TLS session. |
| `myRobot.clean()` | `client.clean()` | Same command intent. |
| `myRobot.pause()` | `client.pause()` | Same command intent. |
| `myRobot.resume()` | `client.resume()` | Same command intent. |
| `myRobot.dock()` | `client.dock()` | Same command intent. |
| `myRobot.stop()` | `client.stop()` | Same command intent. |
| `myRobot.getRobotState(fields)` | `client.get_state(fields)` | Waits for required fields when provided. |
| `myRobot.getMission()` | `client.get_mission()` | Returns mission snapshot, includes pose when available. |
| `myRobot.getBasicMission()` | `client.get_basic_mission()` | Mission snapshot without requiring pose. |
| `myRobot.setPreferences(patch)` | `client.set_preferences(patch)` | Python uses typed `PreferencesPatch`. |
| `dorita980.getRobotIP(cb)` / `dorita980.discovery(cb)` | `discover_robots()` | Returns typed list of discovered robots. |
| `dorita980.getRobotPublicInfo(ip, cb)` | `get_robot_public_info(ip)` | Returns typed robot discovery details. |

## API Surface Differences

- Python uses snake_case names and typed models for inputs and outputs.
- Python command calls return `CommandResult` models instead of raw response dicts.
- Discovery helpers are synchronous function calls returning typed objects.
- Connection state is accessed with `client.is_connected()`.

## Unsupported or Changed Behavior in Reduced Scope

- Cloud API methods are out of scope.
- Full legacy v1 parity is out of scope.
- Low-level raw publish/subscribe APIs are not public in the reduced API.
- Some advanced preference and firmware-specific controls from Node.js are not exposed.

## Example Conversion

Node.js:

```javascript
const dorita980 = require('dorita980');
const robot = new dorita980.Local('BLID', 'PASSWORD', '192.168.1.104');
robot.on('connect', async () => {
  await robot.clean();
  robot.end();
});
```

Python:

```python
from roomba_python import RobotClient

client = RobotClient(blid='BLID', password='PASSWORD', host='192.168.1.104')
client.connect()
try:
    client.clean()
finally:
    client.disconnect()
```
