from abc import abstractmethod, ABC
from typing import List, Tuple, Dict, Optional

from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from sharpy.general.zone import Zone


class IZoneManager(ABC):
    @property
    @abstractmethod
    def expansion_zones(self) -> List[Zone]:
        pass

    @property
    @abstractmethod
    def our_zones(self) -> List[Zone]:
        pass

    @property
    @abstractmethod
    def enemy_zones(self) -> List[Zone]:
        pass

    @property
    @abstractmethod
    def unscouted_zones(self) -> List[Zone]:
        """Returns a list of all zones that have not been scouted."""
        pass

    @property
    @abstractmethod
    def known_enemy_structures_at_start_height(self) -> Units:
        """Returns known enemy structures that are at the height of start locations."""
        pass

    @property
    @abstractmethod
    def enemy_start_location_found(self) -> bool:
        """Returns true if enemy start location has (probably) been found."""
        pass

    @property
    @abstractmethod
    def enemy_start_location(self) -> Point2:
        """Returns the enemy start location, or the most likely one, if one hasn't been found."""
        pass

    @property
    @abstractmethod
    def enemy_main_zone(self) -> Zone:
        """ Returns enemy main / start zone."""
        pass

    @property
    @abstractmethod
    def enemy_expansion_zones(self) -> List[Zone]:
        """Returns enemy expansions zones, sorted by closest to the enemy main zone first."""
        pass

    @property
    @abstractmethod
    def all_zones(self) -> List[Zone]:
        """Returns a list of all zones."""
        pass

    @property
    @abstractmethod
    def enemy_start_zones(self) -> List[Zone]:
        """Returns all zones that are possible enemy start locations."""
        pass

    @property
    @abstractmethod
    def scouted_enemy_start_zones(self) -> List[Zone]:
        """returns possible enemy start zones that have been scouted."""
        pass

    @property
    @abstractmethod
    def unscouted_enemy_start_zones(self) -> List[Zone]:
        """Returns possible enemy start zones that have not been scouted. Similar to unscouted_enemy_start_locations."""
        pass

    @property
    @abstractmethod
    def our_zones_with_minerals(self) -> List[Zone]:
        """Returns all of our zones that have minerals."""
        pass

    @property
    @abstractmethod
    def own_main_zone(self) -> Zone:
        """Returns our own main zone. If we have lost our base at start location, it will be the
        next safe expansion."""
        pass

    @abstractmethod
    def zone_for_unit(self, building: Unit) -> Optional[Zone]:
        pass
