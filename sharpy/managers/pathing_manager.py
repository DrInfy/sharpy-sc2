import logging
from math import floor
from typing import List, Dict, Tuple

from sharpy.general.extended_power import ExtendedPower
from sharpy.managers.unit_value import buildings_2x2, buildings_3x3, buildings_5x5
from sharpy.sc2math import point_normalize
from sc2.ids.effect_id import EffectId
from sc2.units import Units

from sharpy.general.rocks import *

from sc2.game_info import GameInfo

from sharpy.managers import ManagerBase
import sc2pathlibp
from sc2.position import Point2
from sc2.unit import Unit


class PathingManager(ManagerBase):
    def __init__(self):
        super().__init__()
        self.path_finder_terrain: sc2pathlibp.PathFinder = None
        self.path_finder_ground: sc2pathlibp.PathFinder = None
        self.path_finder_air: sc2pathlibp.PathFinder = None
        self.found_points = []
        self.found_points_air = []

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)

        game_info: GameInfo = self.ai.game_info
        path_grid = game_info.pathing_grid
        placement_grid = game_info.placement_grid

        _data = [[0 for y in range(path_grid.height)] for x in range(path_grid.width)]

        for x in range(0, path_grid.width):
            for y in range(0, path_grid.height):
                pathable = path_grid.is_set((x, y)) or placement_grid.is_set((x, y))
                if pathable:
                    _data[x][y] = 1

        self.path_finder_terrain = sc2pathlibp.PathFinder(_data)
        self.path_finder_ground = sc2pathlibp.PathFinder(_data)

        self.path_finder_terrain.normalize_influence(20)

        air_data = [[1 for y in range(path_grid.height)] for x in range(path_grid.width)]
        for x in range(0, path_grid.width):
            for y in range(0, path_grid.height):
                if x < game_info.playable_area.x \
                        or x > game_info.playable_area.x + game_info.playable_area.width\
                        or y < game_info.playable_area.y \
                        or y > game_info.playable_area.y + game_info.playable_area.height:
                    air_data[x][y] = 0
        self.path_finder_air = sc2pathlibp.PathFinder(air_data)

    async def update(self):
        await self.update_influence()
        self.found_points.clear()
        self.found_points_air.clear()

    def set_rocks(self, grid: sc2pathlibp.PathFinder):
        for rock in self.ai.destructables:  # type: Unit
            rock_type = rock.type_id
            if rock.name == "MineralField450":
                # Attempts to solve the issue with sc2 linux 4.10 vs Windows 4.11
                grid.create_block(rock.position, (2, 1))
            elif rock_type in breakable_rocks_2x2:
                grid.create_block(rock.position, (2, 2))
            elif rock_type in breakable_rocks_4x4:
                grid.create_block(rock.position, (4, 3))
                grid.create_block(rock.position, (3, 4))
            elif rock_type in breakable_rocks_6x6:
                grid.create_block(rock.position, (6, 4))
                grid.create_block(rock.position, (5, 5))
                grid.create_block(rock.position, (4, 6))
            elif rock_type in breakable_rocks_4x2:
                grid.create_block(rock.position, (4, 2))
            elif rock_type in breakable_rocks_2x4:
                grid.create_block(rock.position, (2, 4))
            elif rock_type in breakable_rocks_6x2:
                grid.create_block(rock.position, (6, 2))
            elif rock_type in breakable_rocks_2x6:
                grid.create_block(rock.position, (2, 6))
            elif rock_type in breakable_rocks_diag_BLUR:
                for y in range(-4, 6):
                    if y == -4:
                        grid.create_block(rock.position + Point2((y + 2, y)), (1, 1))
                    elif y == 5:
                        grid.create_block(rock.position + Point2((y - 2, y)), (1, 1))
                    elif y == -3:
                        grid.create_block(rock.position + Point2((y - 1, y)), (3, 1))
                    elif y == 4:
                        grid.create_block(rock.position + Point2((y + 1, y)), (3, 1))
                    else:
                        grid.create_block(rock.position + Point2((y, y)), (5, 1))

            elif rock_type in breakable_rocks_diag_ULBR:
                for y in range(-4, 6):
                    if y == -4:
                        grid.create_block(rock.position + Point2((-y - 2, y)), (1, 1))
                    elif y == 5:
                        grid.create_block(rock.position + Point2((-y + 2, y)), (1, 1))
                    elif y == -3:
                        grid.create_block(rock.position + Point2((-y + 1, y)), (3, 1))
                    elif y == 4:
                        grid.create_block(rock.position + Point2((-y - 1, y)), (3, 1))
                    else:
                        grid.create_block(rock.position + Point2((-y, y)), (5, 1))

    async def update_influence(self):
        power = ExtendedPower(self.unit_values)
        self.path_finder_terrain.reset()  # Reset
        self.path_finder_ground.reset()  # Reset

        positions = []

        for mf in self.ai.mineral_field:  # type: Unit
            # In 4.8.5+ minerals are no linger visible in pathing grid
            positions.append(mf.position)

        # for mf in self.ai.mineral_walls:  # type: Unit
        #     # In 4.8.5+ minerals are no linger visible in pathing grid
        #     positions.append(mf.position)

        self.path_finder_terrain.create_block(positions, (2, 1))
        self.path_finder_ground.create_block(positions, (2, 1))

        self.set_rocks(self.path_finder_terrain)
        self.set_rocks(self.path_finder_ground)

        for building in self.ai.structures + self.knowledge.known_enemy_structures:  # type: Unit
            if building.type_id in buildings_2x2:
                self.path_finder_ground.create_block(building.position, (2, 2))
            elif building.type_id in buildings_3x3:
                self.path_finder_ground.create_block(building.position, (3, 3))
            elif building.type_id in buildings_5x5:
                self.path_finder_ground.create_block(building.position, (5, 3))
                self.path_finder_ground.create_block(building.position, (3, 5))

        self.set_rocks(self.path_finder_ground)

        self.path_finder_ground.normalize_influence(20)
        self.path_finder_air.normalize_influence(20)

        for enemy_type in self.cache.enemy_unit_cache:  # type: UnitTypeId
            enemies: Units = self.cache.enemy_unit_cache.get(enemy_type, Units([], self.ai))
            if len(enemies) == 0:
                continue

            example_enemy: Unit = enemies[0]
            power.clear()
            power.add_unit(enemy_type, 100)

            if self.unit_values.can_shoot_air(example_enemy):
                positions: List[Point2] = map(lambda u: u.position, enemies)   # need to be specified in both places
                s_range = self.unit_values.air_range(example_enemy)

                if example_enemy.type_id == UnitTypeId.CYCLONE:
                    s_range = 7

                self.path_finder_air.add_influence(positions, power.air_power, s_range + 3)

            if self.unit_values.can_shoot_ground(example_enemy):
                positions = map(lambda u: u.position, enemies)  # need to be specified in both places
                s_range = self.unit_values.ground_range(example_enemy)
                if example_enemy.type_id == UnitTypeId.CYCLONE:
                    s_range = 7

                if s_range < 2:
                    self.path_finder_ground.add_influence_walk(positions, power.ground_power, 7)
                elif s_range < 5:
                    self.path_finder_ground.add_influence_walk(positions, power.ground_power, 7)
                else:
                    self.path_finder_ground.add_influence(positions, power.ground_power, s_range + 3)

        # influence, radius, points, can it hit air?
        effect_dict: Dict[EffectId, Tuple[float, float, List[Point2], bool]] = dict()
        for effect in self.ai.state.effects:
            values: Tuple[float, float, List[Point2], bool] = None

            if effect.id == EffectId.RAVAGERCORROSIVEBILECP:
                values = effect_dict.get(effect.id, (1000, 2.5, [], True))
                values[2].append(Point2.center(effect.positions))
            elif effect.id == EffectId.BLINDINGCLOUDCP:
                values = effect_dict.get(effect.id, (400, 3.5, [], False))
                values[2].append(Point2.center(effect.positions))
            elif effect.id == EffectId.NUKEPERSISTENT:
                values = effect_dict.get(effect.id, (900, 9, [], True))
                values[2].append(Point2.center(effect.positions))
            elif effect.id == EffectId.PSISTORMPERSISTENT:
                values = effect_dict.get(effect.id, (300, 3.5, [], True))
                values[2].append(Point2.center(effect.positions))
            elif effect.id == EffectId.LIBERATORTARGETMORPHDELAYPERSISTENT:
                values = effect_dict.get(effect.id, (200, 6, [], False))
                values[2].append(Point2.center(effect.positions))
            elif effect.id == EffectId.LIBERATORTARGETMORPHPERSISTENT:
                values = effect_dict.get(effect.id, (300, 6, [], False))
                values[2].append(Point2.center(effect.positions))
            elif effect.id == EffectId.LURKERMP:
                # Each lurker spine deals splash damage to a radius of 0.5
                values = effect_dict.get(effect.id, (1000, 1, [], False))
                values[2].extend(effect.positions)

            if values is not None and effect.id not in effect_dict:
                effect_dict[effect.id] = values

        for effects in effect_dict.values():
            if effects[3]:
                self.path_finder_air.add_influence(effects[2], effects[0], effects[1])
            self.path_finder_ground.add_influence(effects[2], effects[0], effects[1])

        # batteries: Units = self.cache.own(UnitTypeId.SHIELDBATTERY).filter(lambda u: u.energy > 5)
        # if batteries:
        #     positions = map(lambda u: u.position, batteries)
        #     self.path_finder_air.add_influence(positions, -5, 6)
        #     self.path_finder_ground.add_influence(positions, -5, 6)

    async def post_update(self):
        if self.debug:
            self.path_finder_ground.plot(self.found_points)
            self.path_finder_air.plot(self.found_points_air, "air_map")

    def walk_distance(self, start: Point2, target: Point2) -> float:
        result = self.path_finder_ground.find_path(start, target)
        path = result[0]

        if len(path) < 1:
            return 1000  # No path
        return result[1]

    def find_path(self, start: Point2, target: Point2, target_index: int = 20) -> Point2:
        result = self.path_finder_terrain.find_path(start, target)
        path = result[0]

        if len(path) < 1:
            self.print(f"No path found from {start} to {target}", log_level=logging.DEBUG)
            return target

        if len(path) <= target_index:
            return target

        target = path[target_index]
        if self.debug:
            self.found_points.extend(path)
        return Point2((target[0] + 0.5, target[1] + 0.5))

    def find_weak_influence_air(self, target: Point2, radius: float) -> Point2:
        pathing_result = self.path_finder_air.lowest_influence_in_grid(target, floor(radius))
        pos = pathing_result[0]
        return Point2((pos[0] + 0.5, pos[1] + 0.5))

    def find_weak_influence_ground(self, target: Point2, radius: float) -> Point2:
        pathing_result = self.path_finder_ground.safest_spot(target, radius)
        pos = pathing_result[0]
        return Point2((pos[0] + 0.5, pos[1] + 0.5))

    def find_weak_influence_ground_blink(self, target: Point2, radius: float) -> Point2:
        pathing_result = self.path_finder_ground.lowest_influence_in_grid(target, floor(radius))
        pos = pathing_result[0]
        return Point2((pos[0] + 0.5, pos[1] + 0.5))

    def find_influence_air_path(self, start: Point2, target: Point2) -> Point2:
        result = self.path_finder_air.find_path_influence(start, target)
        path = result[0]
        target_index = 4

        if len(path) < 1:
            self.print(f"No path found {start}, {target}")
            return target

        if len(path) <= target_index:
            return target

        target = path[target_index]
        if self.debug:
            self.found_points_air.extend(path)
        return Point2((target[0] + 0.5, target[1] + 0.5))

    def find_influence_ground_path(self, start: Point2, target: Point2, target_index: int = 5) -> Point2:
        result = self.path_finder_ground.find_path_influence(start, target)
        path = result[0]

        if len(path) < 1:
            self.print(f"No path found {start}, {target}")
            return target

        if len(path) <= target_index:
            return target

        target = path[target_index]
        if self.debug:
            self.found_points_air.extend(path)
        return Point2((target[0] + 0.5, target[1] + 0.5))

    def find_low_inside_ground(self, start: Point2, target: Point2, distance: float) -> Point2:
        result = self.path_finder_ground.find_low_inside_walk(start, target, distance)
        result = result[0]  # strip distance
        end_point = Point2((result[0], result[1]))
        result_distance = target.distance_to_point2(end_point)

        if result_distance > distance:
            # Shorten result to be in range for the target
            vector = end_point - target
            normal_vector = point_normalize(vector)
            end_point = normal_vector * distance + target

        return end_point

    def find_low_inside_air(self, start: Point2, target: Point2, distance: float) -> Point2:
        result = self.path_finder_air.find_low_inside_walk(start, target, distance)
        result = result[0]  # strip distance
        end_point = Point2((result[0], result[1]))
        result_distance = target.distance_to_point2(end_point)

        if result_distance > distance:
            # Shorten result to be in range for the target
            vector = end_point - target
            normal_vector = point_normalize(vector)
            end_point = normal_vector * distance + target

        return end_point
