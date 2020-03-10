import sc2
from sc2 import UnitTypeId

from sharpy.plans.require.require_base import RequireBase


class RequiredLessUnitExists(RequireBase):
    def __init__(self, name: UnitTypeId, count: int):
        assert name is not None and isinstance(name, UnitTypeId)
        assert count is not None and isinstance(count, int)
        super().__init__()

        self.name = name
        self.count = count

    def check(self) -> bool:
        count = self.cache.own(self.name).amount
        if self.name == UnitTypeId.WARPGATE:
            count += self.cache.own(UnitTypeId.GATEWAY).amount

        if count < self.count:
            return True
        return False
