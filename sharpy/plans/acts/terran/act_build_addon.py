import math
from typing import Dict

import sc2
from sc2 import UnitTypeId
from sc2.game_info import GameInfo
from sc2.pixel_map import PixelMap
from sc2.position import Point2

from sharpy.plans.acts.act_base import ActBase
from sc2.unit import Unit


class ActBuildAddon(ActBase):
    """Act of starting to build new buildings up to specified count"""
    def __init__(self, unit_type: UnitTypeId, unit_from_type: UnitTypeId, to_count: int):
        assert unit_type is not None and isinstance(unit_type, UnitTypeId)
        assert unit_from_type is not None and isinstance(unit_from_type, UnitTypeId)
        assert to_count is not None and isinstance(to_count, int)

        self.unit_from_type = unit_from_type
        self.unit_type = unit_type
        self.to_count = to_count

        self.tried_to_build_dict: Dict[int, float] = {}

        super().__init__()

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)

    async def execute(self) -> bool:
        count = self.get_count(self.unit_type)
        if count >= self.to_count:
            return True  # Step is done

        unit = self.ai._game_data.units[self.unit_type.value]
        cost = self.ai._game_data.calculate_ability_cost(unit.creation_ability)

        if not self.knowledge.can_afford(self.unit_type):
            self.knowledge.reserve(cost.minerals, cost.vespene)

        builder: Unit
        for builder in self.cache.own(self.unit_from_type).ready.idle:
            if builder.add_on_tag == 0:

                #if self.tried_to_build_dict.get(builder.tag, 0) + 0.5 > ai.time:
                    #continue # Prevent crashes by only trying to build twice per seconds

                center: Point2 = builder.position.offset(Point2((2.5, -0.5)))

                if await self.ai.find_placement(UnitTypeId.SUPPLYDEPOT, center, 0, False):
                    self.tried_to_build_dict[builder.tag] = self.ai.time
                    self.knowledge.print(f"[AddOn] {self.unit_type} to {center}")
                    self.do(builder.build(self.unit_type))
                else:
                    self.knowledge.print("[AddOn] no space")
        return False

    def get_count(self, unit_type: UnitTypeId) -> int:
        """Calculates how many buildings there are already, including pending structures."""
        count = 0

        count += self.cache.own(unit_type).amount

        return count
