from abc import abstractmethod, ABC
from typing import Union, Optional

from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit
from sc2.units import Units
from sharpy.general.extended_power import ExtendedPower


class IUnitValues(ABC):
    @property
    @abstractmethod
    def enemy_worker_type(self) -> Optional[UnitTypeId]:
        pass

    @abstractmethod
    def is_worker(self, unit: Union[Unit, UnitTypeId]):
        pass

    @abstractmethod
    def building_start_time(self, game_time: float, type_id: UnitTypeId, build_progress: float):
        """Calculates when building construction started. This can be used to eg. detect early rushes."""
        pass

    @abstractmethod
    def building_completion_time(self, game_time: float, type_id: UnitTypeId, build_progress: float):
        pass

    @abstractmethod
    def minerals(self, unit_type: UnitTypeId) -> float:
        pass

    @abstractmethod
    def gas(self, unit_type: UnitTypeId) -> float:
        pass

    @abstractmethod
    def supply(self, unit_type: UnitTypeId) -> float:
        pass

    @abstractmethod
    def defense_value(self, unit_type: UnitTypeId) -> float:
        """Deprecated, don't use with main bot any more! use power instead."""
        pass

    @abstractmethod
    def build_time(self, unit_type: UnitTypeId) -> int:
        pass

    @abstractmethod
    def power(self, unit: Unit) -> float:
        pass

    @abstractmethod
    def power_by_type(self, type_id: UnitTypeId, health_percentage: float = 1) -> float:
        pass

    @abstractmethod
    def ground_range(self, unit: Unit) -> float:
        pass

    @abstractmethod
    def air_range(self, unit: Unit) -> float:
        pass

    @abstractmethod
    def can_shoot_air(self, unit: Unit) -> bool:
        pass

    @abstractmethod
    def can_shoot_ground(self, unit: Unit) -> bool:
        pass

    @abstractmethod
    def can_assist_defense(self, unit: Unit) -> bool:
        """ Returns true when unit is an utility unit that can help defend even if it cannot attack correct targets itself."""
        pass

    @abstractmethod
    def real_range(self, unit: Unit, other: Unit) -> float:
        """Returns real range for a unit and against another unit, taking both units radius into account."""
        pass

    @abstractmethod
    def real_speed(self, unit: Unit) -> float:
        pass

    @abstractmethod
    def should_kite(self, unit_type: UnitTypeId) -> bool:
        pass

    @abstractmethod
    def is_ranged_unit(self, unit: Unit):
        pass

    @abstractmethod
    def real_type(self, unit_type: UnitTypeId):
        """Find a mapping if there is one, or use the unit_type as it is"""
        pass

    @abstractmethod
    def is_townhall(self, unit_type: Union[Unit, UnitTypeId]):
        """Returns true if the unit_type or unit_type type is a main structure, ie. Command Center, Nexus, Hatchery, or one of
        their upgraded versions."""
        pass

    @abstractmethod
    def calc_total_power(self, units: Units) -> ExtendedPower:
        """Calculates total power for the given units (either own or enemy)."""
        pass

    @abstractmethod
    def should_attack(self, unit: Unit):
        """ Determines if the unit is something that should attack. """
        pass
