from math import ceil

from sharpy.plans.acts import GridBuilding
from sc2 import UnitTypeId


class AutoDepot(GridBuilding):
    """Builds pylons automatically when needed based on predicted supply growth speed."""
    def __init__(self):
        super().__init__(UnitTypeId.SUPPLYDEPOT, 0)

    async def execute(self):
        self.to_count = await self.pylon_count_calc()
        return await super().execute()

    async def pylon_count_calc(self) -> int:
        growth_speed = 0
        nexus_count = self.cache.own({UnitTypeId.COMMANDCENTER, UnitTypeId.PLANETARYFORTRESS,
                                      UnitTypeId.ORBITALCOMMAND}).ready.amount

        rax_count = self.cache.own(UnitTypeId.BARRACKS).ready.amount
        rax_count += self.cache.own(UnitTypeId.BARRACKSREACTOR).ready.amount

        factory_count = self.cache.own(UnitTypeId.FACTORY).ready.amount
        factory_count += self.cache.own(UnitTypeId.FACTORYREACTOR).ready.amount
        starport_count = self.cache.own(UnitTypeId.STARPORT).ready.amount
        starport_count += self.cache.own(UnitTypeId.STARPORTREACTOR).ready.amount

        # Probes take 12 seconds to build
        # https://liquipedia.net/starcraft2/Nexus_(Legacy_of_the_Void)
        growth_speed += nexus_count / 12.0

        # https://liquipedia.net/starcraft2/Barracks_(Legacy_of_the_Void)
        # fastest usage is marauder supply with 2 supply and train 21 seconds
        growth_speed += rax_count * 2 / 21.0

        # https://liquipedia.net/starcraft2/Factory_(Legacy_of_the_Void)
        # fastest usage is helliom with 2 supply and build time of 21 seconds
        growth_speed += factory_count * 2 / 21.0

        # https://liquipedia.net/starcraft2/Stargate_(Legacy_of_the_Void)
        # We'll ues viking timing here
        growth_speed += starport_count * 2 / 30.0

        growth_speed *= 1.2  # Just a little bit of margin of error
        build_time = 21  # depot build time
        # build_time += min(self.ai.time / 60, 5) # probe walk time

        predicted_supply = min(200, self.ai.supply_used + build_time * growth_speed)
        current_depots = self.cache.own({UnitTypeId.SUPPLYDEPOT, UnitTypeId.SUPPLYDEPOTLOWERED,
                                      UnitTypeId.SUPPLYDEPOTDROP}).ready.amount

        if self.ai.supply_cap == 200:
            return current_depots

        return ceil((predicted_supply - self.ai.supply_cap) / 8) + current_depots
