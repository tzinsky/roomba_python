from roomba_python import RobotClient

# Replace placeholders with your actual credentials and robot IP.
client = RobotClient(
    blid="YOUR_BLID",
    password="YOUR_ROBOT_PASSWORD",
    host="192.168.1.104",
)

client.connect()
try:
    mission = client.get_basic_mission(timeout=5.0)
    print(mission.model_dump())
finally:
    client.disconnect()
