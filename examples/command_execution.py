from roomba_python import RobotClient

# Replace placeholders with your actual credentials and robot IP.
client = RobotClient(
    blid="YOUR_BLID",
    password="YOUR_ROBOT_PASSWORD",
    host="192.168.1.104",
)

client.connect()
try:
    # Choose commands appropriate for your robot's current state.
    client.clean()
    client.pause()
    client.resume()
    client.dock()
finally:
    client.disconnect()
