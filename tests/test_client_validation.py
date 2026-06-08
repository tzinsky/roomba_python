import pytest

from roomba_python.client import RobotClient
from roomba_python.errors import ValidationError
from roomba_python.models import PreferencesPatch


def test_set_preferences_empty_patch_raises() -> None:
    client = RobotClient("blid", "password", "192.168.1.2")
    with pytest.raises(ValidationError):
        client.set_preferences(PreferencesPatch())
