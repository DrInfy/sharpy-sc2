from sc2.ids.unit_typeid import UnitTypeId
from sharpy.interfaces import IEnemyUnitsManager, ILostUnitsManager

from sharpy.plans.require.require_base import RequireBase


class EnemyUnitExistsAfter(RequireBase):
    """
    Checks if enemy has units of the type based on the information we have seen.
    """

    enemy_units_manager: IEnemyUnitsManager
    lost_units_manager: ILostUnitsManager

    def __init__(self, unit_type: UnitTypeId, count: int = 1):
        assert unit_type is not None and isinstance(unit_type, UnitTypeId)
        assert count is not None and isinstance(count, int)
        super().__init__()

        self.unit_type = unit_type
        self.count = count

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.enemy_units_manager = self.knowledge.get_required_manager(IEnemyUnitsManager)
        self.lost_units_manager = self.knowledge.get_required_manager(ILostUnitsManager)

    def check(self) -> bool:
        enemy_count = self.enemy_units_manager.unit_count(self.unit_type)
        enemy_count += self.lost_units_manager.enemy_lost_type(self.unit_type)

        if enemy_count is None:
            return False

        if enemy_count >= self.count:
            return True

        return False
