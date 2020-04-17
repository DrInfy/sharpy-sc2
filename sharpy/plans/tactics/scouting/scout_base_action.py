from typing import List

from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from sharpy.plans.acts import ActBase


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
