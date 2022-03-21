from abc import abstractmethod, ABC
from typing import List, Tuple, Dict

from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit


class ILostUnitsManager(ABC):
    @abstractmethod
    def calculate_own_lost_resources(self) -> Tuple[int, int]:
        """Calculates lost resources for our own bot. Returns a tuple with (unit_count, minerals, gas)."""
        pass

    @abstractmethod
    def calculate_enemy_lost_resources(self) -> Tuple[int, int]:
        """Calculates lost resources for an enemy. Returns a tuple with (unit_count, minerals, gas)."""
        pass

    @abstractmethod
    def own_lost_type(self, unit_type: UnitTypeId, real_type=True) -> int:
        pass

    @abstractmethod
    def enemy_lost_type(self, unit_type: UnitTypeId, real_type=True) -> int:
        pass

    @abstractmethod
    def get_own_enemy_lost_units(self) -> Tuple[Dict[UnitTypeId, List[Unit]], Dict[UnitTypeId, List[Unit]]]:
        """Get tuple with own and enemy lost units"""
        pass
