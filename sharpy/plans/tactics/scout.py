from typing import List, Callable, Set, Union

from sc2 import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from sharpy.managers.roles import UnitTask
from sharpy.plans import SubActs
from sharpy.plans.acts import ActBase
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sharpy.knowledges import Knowledge


class ScoutBaseAction(ActBase):
    _units: Units

    def __init__(self, only_once: bool) -> None:
        super().__init__()
        self.current_target = Point2((0, 0))
        self.ended = False
        self.only_once = only_once

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self._units = Units([], self.ai)

    def set_scouts(self, scouts: List[Unit]):
        self._units.clear()
        self._units.extend(scouts)


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


class Scout(SubActs):
    units: Units

    def __init__(self, unit_types: Union[UnitTypeId, Set[UnitTypeId]], unit_count: int, *args: ScoutBaseAction):
        """
        Scout act for all races, loops the given scout actions
        @param unit_types: Types of units accepted as scouts
        @param unit_count: Units required to be used in scouting, scouting will only start after all are available
        @param args: Scout actions, cen be to scout a certain location, or to move around in certain way
        """
        if isinstance(unit_types, UnitTypeId):
            self.unit_types = set()
            self.unit_types.add(unit_types)
        else:
            self.unit_types = unit_types
        self.unit_count = unit_count

        if len(args) > 0:
            super().__init__(*args)
        else:
            super().__init__(ScoutLocation.scout_main())

        self.scout_tags: List[int] = []
        self.started = False
        self.ended = False
        self.index = 0

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.units = Units([], self.ai)

    async def execute(self) -> bool:
        if self.ended:
            return True

        self.units.clear()

        if not self.started:
            if UnitTypeId.OVERLORD in self.unit_types:
                free_units = self.roles.get_types_from(
                    self.unit_types, UnitTask.Idle, UnitTask.Moving, UnitTask.Gathering, UnitTask.Reserved
                )
            else:
                free_units = self.roles.get_types_from(
                    self.unit_types, UnitTask.Idle, UnitTask.Moving, UnitTask.Gathering
                )
            if len(free_units) >= self.unit_count:
                # TODO: Better selection?
                new_scouts = free_units.random_group_of(self.unit_count)
                self.units.extend(new_scouts)
                self.scout_tags = new_scouts.tags

                self.started = True
        else:
            scouts = self.roles.get_types_from(self.unit_types, UnitTask.Scouting)
            self.units.extend(scouts.tags_in(self.scout_tags))
            if not self.units:
                # Scouts are dead, end the scout act
                self.ended = True
                return True

        if self.units:
            self.roles.set_tasks(UnitTask.Scouting, self.units)
            count = len(self.orders)
            self.index = self.index % count

            for looped in range(0, count):
                if looped == count:
                    self.ended = True
                    return True
                # noinspection PyTypeChecker
                action: ScoutBaseAction = self.orders[self.index]
                action.set_scouts(self.units)
                result = await action.execute()
                if not result:
                    # Not finished
                    return True

                self.index = (self.index + 1) % count
        return True
