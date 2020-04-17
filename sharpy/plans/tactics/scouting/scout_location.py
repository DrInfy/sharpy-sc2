from typing import Callable

from sc2.position import Point2
from sharpy.plans.tactics.scouting.scout_base_action import ScoutBaseAction


class ScoutLocation(ScoutBaseAction):
    def __init__(
        self, func_target: Callable[["Knowledge"], Point2], distance_to_reach: float = 5, only_once: bool = False
    ) -> None:
        super().__init__(only_once)
        self.func_target = func_target
        self.distance_to_reach = distance_to_reach

    async def execute(self) -> bool:
        if self.ended:
            return True
        if not self._units:
            return False
        self.current_target = self.func_target(self.knowledge)

        center = self._units.center
        if self._units[0].is_flying:
            target = self.pather.find_influence_air_path(center, self.current_target)
        else:
            target = self.pather.find_influence_ground_path(center, self.current_target)

        for unit in self._units:
            self.do(unit.move(target))

        if center.distance_to(self.current_target) < self.distance_to_reach:
            if self.only_once:
                self.ended = True
            return True
        return False

    @staticmethod
    def scout_main() -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[-1].behind_mineral_position_center)

    @staticmethod
    def scout_enemy1() -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[-1].center_location)

    @staticmethod
    def scout_enemy2() -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[-2].center_location)

    @staticmethod
    def scout_enemy3() -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[-3].center_location)

    @staticmethod
    def scout_enemy4() -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[-4].center_location)

    @staticmethod
    def scout_enemy5() -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[-5].center_location)

    @staticmethod
    def scout_enemy6() -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[-6].center_location)

    @staticmethod
    def scout_enemy7() -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[-7].center_location)

    @staticmethod
    def scout_own1() -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[0].center_location)

    @staticmethod
    def scout_own2() -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[1].center_location)

    @staticmethod
    def scout_own3() -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[2].center_location)

    @staticmethod
    def scout_own4() -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[3].center_location)

    @staticmethod
    def scout_own5() -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[4].center_location)

    @staticmethod
    def scout_own6() -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[5].center_location)

    @staticmethod
    def scout_own7() -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[6].center_location)
