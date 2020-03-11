from sc2 import UnitTypeId
from sc2.ids.ability_id import AbilityId

from .act_base import ActBase


# Act of researching a technology or upgrade
class ActMorphBuilding(ActBase):
    def __init__(self, ability_type: AbilityId, from_unit: UnitTypeId, to_unit: UnitTypeId):
        assert ability_type is not None and isinstance(ability_type, AbilityId)
        assert from_unit is not None and isinstance(from_unit, UnitTypeId)
        assert to_unit is not None and isinstance(to_unit, UnitTypeId)

        self.ability_type = ability_type
        self.from_unit = from_unit
        self.to_unit = to_unit

        super().__init__()

    async def execute(self) -> bool:
        fromUnits = self.cache.own(self.from_unit)
        toUnits = self.cache.own(self.to_unit)

        # check if something is morphing
        if fromUnits.exists:
            for unit in fromUnits:
                if not unit.noqueue and unit.orders[0].ability.id is self.ability_type:
                    return True

        # if unit exists, we ready
        if toUnits.exists and len(toUnits) > 0:
            return True

        cost = self.ai._game_data.abilities[self.ability_type.value].cost

        if fromUnits.ready.exists and self.knowledge.can_afford(self.ability_type):
            for builder in fromUnits.ready:
                if len(builder.orders) == 0:
                    self.knowledge.print(f'Tech started: {self.ability_type.name}')
                    self.do(builder(self.ability_type))
                    return False

        self.knowledge.reserve(cost.minerals, cost.vespene)
        return False
