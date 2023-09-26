from typing import Optional

from sc2.position import Point2
from sharpy.general.extended_ramp import ExtendedRamp
from .manager_base import ManagerBase
from sharpy.interfaces import IGatherPointSolver


class GatherPointSolver(ManagerBase, IGatherPointSolver):
    def __init__(self):
        super().__init__()
        self._expanding_to: Optional[Point2] = None
        self._gather_point = Point2((0, 0))
        self._gather_point_set = False
        self._set_expand_gather = False
        self._inital_gather_point = Point2((0, 0))

    @property
    def gather_point(self) -> Point2:
        return self._gather_point

    def set_gather_point(self, point: Point2):
        self._gather_point = point
        self._gather_point_set = True

    @property
    def expanding_to(self) -> Optional[Point2]:
        return self._expanding_to

    def set_expanding_to(self, target: Point2) -> None:
        self._expanding_to = target
        self._set_expand_gather = True
        self._find_gather_point()  # Re check the gather point

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        if self.zone_manager.expansion_zones:
            base_ramp = self.zone_manager.expansion_zones[0].ramp
            if base_ramp:
                self._inital_gather_point = base_ramp.top_center.towards(base_ramp.bottom_center, -4)
            else:
                self._inital_gather_point = self.zone_manager.expansion_zones[0].center_location.towards(
                    self.zone_manager.enemy_start_location, 8
                )
        else:
            self._inital_gather_point = self.ai.start_location

    async def update(self):
        if not self._gather_point_set:
            self._find_gather_point()
        self._gather_point_set = False
        self._set_expand_gather = False

    async def post_update(self):
        pass

    def _find_gather_point(self):
        self._gather_point = self._inital_gather_point
        start = 1

        for i in range(start, len(self.zone_manager.expansion_zones)):
            zone = self.zone_manager.expansion_zones[i]
            if self._set_expand_gather and self._expanding_to == zone.center_location:
                self._gather_point = zone.gather_point
            elif zone.is_ours:
                if len(self.zone_manager.gather_points) > i:
                    self._gather_point = self.zone_manager.expansion_zones[
                        self.zone_manager.gather_points[i]
                    ].gather_point
