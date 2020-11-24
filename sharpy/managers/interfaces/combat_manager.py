from abc import abstractmethod, ABC
from typing import Optional, List, Union, Iterable, Dict

from sc2 import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from sharpy.managers.combat2 import MicroRules, MoveType


class ICombatManager(ABC):
    @property
    @abstractmethod
    def tags(self) -> List[int]:
        pass

    @abstractmethod
    def add_unit(self, unit: Unit):
        pass

    @abstractmethod
    def add_units(self, units: Units):
        pass

    @abstractmethod
    def execute(self, target: Point2, move_type=MoveType.Assault, rules: Optional[MicroRules] = None):
        pass
