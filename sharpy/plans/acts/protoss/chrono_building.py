import warnings

from sc2 import UnitTypeId, AbilityId
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit, UnitOrder

from sharpy.plans.acts.act_base import ActBase


class ChronoBuilding(ActBase):
    # Use Chronoboost on unit production
    def __init__(self, building_type: UnitTypeId, count: int = 0):
        """
        Chrono boosts a busy building.
        @param building_type: Which building to chrono
        @param count: Amount of times to cast chronoboost, use 0 for infinite
        """
        assert building_type is not None and isinstance(building_type, UnitTypeId)

        self.building_type = building_type
        self.count = count
        self.casted = 0
        super().__init__()

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)

    async def execute(self) -> bool:
        if self.casted > 0 and self.count < self.casted:
            return True

        for target in self.cache.own(self.building_type).ready:  # type: Unit
            if target.orders:
                # boost here!
                if not target.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
                    for nexus in self.cache.own(UnitTypeId.NEXUS):
                        if self.cd_manager.is_ready(
                            nexus.tag, AbilityId.EFFECT_CHRONOBOOSTENERGYCOST
                        ) and self.allow_new_action(nexus):
                            self.do(nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, target))
                            self.print(f"Chrono {target.orders[0].ability.id.name}")
                            self.casted += 1
                            return True  # TODO: better solution for real time, to prevent multiple duplicate chronos
        return True  # Never block
