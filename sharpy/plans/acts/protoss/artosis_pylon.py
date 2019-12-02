from typing import Optional

from sharpy.managers.grids import ZoneArea
from sharpy.plans.acts.grid_building import GridBuilding
from sharpy.constants import Constants
from sc2 import UnitTypeId
from sc2.position import Point2


class ArtosisPylon(GridBuilding):
    def __init__(self, to_count: int, iterator: Optional[int] = None, priority: bool = False):
        super().__init__(UnitTypeId.PYLON, to_count, iterator, priority, False)

    def position_protoss(self, count) -> Optional[Point2]:
        best_position = None
        buildings = self.knowledge.ai.structures
        best_count = 0

        for point in self.building_solver.pylon_position:
            if buildings.closer_than(1, point):
                continue

            count = 0
            for position in self.building_solver.building_position:
                if self.building_solver.grid[position].ZoneIndex != ZoneArea.OwnMainZone:
                    # Not in main zone
                    continue

                if point.distance_to_point2(position) < Constants.PYLON_POWERED_DISTANCE:
                    count += 1

            if count > best_count:
                best_count = count
                best_position = point

        return best_position

