from abc import abstractmethod, ABC
from sc2.position import Point2


class IGatherPointSolver(ABC):
    @property
    @abstractmethod
    def gather_point(self) -> Point2:
        pass
