from abc import abstractmethod, ABC
from typing import Optional

from sc2.position import Point2


class IGatherPointSolver(ABC):
    @property
    @abstractmethod
    def gather_point(self) -> Point2:
        pass

    @abstractmethod
    def set_gather_point(self, point: Point2):
        """
        Setting gather point manually should remember it for the current frame.
        @param point: new gather point
        """
        pass

    @property
    @abstractmethod
    def expanding_to(self) -> Optional[Point2]:
        """
        This is the location the current intent is to expand into.
        Any available army should go there and clear the area for the worker.
        @return: Nexus / Command center / Hatchery position
        """
        pass

    @abstractmethod
    def set_expanding_to(self, target: Point2) -> None:
        """
        This is used to indicate the intent to expand to a location.
        Any available army should go there and clear the area for the worker.
        @param target: Nexus / Command center / Hatchery position
        """
        pass
