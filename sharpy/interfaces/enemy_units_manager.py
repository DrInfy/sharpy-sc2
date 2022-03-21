from abc import abstractmethod, ABC
from typing import List, KeysView

from sharpy.unit_count import UnitCount
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit

from sharpy.general.extended_power import ExtendedPower


class IEnemyUnitsManager(ABC):
    """Keeps track of enemy units and structures.

        Note that the class has many limitations, it does not account that
        * banelings are created by sacrificing zerglings
        * an archon is created by sacrificing two templars (dark templar or high templar).
        * orbital commands are transformed from command centers.
        * warp gates are transformed from gateways.
        *
        """

    @property
    @abstractmethod
    def unit_types(self) -> KeysView[UnitTypeId]:
        """Returns all unit types that we have seen the enemy to use."""
        pass

    @property
    @abstractmethod
    def enemy_worker_count(self) -> int:
        """Returns the amount of workers we know the enemy has"""
        pass

    @property
    @abstractmethod
    def enemy_composition(self) -> List[UnitCount]:
        pass

    @property
    @abstractmethod
    def enemy_total_power(self) -> ExtendedPower:
        pass

    @property
    @abstractmethod
    def enemy_cloak_trigger(self):
        pass

    def unit_count(self, unit_type: UnitTypeId) -> int:
        """Returns how many units enemy currently has of that unit type."""
        pass

    @abstractmethod
    def danger_value(self, danger_for_unit: Unit, position: Point2) -> float:
        pass
