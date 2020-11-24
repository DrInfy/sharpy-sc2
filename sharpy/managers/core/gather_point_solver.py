from sc2.position import Point2
from sharpy.general.extended_ramp import ExtendedRamp
from sharpy.managers import ManagerBase
from sharpy.managers.interfaces.gather_point_solver import IGatherPointSolver


class GatherPointSolver(ManagerBase, IGatherPointSolver):
    base_ramp: ExtendedRamp

    @property
    def gather_point(self) -> Point2:
        return self._gather_point

    def __init__(self):
        super().__init__()

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
            if zone.expanding_to:
                self._gather_point = zone.gather_point
            elif zone.is_ours:
                if len(self.zone_manager.gather_points) > i:
                    self._gather_point = self.zone_manager.expansion_zones[
                        self.zone_manager.gather_points[i]
                    ].gather_point
