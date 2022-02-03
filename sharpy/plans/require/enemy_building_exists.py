import warnings

from sc2.ids.unit_typeid import UnitTypeId

from sharpy.plans.require.require_base import RequireBase


class EnemyBuildingExists(RequireBase):
    """
    Checks if enemy has units of the type based on the information we have seen.
    """

    def __init__(self, unit_type: UnitTypeId, count: int = 1):
        assert unit_type is not None and isinstance(unit_type, UnitTypeId)
        assert count is not None and isinstance(count, int)
        super().__init__()

        self.unit_type = unit_type
        self.count = count

    def check(self) -> bool:
        enemy_count = self.ai.all_enemy_units(self.unit_type).amount
        if enemy_count is None:
            return False

        if enemy_count >= self.count:
            return True

        return False
