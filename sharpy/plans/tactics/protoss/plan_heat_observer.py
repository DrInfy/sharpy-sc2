from typing import Optional, Tuple

from sharpy.managers.combat2 import MoveType
from sharpy.plans.acts import ActBase
from sharpy.mapping.heat_map import HeatMap
from sharpy.managers.roles import UnitTask
from sharpy.knowledges import Knowledge
from sc2 import UnitTypeId
from sc2.position import Point2


class PlanHeatObserver(ActBase):
    def __init__(self):
        super().__init__()
        self.observer_tag = None
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
            if self.observer_tag is not None:
                self.roles.clear_task(self.observer_tag)
                self.observer_tag = None
            return True

        if self.observer_tag is None:
            idle = self.roles.all_from_task(UnitTask.Idle)
            observers = idle(UnitTypeId.OBSERVER)
            if observers.exists:
                observer = observers.first
                self.observer_tag = observer.tag
                self.roles.set_task(UnitTask.Reserved, observer)
                await self.assault_hot_spot(observer)
        else:
            observer = self.cache.by_tag(self.observer_tag)
            if observer is None:
                self.observer_tag = None
            else:
                await self.assault_hot_spot(observer)

        return True  # never block

    async def assault_hot_spot(self, observer):
        position = self.stealth_hotspot or self.gather_point
        self.combat.add_unit(observer)
        self.combat.execute(position)
