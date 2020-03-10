from math import ceil

from .zerg_unit import ZergUnit
from sc2 import UnitTypeId


class AutoOverLord(ZergUnit):
    def __init__(self):
        super().__init__(UnitTypeId.OVERLORD, 0)

    async def execute(self):
        self.to_count = await self.overlord_count_calc()
        return await super().execute()

    async def overlord_count_calc(self) -> int:
        growth_speed = self.knowledge.income_calculator.mineral_income / 50

        build_time = 18  # overlord build time
        predicted_supply = min(200, self.ai.supply_used + build_time * growth_speed)
        current_overlords = self.cache.own(UnitTypeId.OVERLORD).ready.amount

        if self.ai.supply_cap == 200:
            return current_overlords

        return ceil((predicted_supply - self.ai.supply_cap) / 8) + current_overlords