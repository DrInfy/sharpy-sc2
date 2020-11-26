from abc import abstractmethod, ABC
from typing import List, Optional

from sc2.position import Point2


class IBuildingSolver(ABC):
    @property
    @abstractmethod
    def zealot(self) -> Optional[Point2]:
        pass

    @property
    @abstractmethod
    def wall2x2(self) -> List[Point2]:
        pass

    @property
    @abstractmethod
    def wall3x3(self) -> List[Point2]:
        pass

    @property
    @abstractmethod
    def not_wall2x2(self) -> Optional[Point2]:
        pass

    @property
    @abstractmethod
    def not_wall3x3(self) -> List[Point2]:
        pass

    @property
    @abstractmethod
    def buildings2x2(self) -> List[Point2]:
        pass

    @property
    @abstractmethod
    def buildings3x3(self) -> List[Point2]:
        pass
