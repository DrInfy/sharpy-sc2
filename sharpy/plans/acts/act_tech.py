from sc2 import UnitTypeId, AbilityId
from sc2.ids.upgrade_id import UpgradeId

from sc2.units import Units
from .act_base import ActBase


# Act of researching a technology or upgrade
class ActTech(ActBase):
    def __init__(self, upgrade_type: UpgradeId, from_building: UnitTypeId):
        assert upgrade_type is not None and isinstance(upgrade_type, UpgradeId)
        assert from_building is not None and isinstance(from_building, UnitTypeId)

        self.upgrade_type = upgrade_type
        self.from_building = from_building

        super().__init__()

    async def execute(self) -> bool:
        builders = self.cache.own(self.from_building).ready

        if self.already_pending_upgrade(builders) > 0:
            return True # Started

        cost = self.ai._game_data.upgrades[self.upgrade_type.value].cost
        creationAbilityID = self.solve_ability()

        if builders.ready.exists and self.knowledge.can_afford(self.upgrade_type):
            for builder in builders.ready:
                if len(builder.orders) == 0:
                    # todo: remove this call?
                    abilities = await self.ai.get_available_abilities(builder, True)
                    self.print(f'Started {self.upgrade_type.name}')
                    self.do(builder(creationAbilityID))
                    return False

        self.knowledge.reserve(cost.minerals, cost.vespene)
        return False

    def solve_ability(self) -> AbilityId:
        if self.upgrade_type == UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL1:
            return AbilityId.ARMORYRESEARCH_TERRANVEHICLEANDSHIPPLATINGLEVEL1
        if self.upgrade_type == UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL2:
            return AbilityId.ARMORYRESEARCH_TERRANVEHICLEANDSHIPPLATINGLEVEL2
        if self.upgrade_type == UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL3:
            return AbilityId.ARMORYRESEARCH_TERRANVEHICLEANDSHIPPLATINGLEVEL3

        return self.ai._game_data.upgrades[self.upgrade_type.value].research_ability.id

    def already_pending_upgrade(self, builders: Units) -> float:
        if self.upgrade_type in self.ai.state.upgrades:
            return 1

        creationAbilityID = self.solve_ability()

        level = None
        if "LEVEL" in self.upgrade_type.name:
            level = self.upgrade_type.name[-1]

        for structure in builders:
            for order in structure.orders:
                if order.ability.id is creationAbilityID:
                    if level and order.ability.button_name[-1] != level:
                        return 0
                    return order.progress
        return 0
