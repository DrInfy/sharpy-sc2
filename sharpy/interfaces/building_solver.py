from abc import abstractmethod, ABC
from typing import List

from sc2.position import Point2


class IBuildingSolver(ABC):
    @property
    @abstractmethod
    def pylon_position(self) -> List[Point2]:
        pass

    @property
    @abstractmethod
    def building_position(self) -> List[Point2]:
        pass
