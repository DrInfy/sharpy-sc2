from sc2 import UnitTypeId, AbilityId
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit


from sharpy.plans.acts.act_base import ActBase


class ChronoAnyTech(ActBase):
    ENERGY_COST = 50

    def __init__(self, save_to_energy: int):
        assert save_to_energy is not None and isinstance(save_to_energy, int)
        self.save_to_energy = save_to_energy
        self.types = [UnitTypeId.FORGE, UnitTypeId.ROBOTICSBAY, UnitTypeId.TWILIGHTCOUNCIL, UnitTypeId.TEMPLARARCHIVE,
                      UnitTypeId.CYBERNETICSCORE, UnitTypeId.DARKSHRINE, UnitTypeId.FLEETBEACON]
        super().__init__()

    async def execute(self):
        # if ai.already_pending_upgrade(self.name):
        target: Unit
        nexus: Unit
        for target in self.cache.own(self.types).ready:
            for order in target.orders:
                # TODO: Chrono only up to 90% or 95% complete.
                ability_id = order.ability.id

                # boost here!
                if not target.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
                    for nexus in self.cache.own(UnitTypeId.NEXUS):
                        if nexus.energy > self.save_to_energy + ChronoAnyTech.ENERGY_COST:
                            self.do(nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, target))
                            self.print(f'Chrono {ability_id.name}')
                            return True  # Never block and only boost one building per iteration
        return True  # Never block
