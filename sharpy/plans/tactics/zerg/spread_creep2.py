import random
from typing import List, Optional, Dict, Set
import numpy as np

from sc2.units import Units
from sharpy.managers import BuildingSolver
from sharpy.managers.grids import BlockerType, BuildArea
from sharpy.plans.acts import ActBase
from sc2 import UnitTypeId, AbilityId
from sc2.position import Point2
from sc2.unit import Unit

SPREAD_CREEP_ENERGY = 25
CREEP_TUMOR_MAX_RANGE = 8  # not sure about this

# Max distance before queen is ordered to place tumor, else move there first
QUEEN_TO_TARGET_TUMOR_MAX_DISTANCE = 3

# The minimum distance a point will be marked as 'available' for tumors and queens to spread to
# If a target location is closer than TOWNHALL_MIN_DISTANCE to a townhall, try no longer to spread creep to it, same for CREEP_TUMOR_MIN_DISTANCE and creep tumors
TOWNHALL_MIN_DISTANCE = 10
CREEP_TUMOR_MIN_DISTANCE = 8
# Can be lowered to improve creep spread accuracy, or increased to improve performance
CREEP_TARGET_INTERVAL = 10

# todo:
# * don't spread creep if hostiles are near
# * how to prioritize between injecting larva and spawning creep tumors?
#       -> have a max number on active creep tumors?
#       -> create creep tumors if all hatcheries are already injected and there's enough energy for another round?

tumors = {UnitTypeId.CREEPTUMOR, UnitTypeId.CREEPTUMORBURROWED, UnitTypeId.CREEPTUMORQUEEN}
areas = {BuildArea.Empty, BuildArea.Ramp, BuildArea.BuildingPadding}


class SpreadCreepV2(ActBase):
    def __init__(self):
        self.building_solver: BuildingSolver = None

        # Contains all the tumor locations that the zerg bot should aim for
        self.target_tumor_locations = []
        # Filled later in 'update_available_tumor_locations' function
        self.available_tumor_locations = []
        self.queen_plant_location_cache: Dict[int, Point2] = {}
        self.reserved_expansion_positions: Set[Point2] = set()
        # Locations where a tumor is about to spawn or currently spawning
        self.tumor_used_locations: Set[Point2] = set()
        super().__init__()

    async def start(self, knowledge: "Knowledge"):
        self.building_solver = knowledge.building_solver
        self.ai = knowledge.ai
        self.create_target_tumor_locations()
        self.fill_reserved_expansion_positions()
        return await super().start(knowledge)

    def create_target_tumor_locations(self):
        pathing_grid: np.ndarray = self.ai.game_info.pathing_grid.data_numpy
        map_shape = pathing_grid.shape
        # Contains all the tumor locations that the zerg bot should aim for
        self.target_tumor_locations = [
            Point2((x, y))
            for x in range(CREEP_TARGET_INTERVAL, map_shape[1], CREEP_TARGET_INTERVAL)
            for y in range(CREEP_TARGET_INTERVAL, map_shape[0], CREEP_TARGET_INTERVAL)
            if pathing_grid[y, x] == 1
        ]

    def fill_reserved_expansion_positions(self):
        """ Fill all locations where no creep tumor should be planted at. """
        for expansion in self.ai.expansion_locations_list:
            xx, yy = [int(i) for i in expansion]
            for x in range(-2, 3):
                for y in range(-2, 3):
                    self.reserved_expansion_positions.add(Point2((x + xx, y + yy)))

    async def execute(self) -> bool:
        tumors = self.cache.own(UnitTypeId.CREEPTUMORBURROWED)

        if self.debug and tumors.amount > 0:
            self.print(f"{tumors.amount} creep tumors!")

        await self.update_available_tumor_locations()

        await self.spread_creep_tumors()

        await self.spawn_creep_tumors()

        return True

    async def update_available_tumor_locations(self):
        """
        Filter 'self.target_tumor_locations' by:
            - Remove all locations that already have a townhall nearby
            - Remove all locations that already have a creep tumor nearby
        """
        self.available_tumor_locations.clear()
        # expansions: List[Point2] = self.ai.expansion_locations_list
        townhalls: Units = self.cache.own_townhalls
        tumors: Units = self.cache.own(
            [UnitTypeId.CREEPTUMOR, UnitTypeId.CREEPTUMORQUEEN, UnitTypeId.CREEPTUMORBURROWED]
        )

        self.tumor_used_locations.clear()
        not_idle_tumors = tumors.filter(lambda unit: not unit.is_idle)
        for tumor in not_idle_tumors:
            if isinstance(tumor.order_target, Point2):
                self.tumor_used_locations.add(tumor.order_target.rounded)

        for point in self.target_tumor_locations:  # type: Point2
            if townhalls and townhalls.closest_distance_to(point) < TOWNHALL_MIN_DISTANCE:
                continue
            if tumors and tumors.closest_distance_to(point) < CREEP_TUMOR_MIN_DISTANCE:
                continue
            if (
                self.tumor_used_locations
                and point.distance_to_closest(self.tumor_used_locations) < CREEP_TUMOR_MIN_DISTANCE
            ):
                continue
            self.available_tumor_locations.append(point)

    async def spread_creep_tumors(self):
        """ Orders tumors to plant new tumors. """
        tumors = self.cache.own(UnitTypeId.CREEPTUMORBURROWED)

        for tumor in tumors:  # type: Unit
            if self.knowledge.cooldown_manager.is_ready(tumor.tag, AbilityId.BUILD_CREEPTUMOR_TUMOR):
                position = self.get_next_creep_tumor_position(tumor)
                if position:
                    self.knowledge.cooldown_manager.used_ability(tumor.tag, AbilityId.BUILD_CREEPTUMOR_TUMOR)
                    self.do(tumor(AbilityId.BUILD_CREEPTUMOR_TUMOR, position))

    async def spawn_creep_tumors(self):
        """ Order queens to plant tumors. """
        all_queens = self.cache.own(UnitTypeId.QUEEN)  # todo: include burrowed queens?
        if all_queens.empty:
            return

        idle_queens = all_queens.idle
        # TODO Instead of taking idle queens only, dedicated queen for creep spread to not run back and forth?
        # TODO Stop spreading creep once there are a lot of active creep tumors?

        for queen in idle_queens:  # type: Unit
            if self.knowledge.cooldown_manager.is_ready(queen.tag, AbilityId.BUILD_CREEPTUMOR_QUEEN) and (
                queen.energy >= SPREAD_CREEP_ENERGY * 2 or self.cache.own(UnitTypeId.LARVA).amount > 4
            ):
                position = self.get_next_plant_position(queen)
                if position:
                    # TODO Do not move or plant tumor if enemies are nearby
                    if queen.distance_to(position) < QUEEN_TO_TARGET_TUMOR_MAX_DISTANCE:
                        self.do(queen(AbilityId.BUILD_CREEPTUMOR_QUEEN, position))
                        self.queen_plant_location_cache.pop(queen.tag, None)
                    else:
                        self.do(queen.move(position + Point2((0.5, 0.5))))
                elif self.ai.townhalls and not self.ai.has_creep(queen.position):
                    # No tumor location could be found from current queen location, move queen to closest townhall (back on creep)
                    self.do(queen.move(self.ai.townhalls.closest_to(queen).position))

    def get_next_plant_position(self, queen: Unit) -> Optional[Point2]:
        """ Tries to find a suitable position for queens to plant tumors at. """

        # Map is covered in creep, no need to place more tumors
        if not self.available_tumor_locations:
            return None

        # If queen is close to cached target location, don't return it instantly as creep could've evolved further while the queen was moving to target location
        old_cached_location: Optional[Point2] = self.queen_plant_location_cache.pop(queen.tag, None)

        queen_pos: Point2 = queen.position
        # TODO Find the closest by ground path instead of air distance
        target_pos: Point2 = queen_pos.closest(self.available_tumor_locations)

        # Find path and move along the path and find the last location where it is possible to plant a tumor
        path = self.knowledge.pathing_manager.path_finder_terrain.find_path(queen_pos, target_pos)[0]
        # TODO Figure out why sometimes a queen is stuck and doesn't plant a tumor
        for position_tuple in path[::-1]:
            if queen.tag in self.queen_plant_location_cache:
                # A position to plant tumor was found
                break
            position = Point2(position_tuple)
            if self.is_placeable(position):
                self.queen_plant_location_cache[queen.tag] = position

        # Return the position if one was found
        if queen.tag in self.queen_plant_location_cache:
            return self.queen_plant_location_cache[queen.tag]

        # If no position could be found, return old cached location if it existed
        if old_cached_location and self.is_placeable(old_cached_location):
            self.queen_plant_location_cache[queen.tag] = old_cached_location
            return old_cached_location

        # Mark queen location as possible creep tumor plant location if no location was found
        if queen.tag not in self.queen_plant_location_cache and self.is_placeable(queen_pos):
            self.queen_plant_location_cache[queen.tag] = queen_pos
            return queen_pos

    def get_next_creep_tumor_position(self, tumor: Unit) -> Optional[Point2]:
        """ Tries to find a suitable position for tumors to move to next. """
        tumor_pos: Point2 = tumor.position
        # TODO Find the closest by ground path instead of air distance
        target_pos = tumor_pos.closest(self.available_tumor_locations)

        path = self.knowledge.pathing_manager.path_finder_terrain.find_path(tumor_pos, target_pos)[0]
        # Skip positions close to the tumor, try to find the location furthest from tumor first
        for position_tuple in path[:2:-1]:
            position = Point2(position_tuple)
            # Although creep tumor have 10 cast range on tumor placements, there are still sometimes errors of 'too far away'
            if self.is_placeable(position) and self.ai.is_visible(position) and tumor.distance_to(position) < 9:
                return position

        # A position could not be found, use the old function to find a location
        # TODO Investigate why sometimes a tumor location could not be found, ideas: next location is blocked by vision blocker or creeping up a ramp
        return self.get_next_creep_tumor_position2(tumor)

    def get_next_creep_tumor_position2(self, tumor: Unit) -> Optional[Point2]:
        """ The old version of the find creep tumor locations in case the one above find a suitable location. """
        towards = self.knowledge.enemy_main_zone.center_location

        # iterate a few times so we find a suitable position
        for i in range(10):
            distance_interval = (CREEP_TUMOR_MAX_RANGE - 3, CREEP_TUMOR_MAX_RANGE)
            distance = distance_interval[0] + random.random() * (distance_interval[1] - distance_interval[0])
            next_pos = tumor.position.towards_with_random_angle(towards, distance).rounded

            if self.is_placeable(next_pos):
                close_tumors = self.cache.own_in_range(next_pos, 3).of_type(tumors)
                if not close_tumors:
                    return next_pos

        # suitable position not found
        return None

    def is_placeable(self, position: Point2) -> bool:
        """ Filters out locations that
            - Filter locations that are already target of tumors
            - Have no creep ('illegal' for tumors and queens to plant at this locations)
            - Would block expansion locations
            - Are used by other structures? Or what does building_solver actually do?
        """
        return (
            position not in self.tumor_used_locations
            and self.ai.has_creep(position)
            and position not in self.reserved_expansion_positions
            and self.building_solver.grid.query_area(position, BlockerType.Building1x1, lambda g: g.Area in areas)
        )
