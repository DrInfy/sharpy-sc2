import enum
import logging
import sys
from typing import Dict, List, Optional

import sc2pathlib
from sc2.unit import Unit
from sharpy import sc2math
from sharpy.general.path import Path
from sharpy.interfaces import IZoneManager
from sc2.game_info import Ramp
from sc2.units import Units
from sharpy.managers.core.pathing_manager import PathingManager

from sharpy.managers.core.manager_base import ManagerBase
from sharpy.general.zone import Zone
from sc2.position import Point2, Point3
import numpy as np


class MapName(enum.Enum):
    Example = -1
    Unknown = 0
    AcolyteLE = 1
    RedshiftLE = 2
    AbyssalReefLE = 3
    DreamcatcherLE = 4
    DarknessSanctuaryLE = 5
    LostAndFoundLE = 6
    AutomatonLE = 7
    BlueshiftLE = 8
    CeruleanFallLE = 9
    KairosJunctionLE = 10
    ParaSiteLE = 11
    PortAleksanderLE = 12
    StasisLE = 13
    Reminiscence = 14
    CrystalCavern = 15
    IceandChromeLE = 16
    GoldenWallLE = 17
    SubmarineLE = 18
    EverDreamLE = 19
    PillarsofGoldLE = 20
    DeathAuraLE = 21
    EternalEmpireLE = 22
    RomanticideLE = 23
    AscensiontoAiurLE = 24
    # Ai Arena season 2, 2021
    Atmospheres2000 = 25  # 2000AtmospheresAIE
    Blackburn = 26  # BlackburnAIE
    Jagannatha = 27  # JagannathaAIE
    Lightshade = 28  # LightshadeAIE
    # RomanticideAIE
    Oxide = 30  # OxideAIE


MAIN_ZONE_SIZE_CHANGES: Dict[MapName, float] = {
    MapName.IceandChromeLE: 3,
    MapName.ParaSiteLE: -5,
    MapName.SubmarineLE: 2,
    MapName.EverDreamLE: 3,
}


def recognize_map(map_name: str, height_hash: int) -> MapName:
    if height_hash == 4544808:
        return MapName.AcolyteLE
    if "Redshift" in map_name:
        return MapName.RedshiftLE
    if "Abyssal Reef" in map_name:
        return MapName.AbyssalReefLE
    if "Dreamcatcher" in map_name:
        return MapName.DreamcatcherLE
    if "Darkness Sanctuary" in map_name:
        return MapName.DarknessSanctuaryLE
    if "Lost and Found" in map_name:
        return MapName.LostAndFoundLE
    if "Automaton" in map_name:
        return MapName.AutomatonLE
    if "Blueshift" in map_name:
        return MapName.BlueshiftLE
    if "Cerulean Fall" in map_name:
        return MapName.CeruleanFallLE
    if "Kairos Junction" in map_name:
        return MapName.KairosJunctionLE
    if "Para Site" in map_name:
        return MapName.ParaSiteLE
    if "Port Aleksander" in map_name:
        return MapName.PortAleksanderLE
    if "Stasis" in map_name:
        return MapName.StasisLE
    if "Reminiscence" in map_name:
        return MapName.Reminiscence
    if "Crystal Cavern" in map_name:
        return MapName.CrystalCavern
    if height_hash == 3160539:
        return MapName.IceandChromeLE
    if height_hash == 4580412:
        return MapName.GoldenWallLE
    if height_hash == 3109760:
        return MapName.SubmarineLE
    if height_hash == 3660980:
        return MapName.EverDreamLE
    if height_hash == 3652649:
        return MapName.PillarsofGoldLE
    if height_hash == 3713716:
        return MapName.DeathAuraLE
    if height_hash == 4077698:
        return MapName.EternalEmpireLE
    if height_hash == 4099000:
        return MapName.AscensiontoAiurLE
    if height_hash == 3756032:
        return MapName.RomanticideLE
    if height_hash == 3307847:
        return MapName.Atmospheres2000
    if "Blackburn" in map_name:
        return MapName.Blackburn
    if "Jagannatha" in map_name:
        return MapName.Jagannatha
    if "Lightshade" in map_name:
        return MapName.Lightshade
    if "Oxide" in map_name:
        return MapName.Oxide
    return MapName.Unknown


class ZoneManager(ManagerBase, IZoneManager):

    # region Init

    def __init__(self):
        super().__init__()
        # Dictionary for upkeeping zones such as start and expansion locations.
        # Key is position of the zone.
        self.zones: Dict[Point2, Zone] = {}
        self.map: MapName = MapName.Unknown
        # The same zones in the order of expansions, first zone is our starting main base, second our natural
        # and last is enemy starting zone.
        self._expansion_zones: List[Zone] = []

        # True after enemy starting location is found and after this last of expansion_zones is enemy main base
        self._zones_truly_sorted = False
        self.gather_points: List[int] = [0, 1]
        self.zone_sorted_by = None
        self.found_enemy_start: Optional[Point2] = None
        self._enemy_zones: List[Zone] = []
        self._our_zones: List[Zone] = []

    @property
    def expansion_zones(self) -> List[Zone]:
        return self._expansion_zones

    @property
    def our_zones(self) -> List[Zone]:
        return self._our_zones

    @property
    def enemy_zones(self) -> List[Zone]:
        return self._enemy_zones

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)

        self.ai.game_info.player_start_location = Point2(
            [round(self.ai.start_location.x, 1), round(self.ai.start_location.y, 1)]
        )

        for i in range(0, len(self.ai.enemy_start_locations)):
            self.ai.enemy_start_locations[i] = Point2(
                [round(self.ai.enemy_start_locations[i].x, 1), round(self.ai.enemy_start_locations[i].y, 1)]
            )

        # noinspection PyTypeChecker
        height_hash: int = np.sum(knowledge.ai.game_info.terrain_height.data_numpy)
        self.map = recognize_map(self.ai.game_info.map_name, height_hash)
        self.print(f"Map set to: {self.map} from name: {self.ai.game_info.map_name} and hash: {height_hash}.")
        self.init_zones()
        self.set_pathing_zones()

    def set_pathing_zones(self):
        pather = self.knowledge.get_manager(PathingManager)

        if pather:
            expansion_locations_list = []
            for zone in self.zone_manager.expansion_zones:
                expansion_locations_list.append(zone.center_location)
            pather.map.calculate_zones(expansion_locations_list)

    def init_zones(self):
        """Add expansion locations as zones."""
        for exp_loc in self.ai.expansion_locations_list:  # type: Point2
            is_start_location = False
            if exp_loc in self.ai.enemy_start_locations or exp_loc == self.ai.start_location:
                is_start_location = True

            self.zones[exp_loc] = Zone(exp_loc, is_start_location, self.knowledge, self)

            if is_start_location:
                self.zones[exp_loc].radius += MAIN_ZONE_SIZE_CHANGES.get(self.map, 0)
                self.zones[exp_loc].danger_radius += MAIN_ZONE_SIZE_CHANGES.get(self.map, 0)

        self._expansion_zones = list(self.zones.values())

        self._sort_expansion_zones()
        self._zones_truly_sorted = self.enemy_start_location_found
        self.zone_sorted_by = self.enemy_start_location

    def _path_distance(self, start: Point2, end: Point2) -> float:
        path = Path(self.knowledge.pathing_manager.path_finder_terrain.find_path(start, end))
        if path.distance > 0:
            return path.distance
        return start.distance_to(end)  # Failsafe

    def _sort_expansion_zones(self):
        self._expansion_zones.sort(key=self._zone_distance_to_start)
        own_main = self._expansion_zones[0]
        self._expansion_zones.remove(own_main)

        def _zone_distance_to_ramp(zone: Zone):
            base_ramp = own_main.ramp

            if base_ramp is None:
                position = self.ai.start_location
            else:
                ramp: Ramp = base_ramp.ramp
                position = ramp.bottom_center
            return self._path_distance(zone.center_location, position)

        self._expansion_zones.sort(key=self._zone_distance_to_enemy_start)
        enemy_main = self._expansion_zones[0]
        self._expansion_zones.remove(enemy_main)

        self._expansion_zones.sort(key=_zone_distance_to_ramp)
        self.own_natural = self._expansion_zones[0]
        self._expansion_zones.remove(self.own_natural)

        def _zone_distance_to_enemy_ramp(zone: Zone):
            base_ramp = enemy_main.ramp

            if base_ramp is None:
                position = self.enemy_start_location
                if position is None:
                    position = self.ai.enemy_start_locations[0]
            else:
                ramp: Ramp = base_ramp.ramp
                position = ramp.bottom_center

            return self._path_distance(zone.center_location, position)

        self._expansion_zones.sort(key=_zone_distance_to_enemy_ramp)
        self.enemy_natural = self._expansion_zones[0]
        self._expansion_zones.remove(self.enemy_natural)

        items = len(self._expansion_zones) // 2
        self._expansion_zones.sort(key=self._own_zone_distance_to_naturals)
        own_zones = self._expansion_zones[:items]

        for zone in own_zones:
            self._expansion_zones.remove(zone)

        self._expansion_zones.sort(key=self._enemy_zone_distance_to_naturals)
        enemy_zones = self._expansion_zones[::-1]

        self._expansion_zones.clear()
        self._expansion_zones.append(own_main)
        if self.own_natural is not None:
            self._expansion_zones.append(self.own_natural)
        self._expansion_zones.extend(own_zones)

        self._expansion_zones.extend(enemy_zones)
        if self.enemy_natural is not None:
            self._expansion_zones.append(self.enemy_natural)
        self._expansion_zones.append(enemy_main)

        for i in range(0, len(self._expansion_zones)):
            self._expansion_zones[i].zone_index = i

        self.adjust_zones()
        self.print("Zones sorted", stats=False, log_level=logging.DEBUG)

    def adjust_zones(self):
        self.gather_points = self._solve_gather_points()
        # reset caching of the enemy ramp
        self._cached_enemy_base_ramp = None

    def init_zone_pathing(self):
        """ Init zone pathing. This needs to be run after all managers have properly started. """
        pf: sc2pathlib.PathFinder = self.knowledge.pathing_manager.path_finder_terrain
        zone_count = len(self._expansion_zones)
        for i in range(0, zone_count):
            for j in range(i + 1, zone_count):
                path_data = pf.find_path(
                    self._expansion_zones[i].center_location, self._expansion_zones[j].center_location
                )
                self._expansion_zones[i].paths[j] = Path(path_data)
                self._expansion_zones[j].paths[i] = Path(path_data, True)

        for i in range(1, zone_count - 1):
            # Recalculate improved gather points based on pathing
            # Ignore main base gather point
            path = self._expansion_zones[i].paths.get(zone_count - 1)
            if path.distance > 10:
                self._expansion_zones[i].gather_point = path.get_index(6)

        if 2 not in self.gather_points:
            # 3rd base isn't in gather points.
            # however if we need to go through 3rd to get to enemy base from 2nd, it totally should be.
            path = self._expansion_zones[2].paths.get(zone_count - 1)
            path_to_third = self._expansion_zones[2].paths.get(3)
            last_path_index = len(path_to_third.path) - 1

            if path_to_third.get_index(last_path_index).distance_to_point2(path.get_index(last_path_index)) < 10:
                if len(self.gather_points) > 2:
                    self.gather_points.insert(2, 2)
                else:
                    self.gather_points.append(2)

    def _solve_gather_points(self) -> List[int]:
        gather_points = [0, 1]
        last = 1
        count = len(self._expansion_zones) // 2
        if count > 2:
            last_angle = sc2math.line_angle(
                self._expansion_zones[1].center_location, self._expansion_zones[-2].center_location
            )

            for i in range(2, count):
                angle = sc2math.line_angle(
                    self._expansion_zones[last].center_location, self._expansion_zones[i].center_location
                )
                d = sc2math.angle_distance(last_angle, angle)

                if d < 1:
                    last_angle = sc2math.line_angle(
                        self._expansion_zones[i].center_location, self._expansion_zones[-2].center_location
                    )
                    last = i

                gather_points.append(last)

        return gather_points

    def _zone_distance_to_start(self, zone: Zone):
        return zone.center_location.distance_to(self.ai.start_location)

    def _own_zone_distance_to_naturals(self, zone: Zone):
        if self.own_natural is None:
            own_position = self.ai.start_location
        else:
            own_position = self.own_natural.center_location

        if self.enemy_natural is None:
            enemy_location = self.enemy_start_location
            if enemy_location is None:
                enemy_location = self.ai.enemy_start_locations[0]
        else:
            enemy_location = self.enemy_natural.center_location

        return self._path_distance(zone.center_location, own_position) * 2 - self._path_distance(
            zone.center_location, enemy_location
        )

    def _zone_distance_to_enemy_start(self, zone: Zone):
        enemy_location = self.enemy_start_location
        if enemy_location is None:
            enemy_location = self.ai.enemy_start_locations[0]
        return self._path_distance(zone.center_location, enemy_location)

    def _enemy_zone_distance_to_naturals(self, zone: Zone):
        if self.own_natural is None:
            own_position = self.ai.start_location
        else:
            own_position = self.own_natural.center_location

        if self.enemy_natural is None:
            enemy_location = self.enemy_start_location
            if enemy_location is None:
                enemy_location = self.ai.enemy_start_locations[0]
        else:
            enemy_location = self.enemy_natural.center_location

        return self._path_distance(zone.center_location, enemy_location) * 2 - self._path_distance(
            zone.center_location, own_position
        )

    # endregion

    # region Update

    async def update(self):
        self._enemy_zones.clear()
        self._our_zones.clear()
        if self.knowledge.iteration == 0:
            self.init_zone_pathing()

        self.update_own_units_zones()
        self.update_enemy_units_zones()

        for zone in self.zones.values():  # type: Zone
            zone.update()
            if zone.is_ours:
                self._our_zones.append(zone)
            if zone.is_enemys:
                self._enemy_zones.append(zone)

        if not self._zones_truly_sorted and self.enemy_start_location_found:
            self._zones_truly_sorted = True
            self._sort_expansion_zones()
        elif self.enemy_start_location != self.zone_sorted_by:
            self.zone_sorted_by = self.enemy_start_location
            self._sort_expansion_zones()

    def update_own_units_zones(self):
        # Figure out all the zones the units are set in
        tags_in_zones: Dict[int, List[int]] = {}

        for zone in self._expansion_zones:
            # Clear zones
            zone.our_units.clear()

        unknown_tags = set()

        for unit in self.ai.all_own_units:
            zone_index = self.pather.map.get_zone(unit.position) - 1
            if zone_index < 0:
                # No zone detected, what to do now?
                unknown_tags.add(unit.tag)
            else:
                zone = self._expansion_zones[zone_index]
                zone.our_units.append(unit)
                tags_in_zones[unit.tag] = [zone_index]

        for tag in unknown_tags:
            # Create empty arrays for easy code later
            tags_in_zones[tag] = []

        for zone in self._expansion_zones:
            units = self.cache.own_in_range(zone.center_location, zone.radius)
            for unit in units:
                if unit.tag in unknown_tags:
                    # Registering zone here
                    tags_in_zones[unit.tag].append(zone.zone_index)
                    zone.our_units.append(unit)

        for tag, zone_indices in tags_in_zones.items():
            if len(zone_indices) > 1:
                # the unit is registered in multiple zones, let's make it be in only one zone
                unit = self.cache.by_tag(tag)
                best_d: Optional[float] = None
                best_index = None
                for zone_index in zone_indices:
                    zone = self._expansion_zones[zone_index]
                    d = unit.distance_to(zone.center_location)
                    # structures in the same zone are at the same height, units walking in ramps need also accounting
                    height_difference = abs(zone.height - self.ai.get_terrain_height(unit))
                    d += 10 * height_difference
                    if zone.is_neutral:
                        # We'll want to count units as being in relevant zones if possible
                        d += 5

                    if best_d is None or d < best_d:
                        best_index = zone_index
                        best_d = d

                for zone_index in zone_indices:
                    if zone_index != best_index:
                        # Remove the unit from other zones
                        self._expansion_zones[zone_index].our_units.remove(unit)

    def update_enemy_units_zones(self):
        # Figure out all the zones the units are set in
        tags_in_zones: Dict[int, List[int]] = {}

        for zone in self._expansion_zones:
            # Clear zones
            zone.known_enemy_units.clear()

        unknown_tags = set()

        for unit in self.ai.all_enemy_units:
            zone_index = self.pather.map.get_zone(unit.position) - 1
            if zone_index < 0:
                # No zone detected, what to do now?
                unknown_tags.add(unit.tag)
            else:
                zone = self._expansion_zones[zone_index]
                zone.known_enemy_units.append(unit)
                tags_in_zones[unit.tag] = [zone_index]

        for tag in unknown_tags:
            # Create empty arrays for easy code later
            tags_in_zones[tag] = []

        for zone in self._expansion_zones:
            units = self.cache.enemy_in_range(zone.center_location, zone.radius)
            for unit in units:
                if unit.tag in unknown_tags:
                    # Registering zone here
                    tags_in_zones[unit.tag].append(zone.zone_index)
                    zone.known_enemy_units.append(unit)

        for tag, zone_indices in tags_in_zones.items():
            if len(zone_indices) > 1:
                # the unit is registered in multiple zones, let's make it be in only one zone
                unit = self.cache.by_tag(tag)
                best_d: Optional[float] = None
                best_index = None
                for zone_index in zone_indices:
                    zone = self._expansion_zones[zone_index]
                    d = unit.distance_to(zone.center_location)
                    # structures in the same zone are at the same height, units walking in ramps need also accounting
                    height_difference = abs(zone.height - self.ai.get_terrain_height(unit))
                    d += 10 * height_difference
                    if zone.is_neutral:
                        # We'll want to count units as being in relevant zones if possible
                        d += 5

                    if best_d is None or d < best_d:
                        best_index = zone_index
                        best_d = d

                for zone_index in zone_indices:
                    if zone_index != best_index:
                        # Remove the unit from other zones
                        self._expansion_zones[zone_index].known_enemy_units.remove(unit)

    # endregion

    # region Properties

    @property
    def unscouted_zones(self) -> List[Zone]:
        """Returns a list of all zones that have not been scouted."""
        unscouted = [z for z in self.all_zones if not z.is_scouted_at_least_once]
        return unscouted

    @property
    def known_enemy_structures_at_start_height(self) -> Units:
        """Returns known enemy structures that are at the height of start locations."""
        any_start_location = self.ai.enemy_start_locations[0]
        start_location_height = self.ai.get_terrain_height(any_start_location)

        return self.ai.enemy_structures.filter(
            lambda structure: self.ai.get_terrain_height(structure) == start_location_height
        )

    @property
    def enemy_start_location_found(self) -> bool:
        """Returns true if enemy start location has (probably) been found."""
        if len(self.ai.enemy_start_locations) == 1:
            # Two player map. It's obvious where the enemy is.
            return True

        # We have seen enemy structures at start location terrain height,
        # so the enemy should be there. This is needed eg. against terran
        # walls, when the scout can not get near the command center.
        #
        # The scout may also die before it sees a townhall, especially in a
        # four-player map when the scout arrives late.
        if len(self.known_enemy_structures_at_start_height) > 0:
            return True

        if len(self.scouted_enemy_start_zones) + 1 == len(self.enemy_start_zones):
            # we have scouted all the other start locations, so enemy must
            # be at the last one.
            return True

        return False

    @property
    def enemy_start_location(self) -> Point2:
        """Returns the enemy start location, or the most likely one, if one hasn't been found."""
        if len(self.ai.enemy_start_locations) == 1:
            # Two player map. It's obvious where the enemy is.
            return self.ai.enemy_start_locations[0]

        if self.found_enemy_start:
            # We already found the start position once
            return self.found_enemy_start

        closest_start_location: Point2 = None
        closest_distance: float = sys.maxsize

        structures = self.known_enemy_structures_at_start_height
        if structures:
            center = structures.center
            for start_location in self.ai.enemy_start_locations:
                # out of all enemy start locations which one is closest to known start height structures?
                distance = center.distance_to(start_location)
                if distance < closest_distance:
                    closest_start_location = start_location
                    closest_distance = distance

            # Cache that we now know the start location
            self.found_enemy_start = closest_start_location
            return closest_start_location

        possible_zones = []

        for start_location in self.ai.enemy_start_locations:
            zone = self.zones.get(start_location)
            if not zone.is_scouted_at_least_once:
                possible_zones.append(zone)

        if len(possible_zones) > 0:
            return possible_zones[0].center_location

        return self.ai.enemy_start_locations[0]

    @property
    def enemy_main_zone(self) -> Zone:
        """ Returns enemy main / start zone."""
        # todo: maybe at some point this could return enemy's actual main base, if it has lost the start location.
        # todo: detection could be base on eg. number of tech buildings
        return self._expansion_zones[len(self._expansion_zones) - 1]

    @property
    def enemy_expansion_zones(self) -> List[Zone]:
        """Returns enemy expansions zones, sorted by closest to the enemy main zone first."""
        return list(reversed(self._expansion_zones))

    @property
    def all_zones(self) -> List[Zone]:
        """Returns a list of all zones."""
        zones = list(self.zones.values())
        return zones

    @property
    def enemy_start_zones(self) -> List[Zone]:
        """Returns all zones that are possible enemy start locations."""
        filtered = [z for z in self.all_zones if z.is_start_location]
        return filtered

    @property
    def scouted_enemy_start_zones(self) -> List[Zone]:
        """returns possible enemy start zones that have been scouted."""
        scouted = [z for z in self.enemy_start_zones if z.is_scouted_at_least_once]
        return scouted

    @property
    def unscouted_enemy_start_zones(self) -> List[Zone]:
        """Returns possible enemy start zones that have not been scouted. Similar to unscouted_enemy_start_locations."""
        unscouted = [z for z in self.enemy_start_zones if not z.is_scouted_at_least_once]
        return unscouted

    @property
    def our_zones_with_minerals(self) -> List[Zone]:
        """Returns all of our zones that have minerals."""
        filtered = filter(lambda z: z.our_townhall and z.has_minerals, self.our_zones)
        return list(filtered)

    @property
    def own_main_zone(self) -> Zone:
        """Returns our own main zone. If we have lost our base at start location, it will be the
        next safe expansion."""
        start_zone = self.zones[self.ai.start_location]

        if not start_zone.is_ours:
            for zone in self._expansion_zones:
                if zone.is_ours:
                    return zone

        # Start location is ours or we just don't have a base any more.
        return start_zone

    # endregion

    # region Post update / Debug

    async def post_update(self):
        if self.debug:
            client: "Client" = self.ai._client
            i = 0

            for zone in self._expansion_zones:
                z = self.knowledge.get_z(zone.center_location)
                position: Point3 = Point3((zone.center_location.x, zone.center_location.y, z + 1))
                is_gather = i in self.gather_points

                for unit in zone.our_units:
                    self.debug_text_on_unit(unit, f"Z:{zone.zone_index}")

                for unit in zone.known_enemy_units:
                    self.debug_text_on_unit(unit, f"Z:{zone.zone_index}")

                zone_msg = f"Zone {i}"
                if is_gather:
                    zone_msg += " (Gather)"

                if zone.is_neutral:
                    zone_msg += ", neutral"

                if zone.is_ours:
                    zone_msg += ", ours"

                if zone.is_enemys:
                    zone_msg += ", enemys"

                if zone.is_under_attack:
                    zone_msg += ", under attack"

                our_power = round(zone.our_power.power, 1)
                enemy_power = round(zone.known_enemy_power.power, 1)

                zone_msg += f"\nPower {str(our_power)} Enemy {str(enemy_power)}"
                zone_msg += f"\nBalance {zone.power_balance}"

                client.debug_text_world(zone_msg, position, size=12)
                i += 1
                if zone.is_ours:
                    client.debug_sphere_out(position, zone.radius, Point3((0, 200, 0)))
                    client.debug_sphere_out(position, Zone.ZONE_DANGER_RADIUS, Point3((200, 0, 0)))

                    position = Point3((zone.gather_point.x, zone.gather_point.y, z + 1))
                    client.debug_sphere_out(position, 1, Point3((200, 200, 0)))

    # endregion
    def zone_for_unit(self, building: Unit) -> Optional[Zone]:
        if building.is_mine:
            for zone in self._expansion_zones:
                if zone.our_units.find_by_tag(building.tag):
                    return zone
        else:
            for zone in self._expansion_zones:
                if zone.known_enemy_units.find_by_tag(building.tag):
                    return zone
        return None
