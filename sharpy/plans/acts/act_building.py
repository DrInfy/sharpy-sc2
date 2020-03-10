import math

import sc2
from sc2 import UnitTypeId, AbilityId
from sc2.position import Point2
from sc2.unit import Unit

from .act_base import ActBase




class ActBuilding(ActBase):
    """Act of starting to build new buildings up to specified count"""
    def __init__(self, unit_type: UnitTypeId, to_count: int = 1):
        assert unit_type is not None and isinstance(unit_type, UnitTypeId)
        assert to_count is not None and isinstance(to_count, int)

        self.unit_type = unit_type
        self.to_count = to_count

        super().__init__()

    async def execute(self):
        count = self.get_count(self.unit_type)

        if count >= self.to_count:
            return True  # Step is done

        unit = self.ai._game_data.units[self.unit_type.value]
        cost = self.ai._game_data.calculate_ability_cost(unit.creation_ability)

        if self.knowledge.can_afford(self.unit_type):
            await self.actually_build(self.ai, count)
        else:
            self.knowledge.reserve(cost.minerals, cost.vespene)

        return False



    async def actually_build(self, ai, count):
        location = self.get_random_build_location()
        self.knowledge.print(f'[ActBuilding] {count+1}. building of type {self.unit_type} near {location}')
        await ai.build(self.unit_type, near=location)



    def get_random_build_location(self) -> Point2:
        """Calculates building position."""
        start_point = self.knowledge.own_main_zone.center_location
        if self.ai.townhalls.exists and self.ai.structures.amount > 8:
            start_point = self.ai.townhalls.random.position

        center = self.ai.game_info.map_center

        location = start_point.towards_with_random_angle(center, 9, math.pi / 2)
        return location
