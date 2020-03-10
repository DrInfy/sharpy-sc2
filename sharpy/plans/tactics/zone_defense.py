from typing import List, Dict

from sharpy.managers.combat2 import MoveType
from sharpy.plans.acts import ActBase
from sc2 import UnitTypeId, Race
from sc2.unit import Unit

from sharpy.knowledges import Knowledge

from sharpy.managers.roles import UnitTask
from sharpy.general.extended_power import ExtendedPower
from sc2.units import Units


class PlanZoneDefense(ActBase):
    ZONE_CLEAR_TIMEOUT = 3

    def __init__(self):
        super().__init__()
        self.worker_return_distance2 = 10 ** 10

        self.defender_tags: Dict[int, List[int]] = dict()
        self.defender_secondary_tags: Dict[int, List[int]] = dict()
        self.zone_seen_enemy: Dict[int, float] = dict()


    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)
        self.worker_type: UnitTypeId = knowledge.my_worker_type

        for i in range(0, len(self.knowledge.expansion_zones)):
            self.defender_tags[i] = []
            self.zone_seen_enemy[i] = -10

    def defense_required(self, enemies: Units):
        if enemies.exists:  # and (len(enemies) > 1 or enemies[0].type_id not in self.unit_values.worker_types):
            return True
        return False

    async def execute(self) -> bool:
        unit: Unit

        all_defenders = self.knowledge.roles.all_from_task(UnitTask.Defending)

        for i in range(0, len(self.knowledge.expansion_zones)):
            zone: 'Zone' = self.knowledge.expansion_zones[i]
            zone_tags = self.defender_tags[i]

            zone_defenders_all = all_defenders.tags_in(zone_tags)
            zone_worker_defenders = zone_defenders_all(self.worker_type)
            zone_defenders = zone_defenders_all.exclude_type(self.worker_type)
            enemies = zone.known_enemy_units

            # Let's loop zone starting from our main, which is the one we want to defend the most
            # Check that zone is either in our control or is our start location that has no Nexus
            if zone_defenders.exists or zone.is_ours or zone == self.knowledge.own_main_zone:
                if not self.defense_required(enemies):
                    # Delay before removing defenses in case we just lost visibility of the enemies
                    if zone.last_scouted_center == self.knowledge.ai.time \
                            or self.zone_seen_enemy[i] + PlanZoneDefense.ZONE_CLEAR_TIMEOUT < self.ai.time:
                        self.knowledge.roles.clear_tasks(zone_defenders_all)
                        zone_defenders.clear()
                        zone_tags.clear()
                        continue  # Zone is well under control.
                else:
                    self.zone_seen_enemy[i] = self.ai.time

                if enemies.exists:
                    # enemy_center = zone.assaulting_enemies.center
                    enemy_center = enemies.closest_to(zone.center_location).position
                elif zone.assaulting_enemies:
                    enemy_center = zone.assaulting_enemies.closest_to(zone.center_location).position
                else:
                    enemy_center = zone.gather_point
                
                defense_required = ExtendedPower(self.unit_values)
                defense_required.add_power(zone.assaulting_enemy_power)
                defense_required.multiply(1.5)

                defenders = ExtendedPower(self.unit_values)

                for unit in zone_defenders:
                    self.combat.add_unit(unit)
                    defenders.add_unit(unit)

                # Add units to defenders that are being warped in.
                for unit in self.knowledge.roles.units(UnitTask.Idle).not_ready:
                    if unit.distance_to(zone.center_location) < zone.radius:
                        # unit is idle in the zone, add to defenders
                        self.combat.add_unit(unit)
                        self.knowledge.roles.set_task(UnitTask.Defending, unit)
                        zone_tags.append(unit.tag)

                if not defenders.is_enough_for(defense_required):
                    defense_required.substract_power(defenders)
                    for unit in self.knowledge.roles.get_defenders(defense_required, zone.center_location):
                        if unit.distance_to(zone.center_location) < zone.radius:
                            # Only count units that are close as defenders
                            defenders.add_unit(unit)

                        self.knowledge.roles.set_task(UnitTask.Defending, unit)
                        self.combat.add_unit(unit)
                        zone_tags.append(unit.tag)

                if len(enemies) > 1 or (len(enemies) == 1 and enemies[0].type_id not in self.unit_values.worker_types):
                    # Pull workers to defend only and only if the enemy isn't one worker scout
                    if defenders.is_enough_for(defense_required):
                        # Workers should return to mining.
                        for unit in zone_worker_defenders:
                            zone.go_mine(unit)
                            if unit.tag in zone_tags:  # Just in case, should be in zone tags always.
                                zone_tags.remove(unit.tag)
                        # Zone is well under control without worker defense.
                    else:
                        await self.worker_defence(defenders.power, defense_required, enemy_center, zone, zone_tags,
                                              zone_worker_defenders)

                self.combat.execute(enemy_center, MoveType.SearchAndDestroy)
        return True  # never block


    async def worker_defence(self, defenders: float, defense_required, enemy_center, zone: 'Zone', zone_tags,
                             zone_worker_defenders):
        ground_enemies: Units = zone.known_enemy_units.not_flying
        
        # Enemy value on same level and not on ramp
        hostiles_inside = 0
        for unit in ground_enemies:
            if self.ai.get_terrain_height(unit.position) == self.ai.get_terrain_height(zone.center_location):
                hostiles_inside += self.unit_values.defense_value(unit.type_id)

        if self.ai.workers.amount >= self.ai.supply_used - 2:
            # Workers only, defend for everything
            if zone.our_units.filter(lambda u: u.is_structure and u.health_percentage > 0.6):
                # losing a building, defend for everything
                if ground_enemies(UnitTypeId.PHOTONCANNON):
                    # Don't overreact if it's a low ground cannon rush
                    # 2 per proba and 4 per cannon is optimal
                    defense_count_panic = defense_required.power * 0.75
                else:
                    defense_count_panic = defense_required.power * 1.3

                threshold = 8
            else:
                defense_count_panic = hostiles_inside * 1.3
                threshold = 6 # probably a worker fight?
        else:
            defense_count_panic = hostiles_inside * 1.1
            threshold = 16

        if ground_enemies.exists:
            closest = ground_enemies.closest_to(zone.center_location)
            killing_probes = closest.distance_to(zone.center_location) < 6
        else:
            # No ground enemies near workers. There could be eg. a banshee though.
            killing_probes = False


        # Loop currently defending workers
        for unit in zone_worker_defenders:
            if unit.shield + unit.health < threshold and not killing_probes:
                zone.go_mine(unit)
                if unit.tag in zone_tags:  # Just in case, should be in zone tags always.
                    zone_tags.remove(unit.tag)
            else:
                defenders += self.unit_values.defense_value(self.worker_type)
                self.combat.add_unit(unit)

        if self.ai.time > 5 * 60 and not killing_probes and not self.knowledge.enemy_race == Race.Zerg:
            # late game and enemies aren't killing probes, go back to mining!
            return

        if defense_required.power < 1 and not killing_probes:
            return # Probably a single scout, don't pull workers

        if zone.our_wall() and self.ai.time < 200:
            possible_defender_workers = self.ai.workers
        else:
            possible_defender_workers = zone.our_workers

        if self.knowledge.my_race == Race.Protoss and not killing_probes:
            # This is to protect against sending all units to defend against zealots and others and just die
            defense_count_panic = defense_count_panic * 0.5

        # Get help from other workers
        # type of worker unit doesn't really matter here, add current worker defenders to defender count
        for worker in possible_defender_workers.tags_not_in(zone_tags):
            # Let's use ones with shield left
            if defenders < defense_count_panic and (worker.shield > 3 or killing_probes):
                zone_tags.append(worker.tag)
                self.knowledge.roles.set_task(UnitTask.Defending, worker)
                defenders += self.unit_values.defense_value(worker.type_id)
                self.combat.add_unit(worker)

    async def debug_actions(self):
        for zone in self.defender_tags:
            tags: List[int] = self.defender_tags.get(zone)
            for tag in tags:
                unit = self.cache.by_tag(tag)
                if unit:
                    text = f"Defending {zone}"
                    self._client.debug_text_world(text, unit.position3d)

