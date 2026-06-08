from roomba_python.client import _map_preferences_patch
from roomba_python.models import PreferencesPatch
from roomba_python.types import CarpetBoostMode, CleaningPasses


def test_map_preferences_patch_full() -> None:
    patch = PreferencesPatch(
        carpet_boost_mode=CarpetBoostMode.PERFORMANCE,
        edge_clean_enabled=True,
        cleaning_passes=CleaningPasses.TWO,
        always_finish=False,
    )

    mapped = _map_preferences_patch(patch)

    assert mapped["carpetBoost"] is False
    assert mapped["vacHigh"] is True
    assert mapped["openOnly"] is False
    assert mapped["noAutoPasses"] is True
    assert mapped["twoPass"] is True
    assert mapped["binPause"] is True
