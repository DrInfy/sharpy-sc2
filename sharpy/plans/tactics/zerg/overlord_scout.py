from typing import List, Optional

from sharpy.managers.roles import UnitTask
from sharpy.plans.acts import ActBase
from sc2 import UnitTypeId, AbilityId
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit


class OverlordScout(ActBase):
    def __init__(self):
        self.first_scout: Optional[int] = None
        super().__init__()

    async def start(self, knowledge: 'Knowledge'):
        return await super().start(knowledge)

    async def execute(self) -> bool:
        overlords = self.cache.own(UnitTypeId.OVERLORD)
        if not self.first_scout:
            if overlords:
                self.first_scout = overlords.first.tag

        if self.first_scout:
            first = self.cache.by_tag(self.first_scout)
            if first:
                self.knowledge.roles.set_task(UnitTask.Scouting, first)
                # TODO: Make it into a more likely proxy location
                target = self.knowledge.expansion_zones[2].center_location
                if first.distance_to(target) > 5:
                    self.do(first.move(target))

        return True
