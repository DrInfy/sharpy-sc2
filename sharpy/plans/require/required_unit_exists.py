import sc2
from sc2 import UnitTypeId

from sharpy.plans.require.require_base import RequireBase


class RequiredUnitExists(RequireBase):
    def __init__(self, unit_type: UnitTypeId, count: int = 1,
                 include_pending: bool = False,
                 include_killed: bool = False,
                 include_not_ready: bool = True):

        assert unit_type is not None and isinstance(unit_type, UnitTypeId)
        assert count is not None and isinstance(count, int)
        assert include_pending is not None and isinstance(include_pending, bool)
        assert include_killed is not None and isinstance(include_killed, bool)
        assert include_not_ready is not None and isinstance(include_not_ready, bool)
        super().__init__()

        self.include_killed = include_killed
        self.include_pending = include_pending
        self.include_not_ready = include_not_ready
        self.unit_type = unit_type
        self.count = count

    def check(self) -> bool:
        count = self.get_count(self.unit_type, self.include_pending, self.include_killed, self.include_not_ready)
        return count >= self.count
