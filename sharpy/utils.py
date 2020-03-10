from random import randint
from typing import List, Optional
from sc2.unit import Point2


# Tried to put this as a static method in Zone class, but because of
# circular imports or something it did not work.

def map_to_point2s_center(zones: List['Zone']) -> List[Point2]:
    """Maps list of Zone objects to list of Point2 objects."""
    locations = list(map(lambda zone: zone.center_location, zones))
    return locations

def map_to_point2s_minerals(zones: List['Zone']) -> List[Point2]:
    """Maps list of Zone objects to list of Point2 objects."""
    locations = list(map(lambda zone: (zone.center_location + zone.behind_mineral_position_center) * 0.5, zones))
    return locations

def select_build_index(knowledge: 'Knowledge', build_key: str, min_index: int, max_index) -> int:
    """
    Build selector, uses build key if it is found in settings.ini.
    Otherwise get random index
    """
    tactic: Optional[int] = None
    try:
        tactic = knowledge.get_int_setting(build_key)
    except:
        pass

    if tactic is not None and min_index <= tactic <= max_index:
        return tactic
    else:
        return randint(min_index, max_index)
