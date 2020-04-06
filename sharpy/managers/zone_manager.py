import logging
import sys
from typing import Dict, List, Optional

import sc2pathlibp
from sharpy import sc2math
from sharpy.general.path import Path
from sharpy.managers.grids import BuildGrid, GridArea, ZoneArea
from sharpy.mapping import MapInfo
from sc2.game_info import Ramp
from sc2.units import Units

from sharpy.managers.manager_base import ManagerBase
from sharpy.general.zone import Zone
from sc2.position import Point2, Point3


class ZoneManager(ManagerBase):

    # region Init

    def __init__(self):
        super().__init__()
        # Dictionary for upkeeping zones such as start and expansion locations.
        # Key is position of the zone.
        self.zones: Dict[Point2, Zone] = {}
        # The same zones in the order of expansions, first zone is our starting main base, second our natural
        # and last is enemy starting zone.
        self.expansion_zones: List[Zone] = []

        # True after enemy starting location is found and after this last of expansion_zones is enemy main base
        self._zones_truly_sorted = False
        self.gather_points: List[int] = [0, 1]
        self.zone_sorted_by = None
        self.found_enemy_start: Optional[Point2] = None
        self.map: MapInfo = None

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        self.map = knowledge.map
        self.init_zones()

    def init_zones(self):
        """Add expansion locations as zones."""
        for exp_loc in self.ai.expansion_locations:  # type: Point2
            is_start_location = False
            if exp_loc in self.ai.enemy_start_locations:
                is_start_location = True

            self.zones[exp_loc] = Zone(exp_loc, is_start_location, self.knowledge)

        self.expansion_zones = list(self.zones.values())

        self._sort_expansion_zones()
        self._zones_truly_sorted = self.enemy_start_location_found
        self.zone_sorted_by = self.enemy_start_location


    def _path_distance(self, start: Point2, end: Point2):
        path = Path(self.knowledge.pathing_manager.path_finder_terrain.find_path(start, end))
        if path.distance > 0:
            return path.distance
        return start.distance_to(end)  # Failsafe

    def _sort_expansion_zones(self):
        self.expansion_zones.sort(key=self._zone_distance_to_start)
        own_main = self.expansion_zones[0]
        self.expansion_zones.remove(own_main)

        def _zone_distance_to_ramp(zone: Zone):
            base_ramp = own_main.ramp

            if base_ramp is None:
                position = self.ai.start_location
            else:
                ramp: Ramp = base_ramp.ramp
                position = ramp.bottom_center
            return self._path_distance(zone.center_location, position)

        self.expansion_zones.sort(key=self._zone_distance_to_enemy_start)
        enemy_main = self.expansion_zones[0]
        self.expansion_zones.remove(enemy_main)

        self.expansion_zones.sort(key=_zone_distance_to_ramp)
        self.own_natural = self.expansion_zones[0]
        self.expansion_zones.remove(self.own_natural)

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

        self.expansion_zones.sort(key=_zone_distance_to_enemy_ramp)
        self.enemy_natural = self.expansion_zones[0]
        self.expansion_zones.remove(self.enemy_natural)

        items = len(self.expansion_zones) // 2
        self.expansion_zones.sort(key=self._own_zone_distance_to_naturals)
        own_zones = self.expansion_zones[:items]

        for zone in own_zones:
            self.expansion_zones.remove(zone)

        self.expansion_zones.sort(key=self._enemy_zone_distance_to_naturals)
        enemy_zones = self.expansion_zones[::-1]

        self.expansion_zones.clear()
        self.expansion_zones.append(own_main)
        if self.own_natural is not None:
            self.expansion_zones.append(self.own_natural)
        self.expansion_zones.extend(own_zones)

        self.expansion_zones.extend(enemy_zones)
        if self.enemy_natural is not None:
            self.expansion_zones.append(self.enemy_natural)
        self.expansion_zones.append(enemy_main)

        for i in range(0, len(self.expansion_zones)):
            self.expansion_zones[i].zone_index = i

        self.adjust_zones()
        self.print("Zones sorted", stats=False, log_level=logging.DEBUG)

    def adjust_zones(self):
        if self.map.swap_natural_with_third:
            # Manual hack as the natural is 3rd base in distance
            # Tested, actually works correctly
            # Swaps 3rd base with 2nd
            self.expansion_zones.insert(1, self.expansion_zones[2])
            self.expansion_zones.pop(3)
        # Set base radiuses
        for i in range(0, len(self.map.zone_radiuses)):
            self.expansion_zones[i].radius = self.map.zone_radiuses[i]
        self.expansion_zones.reverse()
        # Do the seame revers
        if self.map.swap_natural_with_third:
            # Manual hack as the natural is 3rd base in distance
            # Tested, actually works correctly
            # Swaps 3rd base with 2nd
            self.expansion_zones.insert(1, self.expansion_zones[2])
            self.expansion_zones.pop(3)
        # Set base radiuses for enemy bases too
        for i in range(0, len(self.map.zone_radiuses)):
            self.expansion_zones[i].radius = self.map.zone_radiuses[i]
        self.expansion_zones.reverse()
        self.gather_points = self._solve_gather_points()
        # reset caching of the enemy ramp
        self._cached_enemy_base_ramp = None

    def init_zone_pathing(self):
        """ Init zone pathing. This needs to be run after all managers have properly started. """
        pf: sc2pathlibp.PathFinder = self.knowledge.pathing_manager.path_finder_terrain
        zone_count = len(self.expansion_zones)
        for i in range(0, zone_count):
            for j in range(i + 1, zone_count):
                path_data = pf.find_path(self.expansion_zones[i].center_location, self.expansion_zones[j].center_location)
                self.expansion_zones[i].paths[j] = Path(path_data)
                self.expansion_zones[j].paths[i] = Path(path_data, True)


        for i in range(1, zone_count - 1):
            # Recalculate improved gather points based on pathing
            # Ignore main base gather point
            path = self.expansion_zones[i].paths.get(zone_count - 1)
            self.expansion_zones[i].gather_point = path.get_index(6)

        if 2 not in self.gather_points:
            # 3rd base isn't in gather points, but if we need to go through 3rd to get to 2nd, it totally should be.
            path = self.expansion_zones[2].paths.get(zone_count - 1)
            grid: BuildGrid = self.knowledge.building_solver.grid
            for i in range(5, min(20, len(path.path))):
                target = path.path[i]

                area: GridArea = grid.get(target[0], target[1])
                if area.ZoneIndex == ZoneArea.OwnThirdZone:
                    if len(self.gather_points )> 2:
                        self.gather_points.insert(2, 2)
                    else:
                        self.gather_points.append(2)

    def _solve_gather_points(self) -> List[int]:
        gather_points = [0, 1]
        last = 1
        count = len(self.expansion_zones) // 2
        if count > 2:
            last_angle = sc2math.line_angle(self.expansion_zones[1].center_location, self.expansion_zones[-2].center_location)

            for i in range(2, count):
                angle = sc2math.line_angle(self.expansion_zones[last].center_location, self.expansion_zones[i].center_location)
                d = sc2math.angle_distance(last_angle, angle)

                if d < 1:
                    last_angle = sc2math.line_angle(self.expansion_zones[i].center_location,
                                                    self.expansion_zones[-2].center_location)
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

        return self._path_distance(zone.center_location, own_position) * 2 \
               - self._path_distance(zone.center_location, enemy_location)

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


        return self._path_distance(zone.center_location, enemy_location) * 2 \
               - self._path_distance(zone.center_location, own_position)

    # endregion

    # region Update
    async def update(self):
        if self.knowledge.iteration == 0:
            self.init_zone_pathing()

        for zone in self.zones.values():  # type: Zone
            zone.update()

        if not self._zones_truly_sorted and self.knowledge.enemy_start_location_found:
            self._zones_truly_sorted = True
            self._sort_expansion_zones()
        elif self.enemy_start_location != self.zone_sorted_by:
            self.zone_sorted_by = self.enemy_start_location
            self._sort_expansion_zones()

    # endregion

    # region Properties

    @property
    def known_enemy_structures_at_start_height(self) -> Units:
        """Returns known enemy structures that are at the height of start locations."""
        any_start_location = self.ai.enemy_start_locations[0]
        start_location_height = self.ai.get_terrain_height(any_start_location)

        return self.knowledge.known_enemy_structures.filter(
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
        return self.expansion_zones[len(self.expansion_zones) - 1]

    @property
    def enemy_expansion_zones(self) -> List[Zone]:
        """Returns enemy expansions zones, sorted by closest to the enemy main zone first."""
        return list(reversed(self.expansion_zones))

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
    def own_main_zone(self) -> Zone:
        """Returns our own main zone. If we have lost our base at start location, it will be the
        next safe expansion."""
        start_zone = self.zones[self.ai.start_location]

        if not start_zone.is_ours:
            for zone in self.expansion_zones:
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

            for zone in self.expansion_zones:
                z = self.knowledge.get_z(zone.center_location)
                position: Point3 = Point3((zone.center_location.x, zone.center_location.y, z + 1))
                is_gather = i in self.gather_points

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
