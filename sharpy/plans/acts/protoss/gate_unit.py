from sharpy.plans.acts import ActUnit, ActWarpUnit
from sc2 import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId


class GateUnit(ActUnit):
    def __init__(self, unit_type: UnitTypeId, to_count: int = 9999, priority: bool = False, only_once: bool = False):
        super().__init__(unit_type, UnitTypeId.GATEWAY, to_count, priority)
        self.only_once = only_once
        self.warp = ActWarpUnit(unit_type, to_count)

    def get_unit_count(self) -> int:
        count = super().get_unit_count()

        if self.only_once:
            count += self.knowledge.lost_units_manager.own_lost_type(self.unit_type)
        return count

    async def start(self, knowledge: 'Knowledge'):
        await self.warp.start(knowledge)
        await super().start(knowledge)

    async def execute(self) -> bool:
        if self.ai.already_pending_upgrade(UpgradeId.WARPGATERESEARCH) >= 1:
            if self.is_done:
                return True
            # Ensure that unit types are the same, python please some proper setters and getters?!?
            self.warp.to_count = self.to_count
            self.warp.unit_type = self.unit_type
            return await self.warp.execute()

        return await super().execute()
