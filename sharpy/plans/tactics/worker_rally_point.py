from typing import Optional, List
from sharpy.plans.acts import ActBase

from sharpy.managers.roles import UnitTask
from sc2 import UnitTypeId, Race, AbilityId
from sc2.unit import Unit
from sharpy.tools import IntervalFunc


class WorkerRallyPoint(ActBase):
    """Handles setting worker rally points"""
    ability: AbilityId
    func: IntervalFunc

    def __init__(self):
        super().__init__()

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        # set rally point once every 5 seconds
        self.func = IntervalFunc(self.ai, self.set_rally_point, 5)

        if self.knowledge.my_race == Race.Terran:
            self.ability = AbilityId.RALLY_COMMANDCENTER
        if self.knowledge.my_race == Race.Protoss:
            self.ability = AbilityId.RALLY_NEXUS
        if self.knowledge.my_race == Race.Zerg:
            self.ability = AbilityId.RALLY_HATCHERY_WORKERS

    def set_rally_point(self):
        for zone in self.knowledge.our_zones:
            best_mineral_field = zone.check_best_mineral_field()

            if zone.our_townhall:
                if best_mineral_field:
                    self.do(zone.our_townhall(self.ability, best_mineral_field))
                else:
                    self.do(zone.our_townhall(self.ability, zone.center_location))

    async def execute(self) -> bool:
        self.func.execute()
        return True
