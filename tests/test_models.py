from roomba_python.models import PreferencesPatch
from roomba_python.types import CarpetBoostMode, CleaningPasses


def test_preferences_patch_empty_state() -> None:
    patch = PreferencesPatch()
    assert patch.is_empty() is True


def test_preferences_patch_non_empty_state() -> None:
    patch = PreferencesPatch(
        carpet_boost_mode=CarpetBoostMode.ECO,
        cleaning_passes=CleaningPasses.TWO,
    )
    assert patch.is_empty() is False
