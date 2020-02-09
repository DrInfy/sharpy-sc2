from typing import List, Optional

from sc2.position import Point2
from sharpy.managers.roles import UnitTask
from sharpy.plans.acts import ActBase
from sc2 import UnitTypeId, AbilityId
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit


class OverlordScout(ActBase):
    def __init__(self):
        self.first_scout: Optional[int] = None
        self.second_scout: Optional[int] = None
        super().__init__()

    async def start(self, knowledge: 'Knowledge'):
        return await super().start(knowledge)

    async def execute(self) -> bool:
        overlords = self.cache.own(UnitTypeId.OVERLORD)
        scouts = self.roles.all_from_task(UnitTask.Scouting)
        overlords = overlords.tags_not_in(scouts.tags)

        if not self.first_scout:
            if overlords:
                self.first_scout = overlords.first.tag
        elif not self.second_scout:
            if overlords:
                self.second_scout = overlords.first.tag

        if self.first_scout:
            first = self.cache.by_tag(self.first_scout)
            if first:
                self.knowledge.roles.set_task(UnitTask.Scouting, first)
                # TODO: Make it into a more likely proxy location
                target = self.knowledge.expansion_zones[2].center_location
                final_target: Point2 = self.knowledge.expansion_zones[-2].center_location
                final_target = final_target.towards(self.ai.start_location, 9)

                if self.knowledge.iteration == 0:  # first.distance_to(target) > 5:
                    self.do(first.move(target))
                    self.do(first.move(final_target, queue=True))
        if self.second_scout:
            second = self.cache.by_tag(self.first_scout)
            if second:
                final_target: Point2 = self.knowledge.expansion_zones[1].center_location
                if second.is_idle and second.distance_to(final_target) > 10:
                    self.do(second.move(final_target))

        return True
