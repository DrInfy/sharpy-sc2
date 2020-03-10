from typing import Set

from sharpy.plans.acts import ActBase
from sharpy.managers import UnitRoleManager
from sc2 import UnitTypeId
from sc2.unit import Unit

from sharpy.managers.roles import UnitTask
from sharpy.knowledges import Knowledge


class PlanHallucination(ActBase):
    """Keeps track of our own hallucinated units."""
    def __init__(self):
        super().__init__()
        self.roles: UnitRoleManager = None
        self.resolved_units_tags: Set[int] = set()

        # Types that we currently use for hallucinations
        self.types: Set[UnitTypeId] = {
            UnitTypeId.COLOSSUS,
            UnitTypeId.PHOENIX,
            UnitTypeId.VOIDRAY,
            UnitTypeId.IMMORTAL,
            UnitTypeId.ARCHON,
            UnitTypeId.STALKER,
            UnitTypeId.ZEALOT,
        }

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)
        self.roles = knowledge.roles

    async def execute(self) -> bool:
        filtered_units = self.cache.own(self.types).tags_not_in(self.resolved_units_tags)

        for unit in filtered_units:  # type: Unit
            if unit.is_hallucination:
                await self.hallucination_detected(unit)

            self.resolved_units_tags.add(unit.tag)

        units = self.roles.units(UnitTask.Hallucination)
        if units.exists:
            if self.knowledge.known_enemy_units_mobile.exists:
                target = self.knowledge.known_enemy_units_mobile.center
            else:
                target = self.knowledge.enemy_main_zone.center_location

            for unit in self.roles.units(UnitTask.Hallucination):
                self.do(unit.attack(target))

        return True

    async def hallucination_detected(self, unit):
        self.roles.set_task(UnitTask.Hallucination, unit)
        self.knowledge.lost_units_manager.hallucination_tags.append(unit.tag)
        self.print(f"{unit.type_id.name} {unit.tag} detected as hallucination")

