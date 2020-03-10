from sc2 import AbilityId, UnitTypeId
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit

from sharpy.plans.acts.act_base import ActBase


class ChronoTech(ActBase):
    # Use Chronoboost on tech upgrade
    def __init__(self, name: AbilityId, from_building: UnitTypeId):
        assert name is not None and isinstance(name, AbilityId)
        assert from_building is not None and isinstance(from_building, UnitTypeId)

        self.name = name
        self.from_building = from_building
        super().__init__()

    async def execute(self):
        #if ai.already_pending_upgrade(self.name):
        target: Unit
        for target in self.cache.own(self.from_building).ready:
            for order in target.orders:
                if order.ability.id == self.name:
                    # boost here!
                    if not target.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
                        for nexus in self.cache.own(UnitTypeId.NEXUS):
                            abilities = await self.ai.get_available_abilities(nexus)
                            if AbilityId.EFFECT_CHRONOBOOSTENERGYCOST in abilities:
                                self.do(nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, target))
                                self.print(f'Chrono to {self.name}!')
        return True # Never block
