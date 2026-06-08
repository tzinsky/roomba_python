from roomba_python import RobotClient

# Replace placeholders with your actual credentials and robot IP.
client = RobotClient(
    blid="YOUR_BLID",
    password="YOUR_ROBOT_PASSWORD",
    host="192.168.1.104",
)

print(f"connected before connect(): {client.is_connected()}")
client.connect()
print(f"connected after connect(): {client.is_connected()}")
client.disconnect()
print(f"connected after disconnect(): {client.is_connected()}")
