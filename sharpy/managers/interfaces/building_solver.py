from abc import abstractmethod, ABC
from typing import Optional, List, Union, Iterable, Dict

from sc2 import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from sharpy.managers.combat2 import MicroRules, MoveType


class IBuildingSolver(ABC):
    @property
    @abstractmethod
    def pylon_position(self) -> List[Point2]:
        pass

    @property
    @abstractmethod
    def building_position(self) -> List[Point2]:
        pass
