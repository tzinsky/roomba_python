from roomba_python import RobotClient
from roomba_python.models import PreferencesPatch
from roomba_python.types import CleaningPasses

# Replace placeholders with your actual credentials and robot IP.
client = RobotClient(
    blid="YOUR_BLID",
    password="YOUR_ROBOT_PASSWORD",
    host="192.168.1.104",
)

client.connect()
try:
    client.clean()
    client.set_preferences(PreferencesPatch(cleaning_passes=CleaningPasses.ONE))
finally:
    client.disconnect()
