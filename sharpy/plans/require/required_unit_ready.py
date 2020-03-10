import sc2
from sc2 import UnitTypeId

from sharpy.plans.require.require_base import RequireBase


class RequiredUnitReady(RequireBase):
    """Condition for how many units must be ready. Used mostly for buildings."""
    def __init__(self, unit_type: UnitTypeId, count: float = 1):
        assert unit_type is not None and isinstance(unit_type, UnitTypeId)
        super().__init__()

        self.unit_type = unit_type
        self.count = count

    def check(self) -> bool:
        count = self.get_count(self.unit_type, False, include_not_ready=False)
        build_progress = 0

        for unit in self.cache.own(self.unit_type).not_ready:
            build_progress = max(build_progress, unit.build_progress)

        count += build_progress
        return count >= self.count
