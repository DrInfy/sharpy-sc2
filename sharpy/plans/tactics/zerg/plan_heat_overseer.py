from typing import Optional, Tuple

from sharpy.plans.acts import ActBase
from sharpy.mapping.heat_map import HeatMap
from sharpy.managers.roles import UnitTask
from sharpy.knowledges import Knowledge
from sc2 import UnitTypeId
from sc2.position import Point2


class PlanHeatOverseer(ActBase):
    def __init__(self):
        super().__init__()
        self.overseer_tag = None
        self.activated = False

        self.last_seen = 0

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)
        self.heat_map: HeatMap = knowledge.heat_map
        self.roles = self.knowledge.roles
        self.gather_point = self.knowledge.expansion_zones[0].center_location

    async def execute(self) -> bool:
        stealth_hotspot: Optional[Tuple[Point2, float]] = self.heat_map.get_stealth_hotspot()

        if stealth_hotspot is not None:
            self.stealth_hotspot = stealth_hotspot[0]
            self.activated = True
            self.last_seen = self.ai.time

        if not self.activated:
            return True
        elif self.last_seen + 30 < self.ai.time:
            self.activated = False
            if self.overseer_tag is not None:
                self.roles.clear_task(self.overseer_tag)
                self.overseer_tag = None
            return True

        if self.overseer_tag is None:
            idle = self.roles.all_from_task(UnitTask.Idle)
            overseers = idle(UnitTypeId.OVERSEER)
            if overseers.exists:
                overseer = overseers.first
                self.overseer_tag = overseer.tag
                self.roles.set_task(UnitTask.Reserved, overseer)
                await self.assault_hot_spot(overseer)
        else:
            overseer = self.cache.by_tag(self.overseer_tag)
            if overseer is None:
                self.overseer_tag = None
            else:
                await self.assault_hot_spot(overseer)

        return True  # never block

    async def assault_hot_spot(self, observer):
        position = self.stealth_hotspot or self.gather_point
        self.combat.add_unit(observer)
        self.combat.execute(position)
