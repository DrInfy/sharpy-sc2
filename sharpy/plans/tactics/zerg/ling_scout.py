from typing import List, Optional

from sc2.position import Point2
from sc2.units import Units
from sharpy.managers.roles import UnitTask
from sharpy.plans.acts import ActBase
from sc2 import UnitTypeId, AbilityId
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit

class LingScoutMain(ActBase):
    def __init__(self):
        self.scout_tags: List[int] = []
        super().__init__()

    async def start(self, knowledge: 'Knowledge'):
        return await super().start(knowledge)

    async def execute(self) -> bool:
        lings = self.cache.own(UnitTypeId.ZERGLING)
        scouts = self.roles.all_from_task(UnitTask.Scouting)
        scout_lings = lings.tags_in(scouts.tags)
        non_scout_lings = lings.tags_not_in(scouts.tags)

        if len(self.scout_tags) > 0 and not len(scout_lings) == 0:
            return True

        if len(self.scout_tags) == 0 and non_scout_lings.amount > 2:
            scout_lings = Units(non_scout_lings[0:1], self.ai)
            self.scout_tags = scout_lings.tags

        for scout in scout_lings:
            self.knowledge.roles.set_task(UnitTask.Scouting, scout)
            target = self.knowledge.expansion_zones[-1].behind_mineral_position_center

            self.do(scout.move(target))

        return True
