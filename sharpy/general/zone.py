from typing import Optional, List, Dict

import sc2
from sharpy.general.extended_ramp import ExtendedRamp
from .path import Path
from sharpy.tools import IntervalFunc
from sc2 import UnitTypeId
from sc2.game_info import Ramp
from sc2.unit import Unit
from sc2.position import Point2
from sc2.units import Units

from sharpy.general.extended_power import ExtendedPower

import enum


class ZoneResources(enum.Enum):
    Empty = 0
    NearEmpty = 1
    Limited = 2
    Plenty = 3
    Full = 4


class Zone:
    ZONE_RADIUS = 15
    ZONE_DANGER_RADIUS = 30
    MAIN_ZONE_RAMP_MAX_RADIUS = 26
    ZONE_RAMP_MAX_RADIUS = 15
    ZONE_RADIUS_SQUARED = ZONE_RADIUS ** 2
    VESPENE_GEYSER_DISTANCE = 10

    def __init__(self, center_location, is_start_location, knowledge):
        self.center_location: Point2 = center_location
        self.is_start_location: bool = is_start_location

        self.knowledge = knowledge
        self.ai: sc2.BotAI = knowledge.ai
        self.cache: 'UnitCacheManager' = knowledge.unit_cache
        self.unit_values: 'UnitValue' = knowledge.unit_values
        self.needs_evacuation = False
        self._is_enemys = False

        self.zone_index: int = 0
        self.paths: Dict[int, Path] = dict()  # paths to other expansions as it is dictated in the .expansion_zones
        # Game time seconds when we have last had visibility on this zone.
        self.last_scouted_center: float = -1
        self.last_scouted_mineral_line: float = -1

        # Timing on when there could be enemy workers here
        self.could_have_enemy_workers_in = 0

        # All mineral fields on the zone
        self._original_mineral_fields: Units = self.ai.expansion_locations.get(self.center_location, Units([], self.ai))
        self.mineral_fields: Units = Units(self._original_mineral_fields.copy(), self.ai)

        self.last_minerals: int = 10000000  # Arbitrary value just to ensure a lower value will get updated.
        # Game time seconds when scout has last circled around the center location of this zone.

        # All vespene geysers on the zone
        self.gas_buildings: Units = None

        self.scout_last_circled: Optional[int] = None

        self.our_townhall: Optional[Unit] = None
        self.enemy_townhall: Optional[Unit] = None

        self.known_enemy_units: Units = Units([], self.ai)
        self.our_units: Units = Units([], self.ai)
        self.our_workers: Units = Units([], self.ai)
        self.enemy_workers: Units = Units([], self.ai)
        self.known_enemy_power: ExtendedPower = ExtendedPower(self.unit_values)
        self.our_power: ExtendedPower = ExtendedPower(self.unit_values)

        # Assaulting enemies can be further away, but zone defense should prepare for at least that amount of defense
        self.assaulting_enemies: Units = Units([], self.ai)
        self.assaulting_enemy_power: ExtendedPower = ExtendedPower(self.unit_values)

        # 3 positions behind minerals
        self.behind_mineral_positions: List[Point2] = self._init_behind_mineral_positions()
        self._count_minerals()
        self._minerals_counter = IntervalFunc(knowledge.ai, self._count_minerals, 0.5)
        self.gather_point = self.center_location.towards(self.ai.game_info.map_center, 5)

        self.height = self.ai.get_terrain_height(center_location)

        # This is ExtendedRamp!
        self.ramp = self._find_ramp(self.ai)
        self.radius = Zone.ZONE_RADIUS
        self.danger_radius = Zone.ZONE_DANGER_RADIUS

        if self.ramp is not None:
            self.gather_point = self.ramp.top_center.towards(self.center_location, 4)

    def _init_behind_mineral_positions(self) -> List[Point2]:
        positions: List[Point2] = []
        possible_behind_mineral_positions: List[Point2] = []

        all_mf: Units = self.ai.mineral_field.closer_than(10, self.center_location)

        for mf in all_mf:  # type: Unit
            possible_behind_mineral_positions.append(self.center_location.towards(mf.position, 9))

        positions.append(self.center_location.towards(all_mf.center, 9))  # Center
        positions.insert(0, positions[0].furthest(possible_behind_mineral_positions))
        positions.append(positions[0].furthest(possible_behind_mineral_positions))
        return positions

    @property
    def behind_mineral_position_center(self) -> Point2:
        return self.behind_mineral_positions[1]

    @property
    def mineral_line_center(self) -> Point2:
        return self.behind_mineral_positions[1].towards(self.center_location, 4)

    def calc_needs_evacuation(self):
        """
        Checks if the zone needs evacuation for the workers mining there.
        This is a method because it is quite CPU heavy.
        """

        enemies: Units = self.cache.enemy_in_range(self.mineral_line_center, 10)
        power = ExtendedPower(self.unit_values)
        power.add_units(enemies)
        if power.ground_power > 3 and enemies.exclude_type(self.unit_values.worker_types):
            self.needs_evacuation = True
        else:
            self.needs_evacuation = False

    def _count_minerals(self):

        total_minerals = 0

        nearby_mineral_fields = self.mineral_fields

        for mf in nearby_mineral_fields:  # type: Unit
            if mf.is_mineral_field:
                if mf.is_visible:
                    total_minerals += mf.mineral_contents
                else:
                    # if the last 3 character end in 750, then it's 900 mineral patch, otherwise 1800
                    if "750" == mf.type_id.name[-3:]:
                        total_minerals += 900
                    else:
                        total_minerals += 1800

        if self.last_minerals > total_minerals:
            # Set new standard only if less than last time the minerals were seen
            self.last_minerals = total_minerals

    @property
    def resources(self) -> ZoneResources:
        """Rough amount of mineral resources that are left on the zone."""
        if self.last_minerals >= 10000:
            return ZoneResources.Full
        elif self.last_minerals >= 5000:
            return ZoneResources.Plenty
        elif self.last_minerals >= 1500:
            return ZoneResources.Limited
        elif self.last_minerals > 0:
            return ZoneResources.NearEmpty
        else:
            return ZoneResources.Empty

    def update(self):
        self.mineral_fields.clear()
        for mf in self._original_mineral_fields:
            new_mf = self.cache.mineral_fields.get(mf.position, None)
            if new_mf:
                self.mineral_fields.append(new_mf)

        self.our_power.clear()
        self.known_enemy_power.clear()
        self.assaulting_enemy_power.clear()

        self.our_units: Units = self.cache.own_in_range(self.center_location, self.radius)
        self.known_enemy_units: Units = self.cache.enemy_in_range(self.center_location, self.radius)
        # Only add units that we can fight against
        self.known_enemy_units = self.known_enemy_units.filter(lambda x: x.cloak != 2)
        self.enemy_workers = self.known_enemy_units.of_type(self.unit_values.worker_types)
        self.our_workers: Units = self.our_units.of_type(self.unit_values.worker_types)

        self._minerals_counter.execute()
        self._update_gas_buildings()
        self.update_our_townhall()
        self.update_enemy_townhall()

        if self.ai.is_visible(self.center_location):
            self.last_scouted_center = self.knowledge.ai.time

        if self.ai.is_visible(self.mineral_line_center):
            self.last_scouted_mineral_line = self.knowledge.ai.time

        for unit in self.our_units:
            # Our unit is inside the zone
            self.our_power.add_unit(unit)

        for unit in self.known_enemy_units:
            # Enemy unit is inside the zone
            self.known_enemy_power.add_unit(unit)

        if self.is_ours:
            self.calc_needs_evacuation()
            self.assaulting_enemies: Units = self.cache.enemy_in_range(self.center_location, self.danger_radius)
            self.assaulting_enemy_power.add_units(self.assaulting_enemies)
        else:
            self.needs_evacuation = False
            self.assaulting_enemies.clear()

    def check_best_mineral_field(self) -> Optional[Unit]:
        best_score = 0
        best_mf: Optional[Unit] = None

        for mf in self.mineral_fields:  # type: Unit
            score = mf.mineral_contents
            for worker in self.our_workers:   # type: Unit
                if worker.order_target == mf.tag:
                    score -= 1000
            if score > best_score or best_mf is None:
                best_mf = mf
                best_score = score
        return best_mf

    def update_enemy_worker_status(self):
        if self.is_ours:
            self.could_have_enemy_workers_in = self.ai.time + 5 * 60
        if self.ai.is_visible(self.behind_mineral_position_center.towards(self.center_location, 3)):
            if self.is_enemys:
                if self.enemy_workers:
                    self.could_have_enemy_workers_in = 0
                elif self.enemy_townhall:
                    if self.enemy_townhall.is_ready:
                        self.could_have_enemy_workers_in = self.ai.time + 60
                    else:
                        finish_time = self.unit_values.building_completion_time(self.ai.time, self.enemy_townhall.type_id,
                                                               self.enemy_townhall.build_progress)
                        self.could_have_enemy_workers_in = finish_time + 60
        else:
            if self.is_scouted_at_least_once:
                if not self.is_neutral:
                    self.could_have_enemy_workers_in = self.last_scouted_center + self.unit_values.build_time(UnitTypeId.NEXUS) + 90
            else:
                self.could_have_enemy_workers_in = 3 * 60

    def _update_gas_buildings(self):
        self.gas_buildings = self.ai.gas_buildings.closer_than(Zone.VESPENE_GEYSER_DISTANCE, self.center_location)

    def update_our_townhall(self):
        friendly_townhalls = self.cache.own_townhalls.closer_than(5, self.center_location)
        if friendly_townhalls.exists:
            self.our_townhall = friendly_townhalls.closest_to(self.center_location)
        else:
            self.our_townhall = None

    def update_enemy_townhall(self):
        enemy_townhalls = self.cache.enemy_townhalls.not_flying.closer_than(5, self.center_location)
        if enemy_townhalls.exists:
            self.enemy_townhall = enemy_townhalls.closest_to(self.center_location)
        else:
            self.enemy_townhall = None

        # We are going to presume that the enemy has a town hall even if we don't see one
        self._is_enemys = self.enemy_townhall is not None or \
            (self == self.knowledge.enemy_main_zone and self in self.knowledge.unscouted_zones)
        
    @property
    def should_expand_here(self) -> bool:
        resources = self.has_minerals or self.resources == ZoneResources.Limited

        return resources and not self.is_enemys and self.our_townhall is None

    @property
    def has_minerals(self) -> bool:
        return self.resources != ZoneResources.NearEmpty and self.resources != ZoneResources.Empty

    @property
    def minerals_running_low(self) -> bool:
        return not self.has_minerals or self.resources == ZoneResources.Limited

    @property
    def is_enemys(self) -> bool:
        """ Is there an enemy town hall in this zone? """
        return self._is_enemys

    @property
    def is_neutral(self) -> bool:
        return not self.is_ours and not self.is_enemys

    @property
    def expanding_to(self) -> bool:
        return self.knowledge.expanding_to == self

    @property
    def is_ours(self) -> bool:
        """ Is there a town hall of ours in this zone or have we walled it off?"""
        return self.our_townhall is not None or self.our_wall()

    @property
    def is_under_attack(self) -> bool:
        return self.is_ours and self.power_balance < 0 or \
            self.is_enemys and self.power_balance > 0

    @property
    def safe_expand_here(self) -> bool:
        return (self.is_neutral or self.is_ours) and self.power_balance > -2

    @property
    def is_scouted_at_least_once(self):
        return self.last_scouted_center and self.last_scouted_center > 0

    @property
    def power_balance(self) -> float:
        """Returns the power balance on this zone. Positive power balance indicates we have more units
        than the enemy, and negative indicates enemy has more units."""
        return round(self.our_power.power - self.known_enemy_power.power, 1)

    @property
    def our_photon_cannons(self) -> Units:
        """Returns any of our own static defenses on the zone."""
        # todo: make this work for Terran and Zerg and rename
        return self.our_units(UnitTypeId.PHOTONCANNON).closer_than(10, self.center_location)

    @property
    def our_batteries(self) -> Units:
        """Returns shield batteries."""
        return self.our_units(UnitTypeId.SHIELDBATTERY).closer_than(10, self.center_location)

    @property
    def enemy_static_defenses(self) -> Units:
        """Returns all enemy static defenses on the zone. Both ground and air."""
        # Use a set so we don't count eg. the same photon cannon twice.
        defenses = set()
        defenses.update(self.enemy_static_ground_defenses)
        defenses.update(self.enemy_static_air_defenses)
        return Units(defenses, self.ai)

    # @property
    # def enemy_static_defenses_power(self) -> ExtendedPower:
    #     """Returns power of enemy static defenses on the zone. Both ground and air."""
    #     power = ExtendedPower(self.unit_values)
    #     for static_def in self.enemy_static_defenses:
    #         power.add_unit(static_def)
    #     return power

    @property
    def enemy_static_ground_defenses(self) -> Units:
        """Returns all enemy static ground defenses on the zone."""
        return self.known_enemy_units.filter(self.unit_values.is_static_ground_defense)

    @property
    def enemy_static_power(self) -> ExtendedPower:
        """Returns power of enemy static defenses."""
        power = ExtendedPower(self.unit_values)
        power.add_units(self.enemy_static_defenses)
        return power

    @property
    def enemy_static_ground_power(self) -> ExtendedPower:
        """Returns power of enemy static ground defenses."""
        power = ExtendedPower(self.unit_values)
        for ground_def in self.enemy_static_ground_defenses:
            power.add_unit(ground_def)
        return power

    @property
    def enemy_static_air_defenses(self) -> Units:
        """Returns all enemy static air defenses on the zone."""
        return self.known_enemy_units.filter(self.unit_values.is_static_air_defense)

    @property
    def enemy_static_air_power(self) -> ExtendedPower:
        """Returns power of enemy static ground defenses on the zone."""
        power = ExtendedPower(self.unit_values)
        for air_def in self.enemy_static_air_defenses:
            power.add_unit(air_def)
        return power

    def go_mine(self, unit: Unit):
        self.knowledge.roles.clear_task(unit)

        if len(self.mineral_fields) > 0:
            # Go to mine in this zone
            mf = self.mineral_fields[0]
            self.ai.do(unit.gather(mf))
        elif self.ai.townhalls.exists and self.ai.mineral_field.exists:
            closest_base = self.ai.townhalls.closest_to(self.center_location)
            # Go to mine in some other base
            mf = self.ai.mineral_field.closest_to(closest_base)
            self.ai.do(unit.gather(mf))

    def _find_ramp(self, ai):
        if self.center_location in self.ai.enemy_start_locations or self.center_location == self.ai.start_location:
            ramps: List[Ramp] = [ramp for ramp in self.ai.game_info.map_ramps if len(ramp.upper) == 2
                 and ramp.top_center.distance_to(self.center_location) < Zone.MAIN_ZONE_RAMP_MAX_RADIUS]

            if not ramps:
                ramps: List[Ramp] = [ramp for ramp in self.ai.game_info.map_ramps if len(ramp.upper) <= 4
                                     and ramp.top_center.distance_to(
                    self.center_location) < Zone.MAIN_ZONE_RAMP_MAX_RADIUS]

            if not len(ramps):
                ramps: List[Ramp] = self.ai.game_info.map_ramps

            ramp: Ramp = min(
                ramps,
                key=(lambda r: self.center_location.distance_to(r.top_center))
            )

            if ramp.top_center.distance_to(self.center_location) < Zone.MAIN_ZONE_RAMP_MAX_RADIUS:
                return ExtendedRamp(ramp, self.ai)
            else:
                self.knowledge.print("Main zone ramp not found!", "Zone")

        """ Ramp going closest to center of the map. """
        found_ramp: Optional[ExtendedRamp] = None

        for map_ramp in ai.game_info.map_ramps:  # type: Ramp
            if map_ramp.top_center == map_ramp.bottom_center:
                continue  # Bugged ramp data
            if ai.get_terrain_height(map_ramp.top_center) == self.height \
                    and map_ramp.top_center.distance_to(self.center_location) < Zone.ZONE_RAMP_MAX_RADIUS:

                if found_ramp is None:
                    found_ramp = ExtendedRamp(map_ramp, ai)
                else:
                    if found_ramp.top_center.distance_to(self.gather_point) > map_ramp.top_center.distance_to(
                            self.gather_point):
                        found_ramp = ExtendedRamp(map_ramp, ai)

        return found_ramp

    def our_wall(self):
        if self != self.knowledge.expansion_zones[0] and self != self.knowledge.expansion_zones[1]:
            return False  # Not main base and not natural wall

        gate_position: Point2 = self.knowledge.gate_keeper_position
        if gate_position is not None and self.knowledge.base_ramp.top_center.distance_to(gate_position) < 6:
            # Main base ramp
            return False

        if gate_position is not None and gate_position.distance_to(self.center_location) < 20:
            if self.our_units.of_type({UnitTypeId.GATEWAY, UnitTypeId.WARPGATE, UnitTypeId.CYBERNETICSCORE}):
                # Natural wall should be up
                return True
        return False
