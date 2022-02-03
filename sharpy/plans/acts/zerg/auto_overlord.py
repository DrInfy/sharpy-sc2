from math import ceil

from sharpy.interfaces import IIncomeCalculator
from .zerg_unit import ZergUnit
from sc2.ids.unit_typeid import UnitTypeId


class AutoOverLord(ZergUnit):
    income_calculator: IIncomeCalculator

    def __init__(self):
        super().__init__(UnitTypeId.OVERLORD, 0)

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.income_calculator = knowledge.get_required_manager(IIncomeCalculator)

    async def execute(self):
        self.to_count = await self.overlord_count_calc()
        return await super().execute()

    async def overlord_count_calc(self) -> int:
        growth_speed = self.income_calculator.mineral_income / 50

        build_time = 18  # overlord build time
        larva = self.cache.own(UnitTypeId.LARVA).amount
        bonus = min(larva * 2, int((self.ai.minerals - 300) / 50))
        predicted_supply = min(200, self.ai.supply_used + build_time * growth_speed + bonus)
        current_overlords = self.cache.own(UnitTypeId.OVERLORD).ready.amount

        if self.ai.supply_cap == 200:
            return current_overlords

        return ceil((predicted_supply - self.ai.supply_cap) / 8) + current_overlords
