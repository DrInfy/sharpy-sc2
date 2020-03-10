from sc2 import UnitTypeId, AbilityId
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit, UnitOrder

from sharpy.plans.acts.act_base import ActBase


class ChronoUnitProduction(ActBase):
    # Use Chronoboost on unit production
    def __init__(self, name: UnitTypeId, from_building: UnitTypeId):
        assert name is not None and isinstance(name, UnitTypeId)
        assert from_building is not None and isinstance(from_building, UnitTypeId)

        self.unit_type = name
        self.from_building = from_building
        super().__init__()

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        unit = self.ai._game_data.units[self.unit_type.value]
        self.creation_ability = unit.creation_ability.id

    async def execute(self) -> bool:
        for target in self.cache.own(self.from_building).ready: # type: Unit
            for order in target.orders: # type: UnitOrder
                if order.ability.id == self.creation_ability:
                    # boost here!
                    if not target.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
                        for nexus in self.cache.own(UnitTypeId.NEXUS):
                            abilities = await self.ai.get_available_abilities(nexus)
                            if AbilityId.EFFECT_CHRONOBOOSTENERGYCOST in abilities:
                                self.do(nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, target))
                                self.print(f'Chrono {self.creation_ability.name}')
        return True  # Never block
