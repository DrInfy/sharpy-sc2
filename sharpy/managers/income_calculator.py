from sc2 import UnitTypeId

from sharpy.managers.manager_base import ManagerBase
from sc2.unit import Unit

MINERAL_MINE_RATE = 1  # this isn't needed in calculations
GAS_MINE_RATE = 0.9433962264

class IncomeCalculator(ManagerBase):
    def __init__(self):
        super().__init__()
        self._mineral_income = 0
        self._gas_income = 0

    @property
    def mineral_income(self):
        return self._mineral_income

    @property
    def gas_income(self):
        return self._gas_income

    async def update(self):
        self._mineral_income = self.mineral_rate_calc()
        self._gas_income = self.vespene_rate_calc()

        # TODO: Calculate enemy income and minerals harvested here

    def mineral_rate_calc(self) -> float:
        rate = 0
        nexus: Unit
        for nexus in self.ai.townhalls:
            rate += min(nexus.assigned_harvesters, nexus.ideal_harvesters)
            rate += max(nexus.assigned_harvesters - nexus.ideal_harvesters, 0) * 0.5 # half power mining?
        # With two workers per mineral patch, a large node with 1800 minerals will exhaust after 15 minutes
        # multiplier = 1800.0 / 60 / 15 / 2 => 1
        return rate

    def vespene_rate_calc(self) -> float:
        rate = 0
        vespene_miner: Unit
        for vespene_miner in self.knowledge.unit_cache.own(self.unit_values.gas_miners):
            rate += min(vespene_miner.assigned_harvesters, vespene_miner.ideal_harvesters)
        # A standard vespene geyser contains 2250 gas and will exhaust after 13.25 minutes of saturated extraction.
        # multiplier = 2250 / 60 / 13.25 / 3 => 0.94339622641509433962264150943396
        return rate * GAS_MINE_RATE

    async def post_update(self):
        pass

