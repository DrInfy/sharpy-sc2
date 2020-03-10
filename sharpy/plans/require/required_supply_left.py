import sc2

from sharpy.plans.require.require_base import RequireBase


class RequiredSupplyLeft(RequireBase):
    def __init__(self, supply_amount: int):
        assert supply_amount is not None and isinstance(supply_amount, int)
        super().__init__()

        # if less than supply amount of free supply left
        self.supplyAmount  = supply_amount

    def check(self) -> bool:
        if self.ai.supply_left <= self.supplyAmount and self.ai.supply_cap < 200:
            return True
        return False
