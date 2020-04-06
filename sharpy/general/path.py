from typing import Tuple, List, Optional

from sc2.position import Point2


class Path():
    path: Tuple[int, int]
    def __init__(self, path: Tuple[List[Tuple[int, int]], float], reverse: bool = False) -> None:
        self.distance: float = path[1]
        if reverse:
            self.path = path[0][::-1]
        else:
            self.path = path[0]

    def get_index(self, target_index: int) -> Optional[Point2]:
        if len(self.path) < 1:
            return None

        if len(self.path) <= target_index:
            target_index = len(self.path) - 1

        target = self.path[target_index]
        return Point2((target[0] + 0.5, target[1] + 0.5))
