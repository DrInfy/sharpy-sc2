import warnings

from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit, UnitOrder

from sharpy.plans.acts.act_base import ActBase


class ChronoUnit(ActBase):
    # Use Chronoboost on unit production
    def __init__(self, name: UnitTypeId, from_building: UnitTypeId, count: int = 0):
        """
        Chrono boosts unit production.
        @param name: Unit type for which to chronoboost
        @param from_building: Which building to chrono
        @param count: Amount of times to cast chronoboost, use 0 for infinite
        """
        assert name is not None and isinstance(name, UnitTypeId)
        assert from_building is not None and isinstance(from_building, UnitTypeId)

        self.unit_type = name
        self.from_building = from_building
        self.count = count
        self.casted = 0
        super().__init__()

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        unit = self.ai._game_data.units[self.unit_type.value]
        self.creation_ability = unit.creation_ability.id

    async def execute(self) -> bool:
        if self.count > 0 and self.casted >= self.count:
            return True

        for target in self.cache.own(self.from_building).ready:  # type: Unit
            if target.orders and target.orders[0].ability.id == self.creation_ability:
                # boost here!
                if not target.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
                    for nexus in self.cache.own(UnitTypeId.NEXUS):
                        if self.cd_manager.is_ready(nexus.tag, AbilityId.EFFECT_CHRONOBOOSTENERGYCOST):
                            if nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, target):
                                self.print(f"Chrono {self.creation_ability.name}")
                                self.casted += 1
                                return True
        return True  # Never block
