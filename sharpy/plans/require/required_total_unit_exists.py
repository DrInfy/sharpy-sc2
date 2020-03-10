from typing import List

import sc2

from sharpy.plans.require.require_base import RequireBase
from sc2 import UnitTypeId


class RequiredTotalUnitExists(RequireBase):
    """names is a list of units types. Their total count is summed to compare to count."""
    def __init__(self, type_ids: List[UnitTypeId], count: int = 1, include_pending: bool = False, include_killed: bool = False):
        assert count is not None and isinstance(count, int)
        assert include_pending is not None and isinstance(include_pending, bool)
        assert include_killed is not None and isinstance(include_killed, bool)
        super().__init__()

        self.include_killed = include_killed
        self.include_pending = include_pending
        self.count = count
        assert type_ids is not None and isinstance(type_ids, list)
        assert count is not None and isinstance(count, int)
        super().__init__()

        self.type_ids = type_ids
        self.count = count

    def check(self) -> bool:
        amount = 0
        for name in self.type_ids:
            amount += self.count_type(name)

        if amount >= self.count:
            return True
        return False
    
    def count_type(self, unit_type) -> int:
        # TODO: Use aliases
        count = self.cache.own(unit_type).amount

        # Right now this class is used as a skip_until condition for WorkerScout, but in that
        # case RequireBase.start() method is never called and we do not have reference to Knowledge here.
        if self.knowledge is not None:
            # Subtract amount of friendly hallucinated units
            hallucinations = self.knowledge.roles.hallucinated_units.of_type(unit_type)
            count -= hallucinations.amount

        if unit_type == UnitTypeId.WARPGATE:
            count += self.cache.own(UnitTypeId.GATEWAY).amount

        if unit_type == UnitTypeId.HATCHERY:
            count += self.cache.own(UnitTypeId.LAIR).amount
            count += self.cache.own(UnitTypeId.HIVE).amount

        if unit_type == UnitTypeId.COMMANDCENTER:
            count += self.cache.own(UnitTypeId.ORBITALCOMMAND).amount
            count += self.cache.own(UnitTypeId.PLANETARYFORTRESS).amount

        if unit_type == UnitTypeId.WARPPRISM:
            count += self.cache.own(UnitTypeId.WARPPRISMPHASING).amount

        if unit_type == UnitTypeId.LAIR:
            count += self.cache.own(UnitTypeId.HIVE).amount

        if self.include_pending:
            count += self.unit_pending_count(unit_type)
            if unit_type == UnitTypeId.WARPGATE:
                count += self.pending_build(UnitTypeId.GATEWAY)

            if unit_type is UnitTypeId.HATCHERY:
                count += self.pending_build(UnitTypeId.LAIR)
                count += self.pending_build(UnitTypeId.HIVE)

            if unit_type is UnitTypeId.LAIR:
                count += self.pending_build(UnitTypeId.HIVE)

        if self.include_killed:
            count += self.knowledge.lost_units_manager.own_lost_type(unit_type)

        return count
