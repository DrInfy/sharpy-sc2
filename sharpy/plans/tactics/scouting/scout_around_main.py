from typing import Callable, List

from sc2.position import Point2
from sharpy.plans.tactics.scouting.scout_base_action import ScoutBaseAction

from typing import TYPE_CHECKING

from sharpy.sc2math import points_on_circumference_sorted

if TYPE_CHECKING:
    from sharpy.knowledges import Knowledge


class ScoutAroundMain(ScoutBaseAction):
    scout_locations: List[Point2]

    def __init__(self, distance_to_reach: float = 5, only_once: bool = False) -> None:
        super().__init__(only_once)
        self.distance_to_reach = distance_to_reach
        self.main_target = Point2((0, 0))
        self.scout_locations = []

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.main_target = self.knowledge.enemy_expansion_zones[0].center_location

    async def execute(self) -> bool:
        if self.ended:
            return True
        if not self._units:
            return False

        center = self._units.center

        if center.distance_to(self.main_target) < 15 and not self.scout_locations:
            self.scout_locations = points_on_circumference_sorted(self.main_target, center, 10, 30)

        if self.scout_locations:
            self.current_target = self.scout_locations[0]
        else:
            self.current_target = self.main_target

        if self._units[0].is_flying:
            target = self.pather.find_influence_air_path(center, self.current_target)
        else:
            target = self.pather.find_influence_ground_path(center, self.current_target)

        for unit in self._units:
            self.do(unit.move(target))

        if center.distance_to(self.current_target) < self.distance_to_reach:
            if self.scout_locations:
                self.scout_locations.remove(self.current_target)
                if not self.scout_locations:
                    if self.only_once:
                        self.ended = True
                    return True
        return False
