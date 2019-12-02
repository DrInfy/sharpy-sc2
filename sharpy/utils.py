from typing import List, Optional

from sc2.game_info import Ramp
from sc2.unit import Point2


# Tried to put this as a static method in Zone class, but because of
# circular imports or something it did not work.
from sharpy.general.extended_ramp import ExtendedRamp


def map_to_point2s_center(zones: List['Zone']) -> List[Point2]:
    """Maps list of Zone objects to list of Point2 objects."""
    locations = list(map(lambda zone: zone.center_location, zones))
    return locations

def map_to_point2s_minerals(zones: List['Zone']) -> List[Point2]:
    """Maps list of Zone objects to list of Point2 objects."""
    locations = list(map(lambda zone: (zone.center_location + zone.behind_mineral_position_center) * 0.5, zones))
    return locations
