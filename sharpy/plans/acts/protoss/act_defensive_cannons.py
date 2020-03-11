from typing import Optional

from sharpy.general.zone import Zone
from sc2 import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit

from sharpy.plans.acts.act_base import ActBase


class ActDefensiveCannons(ActBase):
    """Act of starting to build new buildings up to specified count"""

    def __init__(self, to_count_pre_base: int, additional_batteries: int = 0, to_base_index: Optional[int] = None):
        self.to_base_index = to_base_index
        self.additional_batteries = additional_batteries
        assert to_count_pre_base is not None and isinstance(to_count_pre_base, int) and (to_count_pre_base > 0 or additional_batteries > 0)
        self.to_count_per_base = to_count_pre_base

        super().__init__()

    async def execute(self) -> bool:
        map_center = self.ai.game_info.map_center
        pending_cannon_count = self.pending_build(UnitTypeId.PHOTONCANNON)
        pending_battery_count = self.pending_build(UnitTypeId.SHIELDBATTERY)

        all_ready = True

        # Go through zones so that furthest expansions are fortified first
        zones = self.knowledge.expansion_zones
        for i in range(0, len(zones)):
            zone = zones[i]
            # Filter out zones that aren't ours and own zones that we are about to lose.
            if zone.our_townhall is None or zone.known_enemy_power.ground_power > zone.our_power.ground_presence:
                continue

            if self.to_base_index is not None and i != self.to_base_index:
                # Defenses are not ordered to that base
                continue

            closest_pylon: Unit = None
            pylons = zone.our_units(UnitTypeId.PYLON)
            if pylons.exists:
                closest_pylon = pylons.closest_to(zone.center_location)

            available_minerals = self.ai.minerals - self.knowledge.reserved_minerals
            can_afford_cannon = available_minerals >= 150
            can_afford_battery = available_minerals >= 100

            if closest_pylon is None or closest_pylon.distance_to(zone.center_location) > 10:
                # We need a pylon, but only if one isn't already on the way
                if not self.pending_build(UnitTypeId.PYLON) and can_afford_battery:
                    await self.ai.build(UnitTypeId.PYLON, near=zone.center_location.towards(map_center, 4))

                all_ready = False
                continue

            if zone.our_photon_cannons.amount + pending_cannon_count < self.to_count_per_base:
                all_ready = False
                if closest_pylon.is_ready and can_afford_cannon:
                    pos = self.defense_position(zone, closest_pylon)
                    await self.ai.build(UnitTypeId.PHOTONCANNON, near=pos)

            if zone.our_batteries.amount + pending_battery_count < self.additional_batteries:
                all_ready = False
                if closest_pylon.is_ready and can_afford_battery:
                    pos = self.defense_position(zone, closest_pylon)
                    await self.ai.build(UnitTypeId.SHIELDBATTERY, near=pos)

        return all_ready

    def defense_position(self, zone: Zone, pylon: Unit):
        position: Point2 = pylon.position
        path = zone.paths.get(self.knowledge.enemy_main_zone.zone_index, None)
        if path and path.distance > 50:
            target_pos = path.get_index(10)
            return position.towards(target_pos, 3)

        return position.towards(zone.center_location, -2)
