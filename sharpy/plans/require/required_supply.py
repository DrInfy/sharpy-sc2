import enum

from sharpy.plans.require.require_base import RequireBase


class SupplyType(enum.Enum):
    All = 0
    Combat = 1
    Workers = 2


class RequiredSupply(RequireBase):
    def __init__(self, supply_amount: int, supply_type: SupplyType = SupplyType.All):
        assert supply_amount is not None and isinstance(supply_amount, int)
        super().__init__()
        self.supply_type = supply_type
        self.supply_amount = supply_amount

    def check(self) -> bool:
        if self.supply_type == SupplyType.All:
            return self.ai.supply_used >= self.supply_amount
        if self.supply_type == SupplyType.Combat:
            return self.ai.supply_used - self.ai.supply_workers >= self.supply_amount

        return self.ai.supply_workers >= self.supply_amount
