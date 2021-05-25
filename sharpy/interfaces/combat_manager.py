from abc import abstractmethod, ABC
from typing import Optional, List, TYPE_CHECKING

from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

if TYPE_CHECKING:
    from sharpy.combat import MicroRules

import enum


class MoveType(enum.IntEnum):
    # Look for enemies, even if they are further away.
    SearchAndDestroy = 0
    # Same as attack move
    Assault = 1
    # When attacked from sides, fight back while moving
    Push = 2
    # Shoot while retreating
    DefensiveRetreat = 3
    # Use everything in arsenal to escape the situation
    PanicRetreat = 4
    # Don't fight with buildings and skip enemy army units if possible
    Harass = 5
    # Attempt to regroup with other units.
    ReGroup = 6


retreat_move_types = {MoveType.DefensiveRetreat, MoveType.PanicRetreat}
retreat_or_push_move_types = retreat_move_types | {MoveType.Push}


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
    def execute(self, target: Point2, move_type=MoveType.Assault, rules: Optional["MicroRules"] = None):
        pass
