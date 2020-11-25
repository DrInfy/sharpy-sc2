from typing import Optional

from sc2.position import Point2
from sharpy.general.extended_ramp import ExtendedRamp
from sharpy.managers import ManagerBase
from sharpy.interfaces import IGatherPointSolver


class GatherPointSolver(ManagerBase, IGatherPointSolver):
    base_ramp: ExtendedRamp

    def __init__(self):
        super().__init__()
        self._expanding_to: Optional[Point2] = None

    @property
    def gather_point(self) -> Point2:
        return self._gather_point

    @property
    def expanding_to(self) -> Optional[Point2]:
        return self._expanding_to

    def set_expanding_to(self, target: Point2) -> None:
        self._expanding_to = target
        self._find_gather_point()  # Re check the gather point

    async def start(self, knowledge: "SkeletonKnowledge"):
        await super().start(knowledge)
        self.base_ramp = self.zone_manager.expansion_zones[0].ramp

    async def update(self):
        self._find_gather_point()

    async def post_update(self):
        pass

    def _find_gather_point(self):
        self._gather_point = self.base_ramp.top_center.towards(self.base_ramp.bottom_center, -4)
        start = 1

        for i in range(start, len(self.zone_manager.expansion_zones)):
            zone = self.zone_manager.expansion_zones[i]
            if self._expanding_to == zone.center_location:
                self._gather_point = zone.gather_point
            elif zone.is_ours:
                if len(self.zone_manager.gather_points) > i:
                    self._gather_point = self.zone_manager.expansion_zones[
                        self.zone_manager.gather_points[i]
                    ].gather_point
