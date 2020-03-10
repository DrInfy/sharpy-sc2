from math import ceil

from sharpy.plans.acts import GridBuilding
from sc2 import UnitTypeId


class AutoPylon(GridBuilding):
    """Builds pylons automatically when needed based on predicted supply growth speed."""
    def __init__(self):
        super().__init__(UnitTypeId.PYLON, 0)

    async def execute(self):
        self.to_count = await self.pylon_count_calc()
        return await super().execute()

    async def pylon_count_calc(self) -> int:
        growth_speed = 0
        nexus_count = self.cache.own(UnitTypeId.NEXUS).ready.amount

        gate_count = self.cache.own(UnitTypeId.GATEWAY).ready.amount
        gate_count += self.cache.own(UnitTypeId.WARPGATE).ready.amount

        robo_count = self.cache.own(UnitTypeId.ROBOTICSFACILITY).ready.amount
        stargate_count = self.cache.own(UnitTypeId.STARGATE).ready.amount

        # Probes take 12 seconds to build
        # https://liquipedia.net/starcraft2/Nexus_(Legacy_of_the_Void)
        growth_speed += nexus_count / 12.0

        # https://liquipedia.net/starcraft2/Warp_Gate_(Legacy_of_the_Void)
        # fastest usage is zealot supply with 2 supply and warp in cooldown is 20 seconds
        growth_speed += gate_count * 2 / 20.0

        # https://liquipedia.net/starcraft2/Robotics_Facility_(Legacy_of_the_Void)
        # fastest usage is immortal with 4 supply and build time of 39 seconds
        growth_speed += robo_count * 4 / 39.0

        # https://liquipedia.net/starcraft2/Stargate_(Legacy_of_the_Void)
        # fastest usage is tempest with 5 supply and build time of 43 seconds
        growth_speed += stargate_count * 5 / 43.0

        growth_speed *= 1.2  # Just a little bit of margin of error
        build_time = 18  # pylon build time
        # build_time += min(self.ai.time / 60, 5) # probe walk time

        predicted_supply = min(200, self.ai.supply_used + build_time * growth_speed)
        current_pylons = self.cache.own(UnitTypeId.PYLON).ready.amount

        if self.ai.supply_cap == 200:
            return current_pylons

        return ceil((predicted_supply - self.ai.supply_cap) / 8) + current_pylons
