from typing import List, Set, Union

from sc2 import UnitTypeId
from sc2.units import Units
from sharpy.managers.roles import UnitTask
from sharpy.plans import SubActs, Step
from typing import TYPE_CHECKING

from sharpy.plans.tactics.scouting.scout_base_action import ScoutBaseAction
from sharpy.plans.tactics.scouting.scout_location import ScoutLocation

if TYPE_CHECKING:
    from sharpy.knowledges import Knowledge


class Scout(SubActs):
    units: Units

    def __init__(
        self, unit_types: Union[UnitTypeId, Set[UnitTypeId]], unit_count: int, *args: Union[Step, ScoutBaseAction]
    ):
        """
        Scout act for all races, loops the given scout actions
        @param unit_types: Types of units accepted as scouts
        @param unit_count: Units required to be used in scouting, scouting will only start after all are available
        @param args: Scout actions, cen be to scout a certain location, or to move around in certain way. Defaults to scouting enemy main
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

        if self.find_units():
            return True

        if self.units:
            self.roles.set_tasks(UnitTask.Scouting, self.units)
            await self.micro_units()  # Ignore if the scouting has finished
        return True

    async def micro_units(self) -> bool:
        """
        Micros units
        @return: True when finished
        """
        count = len(self.orders)
        self.index = self.index % count

        for looped in range(0, count + 1):
            if looped == count:
                self.ended = True
                return True
            # noinspection PyTypeChecker
            action: ScoutBaseAction = self.orders[self.index]
            action.set_scouts(self.units)
            result = await action.execute()
            if not result:
                # Not finished
                return False

            self.index = (self.index + 1) % count
        return False

    def find_units(self) -> bool:
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
