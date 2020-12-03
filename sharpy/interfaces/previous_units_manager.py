from abc import ABC, abstractmethod
from typing import Optional

from sc2.position import Point2
from sc2.unit import Unit


class IPreviousUnitsManager(ABC):
    @abstractmethod
    def last_unit(self, tag: int) -> Optional[Unit]:
        """
        Return unit matching the tag from previous frame, if one is found.
        """
        pass

    @abstractmethod
    def last_position(self, unit: Unit) -> Point2:
        """
        Return unit position in last frame, or current if unit was just created.
        """
        pass
