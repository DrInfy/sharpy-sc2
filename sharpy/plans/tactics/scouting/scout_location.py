from typing import Callable, Optional, List

from sc2.position import Point2
from sharpy.general.zone import Zone
from sharpy.interfaces import IZoneManager
from sharpy.managers.core import PathingManager
from sharpy.plans.tactics.scouting.scout_base_action import ScoutBaseAction

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sharpy.knowledges import Knowledge


class ScoutLocation(ScoutBaseAction):
    zone_manager: IZoneManager
    pathing_manager: Optional[PathingManager]

    def __init__(
        self, func_target: Callable[["ScoutLocation"], Point2], distance_to_reach: float = 5, only_once: bool = False
    ) -> None:
        super().__init__(only_once)
        self.func_target = func_target
        self.distance_to_reach = distance_to_reach

    @property
    def expansion_zones(self) -> List[Zone]:
        return self.zone_manager.expansion_zones

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.zone_manager = knowledge.get_required_manager(IZoneManager)
        self.pathing_manager = knowledge.get_manager(PathingManager)  # some scout actions might actually require this

    async def execute(self) -> bool:
        if self.ended:
            return True
        if not self._units:
            return False
        self.current_target = self.func_target(self)

        center = self._units.center
        if self._units[0].is_flying:
            target = self.pather.find_influence_air_path(center, self.current_target)
        else:
            target = self.pather.find_influence_ground_path(center, self.current_target)

        for unit in self._units:
            unit.move(target)

        if center.distance_to(self.current_target) < self.distance_to_reach:
            if self.only_once:
                self.ended = True
            return True
        return False

    @staticmethod
    def scout_main(**kwargs) -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[-1].behind_mineral_position_center, **kwargs)

    @staticmethod
    def scout_enemy1(**kwargs) -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[-1].center_location, **kwargs)

    @staticmethod
    def scout_enemy2(**kwargs) -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[-2].center_location, **kwargs)

    @staticmethod
    def scout_enemy3(**kwargs) -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[-3].center_location, **kwargs)

    @staticmethod
    def scout_enemy4(**kwargs) -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[-4].center_location, **kwargs)

    @staticmethod
    def scout_enemy5(**kwargs) -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[-5].center_location, **kwargs)

    @staticmethod
    def scout_enemy6(**kwargs) -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[-6].center_location, **kwargs)

    @staticmethod
    def scout_enemy7(**kwargs) -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[-7].center_location, **kwargs)

    @staticmethod
    def scout_own1(**kwargs) -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[0].center_location, **kwargs)

    @staticmethod
    def scout_own2(**kwargs) -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[1].center_location, **kwargs)

    @staticmethod
    def scout_own3(**kwargs) -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[2].center_location, **kwargs)

    @staticmethod
    def scout_own4(**kwargs) -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[3].center_location, **kwargs)

    @staticmethod
    def scout_own5(**kwargs) -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[4].center_location, **kwargs)

    @staticmethod
    def scout_own6(**kwargs) -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[5].center_location, **kwargs)

    @staticmethod
    def scout_own7(**kwargs) -> ScoutBaseAction:
        return ScoutLocation(lambda k: k.expansion_zones[6].center_location, **kwargs)

    @staticmethod
    def scout_enemy_natural_ol_spot(**kwargs) -> ScoutBaseAction:
        return ScoutLocation(
            lambda k: ScoutLocation.closest_overlord_spot_to(k, k.expansion_zones[-2].center_location), **kwargs
        )

    @staticmethod
    def scout_own_natural_ol_spot(**kwargs) -> ScoutBaseAction:
        return ScoutLocation(
            lambda k: ScoutLocation.closest_overlord_spot_to(k, k.expansion_zones[1].center_location), **kwargs
        )

    @staticmethod
    def scout_center_ol_spot(**kwargs) -> ScoutBaseAction:
        return ScoutLocation(
            lambda k: ScoutLocation.closest_overlord_spot_to(k.knowledge, k.ai.game_info.map_center), **kwargs
        )

    @staticmethod
    def closest_overlord_spot_to(k: "ScoutLocation", target: Point2) -> Point2:
        if k.pathing_manager.overlord_spots:
            return target.closest(k.pathing_manager.overlord_spots)
        return target
