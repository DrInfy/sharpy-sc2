import enum
import logging
import math
from math import floor
from typing import Dict, List, Optional, Tuple

from s2clientprotocol.debug_pb2 import Color

from sharpy.constants import Constants
from sharpy import sc2math
from sharpy.sc2math import spiral
from sharpy.general.zone import Zone
from sc2 import Race

from sharpy.managers.grids import *
from sc2.client import Client
from sc2.pixel_map import PixelMap

from sc2.game_info import GameInfo

import sc2
from sharpy.managers.manager_base import ManagerBase
from sc2.position import Point2, Point3
from sharpy.general.extended_ramp import RampPosition

from .grids import *

class WallType(enum.IntEnum):
    Auto = 0,
    ProtossNaturalOneUnit = 1,
    ProtossMainZerg = 2,
    ProtossMainProtoss = 3,
    NoWall = 4,
    TerranMainDepots = 5,


def is_empty(cell: GridArea) -> bool:
    return cell.Area == BuildArea.Empty

def is_free(cell: GridArea) -> bool:
    return cell.Area == BuildArea.Empty or cell.Area == BuildArea.BuildingPadding

def fill_padding(cell: GridArea, point: Point2 = None) -> GridArea:
    if cell.Area == BuildArea.Empty:
        cell.Area = BuildArea.BuildingPadding
    return cell

class WallFinder():
    def __init__(self, b1: Point2, b2: Point2, check_from_b1: Point2, check_from_b2: Point2, zealot: Point2, score: int=2):
        assert isinstance(b1, Point2)
        assert isinstance(b2, Point2)
        assert isinstance(check_from_b1, Point2)
        assert isinstance(check_from_b2, Point2)
        self.buildings: List[Point2] = [b1, b2, Point2((0, 0))]
        self.checks: List[Point2] = [b1 + check_from_b1, b2 + check_from_b2]
        self.zealot: Point2 = zealot
        self.score = score

    def query(self, grid: BuildGrid, position: Point2, zone: ZoneArea):
        def is_not_hard_wall(cell: GridArea) -> bool:
            if cell.Area == BuildArea.NotBuildable or cell.Area == BuildArea.HighRock:
                return False
            return True

        # and cell.ZoneIndex == zone

        # Both checks need to match with hard wall
        for check in self.checks:
            if grid.query_area(position + check, BlockerType.Building3x3, is_not_hard_wall):
                return False

        # All buildings must be buildable:
        for building in self.buildings:
            if not grid.query_area(position + building, BlockerType.Building3x3, is_empty):
                return False

        return True

    def positions(self, position: Point2) -> List[Point2]:
        list = []
        for building in self.buildings:
            list.append(position + building)
        return list

class BuildingSolver(ManagerBase):
    def __init__(self):
        super().__init__()
        self.grid: BuildGrid = None
        self.wall_type = WallType.Auto

        self._building_positions: Dict[BuildArea, List[Point2]] = dict()
        self.zealot_position: Optional[Point2] = None

        self.wall_buildings: List[Point2] = []
        self.wall_pylons: List[Point2] = []

        self.wall_finders_v = [
            # Pure vertical walls
            WallFinder(Point2((0, -3)), Point2((0, 4)), Point2((0, -1)), Point2((0, 1)), Point2((0, 2)), 5),

            WallFinder(Point2((1, -3)), Point2((0, 4)), Point2((0, -1)), Point2((0, 1)), Point2((0, 2))),
            WallFinder(Point2((-1, -3)), Point2((0, 4)), Point2((0, -1)), Point2((0, 1)), Point2((0, 2))),

            WallFinder(Point2((1, -3)), Point2((-1, 4)), Point2((0, -1)), Point2((0, 1)), Point2((0, 2))),
            WallFinder(Point2((-1, -3)), Point2((1, 4)), Point2((0, -1)), Point2((0, 1)), Point2((0, 2))),

            # Hybrid vertical walls
            WallFinder(Point2((2, -3)), Point2((-1, 4)), Point2((1, 0)), Point2((0, 1)), Point2((0, 2))),
            WallFinder(Point2((-2, -3)), Point2((1, 4)), Point2((-1, 0)), Point2((0, 1)), Point2((0, 2))),

            WallFinder(Point2((2, 3)), Point2((-1, -4)), Point2((1, 0)), Point2((0, -1)), Point2((0, -2))),
            WallFinder(Point2((-2, 3)), Point2((1, -4)), Point2((-1, 0)), Point2((0, -1)), Point2((0, -2))),

            WallFinder(Point2((2, -3)), Point2((-2, 4)), Point2((1, 0)), Point2((0, 1)), Point2((-1, 2)), 1),
            WallFinder(Point2((-2, -3)), Point2((2, 4)), Point2((-1, 0)), Point2((0, 1)), Point2((1, 2)), 1),

            WallFinder(Point2((2, 3)), Point2((-2, -4)), Point2((1, 0)), Point2((0, -1)), Point2((-1, -2)), 1),
            WallFinder(Point2((-2, 3)), Point2((2, -4)), Point2((-1, 0)), Point2((0, -1)), Point2((1, -2)), 1),
        ]

        self.wall_finders_h = [
            # Pure horizontal walls
            WallFinder(Point2((-3, 0)), Point2((4, 0)), Point2((-1, 0)), Point2((1, 0)), Point2((2, 0))),

            WallFinder(Point2((-3, 1)), Point2((4, 0)), Point2((-1, 0)), Point2((1, 0)), Point2((2, 0))),
            WallFinder(Point2((-3, -1)), Point2((4, 0)), Point2((-1, 0)), Point2((1, 0)), Point2((2, 0))),

            WallFinder(Point2((-3, 1)), Point2((4, -1)), Point2((-1, 0)), Point2((1, 0)), Point2((2, 0))),
            WallFinder(Point2((-3, -1)), Point2((4, 1)), Point2((-1, 0)), Point2((1, 0)), Point2((2, 0))),

            # Hybrid horizontal walls
            WallFinder(Point2((-3, 2)), Point2((4, -1)), Point2((0, 1)), Point2((1, 0)), Point2((2, 0))),
            WallFinder(Point2((-3, -2)), Point2((4, 1)), Point2((0, -1)), Point2((1, 0)), Point2((2, 0))),

            WallFinder(Point2((3, 2)), Point2((-4, -1)), Point2((0, 1)), Point2((-1, 0)), Point2((-2, 0))),
            WallFinder(Point2((3, -2)), Point2((-4, 1)), Point2((0, -1)), Point2((-1, 0)), Point2((-2, 0))),

            WallFinder(Point2((-3, 2)), Point2((4, -2)), Point2((0, 1)), Point2((1, 0)), Point2((2, -1)), 1),
            WallFinder(Point2((-3, -2)), Point2((4, 2)), Point2((0, -1)), Point2((1, 0)), Point2((2, 1)), 1),

            WallFinder(Point2((3, 2)), Point2((-4, -2)), Point2((0, 1)), Point2((-1, 0)), Point2((-2, -1)), 1),
            WallFinder(Point2((3, -2)), Point2((-4, 2)), Point2((0, -1)), Point2((-1, 0)), Point2((-2, 1)), 1),
        ]

        self.wall_finders_d = [
            # Dioganal / ramp walls
            WallFinder(Point2((2, 4)), Point2((-3, -2)), Point2((0, 1)), Point2((-1, 0)), Point2((1, 2))),
            WallFinder(Point2((-2, -4)), Point2((3, 2)), Point2((0, -1)), Point2((1, 0)), Point2((-1, -2))),

            WallFinder(Point2((4, 2)), Point2((-2, -3)), Point2((1, 0)), Point2((0, -1)), Point2((2, 1))),
            WallFinder(Point2((-4, -2)), Point2((2, 3)), Point2((-1, 0)), Point2((0, 1)), Point2((-2, -1))),

            WallFinder(Point2((2, 4)), Point2((-3, -1)), Point2((0, 1)), Point2((-1, 0)), Point2((1, 2))),
            WallFinder(Point2((-2, -4)), Point2((3, 1)), Point2((0, -1)), Point2((1, 0)), Point2((-1, -2))),

            WallFinder(Point2((4, 2)), Point2((-1, -3)), Point2((1, 0)), Point2((0, -1)), Point2((2, 1))),
            WallFinder(Point2((-4, -2)), Point2((1, 3)), Point2((-1, 0)), Point2((0, 1)), Point2((-2, -1))),
        ]

    @property
    def pylon_position(self) -> List[Point2]:
        return self._building_positions.get(BuildArea.Pylon, [])

    @property
    def building_position(self) -> List[Point2]:
        return self._building_positions.get(BuildArea.Building, [])

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        self.grid = BuildGrid(self.knowledge)

        self.color_zone(self.knowledge.expansion_zones[0], ZoneArea.OwnMainZone)
        self.color_zone(self.knowledge.expansion_zones[1], ZoneArea.OwnNaturalZone)
        self.color_zone(self.knowledge.expansion_zones[2], ZoneArea.OwnThirdZone)

    async def update(self):
        if self.knowledge.iteration == 0:
            await self.solve_grid()

    async def post_update(self):
        if self.debug:
            client: "Client" = self.ai._client

            if self.zealot_position:
                x = self.zealot_position.x
                y = self.zealot_position.y
                z = self.knowledge.get_z(Point2((x, y)))
                c1 = Point3((x - 0.25, y- 0.25, z))
                c2 = Point3((x + 0.25, y + 0.25, z + 2))
                client.debug_box_out(c1, c2)

            correction = Point2((0, 1))
            for x in range(0, self.grid.width - 1):
                for y in range(0, self.grid.height - 1):
                    cell: GridArea = self.grid.get(x, y)
                    color = None
                    if cell.Area == BuildArea.Building:
                        color = self.grid.building_color
                    elif cell.Area == BuildArea.TownHall:
                        color = self.grid.townhall_color
                    elif cell.Area == BuildArea.Pylon:
                        color = self.grid.pylon_color
                    elif cell.Area == BuildArea.Mineral:
                        color = self.grid.mineral_color
                    elif cell.Area == BuildArea.Gas:
                        color = self.grid.gas_color
                    #elif cell.Area == BuildArea.Empty:
                    #    color = self.grid.gas_color

                    if color:
                        z = self.knowledge.get_z(Point2((x, y)) + correction)
                        c1 = Point3((x, y, z))
                        c2 = Point3((x + 1, y + 1, z + 1))
                        client.debug_box_out(c1, c2, color)

    async def solve_grid(self):
        if self.wall_type == WallType.Auto:
            if self.knowledge.my_race == Race.Protoss:
                if self.knowledge.enemy_race == Race.Terran:
                    self.wall_type = WallType.NoWall
                elif self.knowledge.enemy_race == Race.Protoss:
                    self.wall_type = WallType.ProtossMainProtoss
                elif self.knowledge.rush_distance < 100:
                    self.wall_type = WallType.ProtossMainZerg
                else:
                    self.wall_type = WallType.ProtossNaturalOneUnit
            elif self.knowledge.my_race == Race.Terran:
                self.wall_type = WallType.TerranMainDepots

        if self.wall_type == WallType.ProtossNaturalOneUnit:
            if not await self.natural_wall():
                self.zerg_wall()
        elif self.wall_type == WallType.ProtossMainProtoss:
            self.protoss_wall()
        elif self.wall_type == WallType.ProtossMainZerg:
            self.zerg_wall()
        elif self.wall_type == WallType.TerranMainDepots:
            self.terran_depot_wall()

        self.solve_buildings()

        if self.debug:
            self.grid.save("buildGrid.bmp")

    def terran_depot_wall(self):
        main: Zone = self.knowledge.own_main_zone
        if main.ramp.ramp.depot_in_middle:
            self.wall_pylons = list(main.ramp.ramp.corner_depots)
            self.wall_pylons.append(main.ramp.ramp.depot_in_middle)
            for pos in self.wall_pylons:
                self.fill_and_save(pos, BlockerType.Building2x2, BuildArea.Pylon)

    def solve_buildings(self):
        start: Point2 = self.knowledge.own_main_zone.center_location
        zone: Zone = self.knowledge.own_main_zone
        zone_color = ZoneArea.OwnMainZone
        self.fill_zone(zone.center_location, zone_color)

        if self.knowledge.my_race == Race.Terran:
            list = self._building_positions.get(BuildArea.Building)
            list.sort(key=lambda k: start.distance_to_point2(k))

        zone: Zone = self.knowledge.expansion_zones[1]
        zone_color = ZoneArea.OwnNaturalZone
        self.fill_zone(zone.center_location, zone_color)

        zone: Zone = self.knowledge.expansion_zones[2]
        zone_color = ZoneArea.OwnThirdZone
        self.fill_zone(zone.center_location, zone_color)

    def fill_zone(self, center: Point2, zone_color: ZoneArea):
        center = Point2((floor(center.x), floor(center.y)))
        x_range = range(-18, 18)

        if self.ai.start_location.x < self.ai.game_info.map_center.x:
            x_range = range(-18, 18)[::-1]
            action = self.pylon_pair_reversed
        else:
            action = self.pylon_pair_normal

        y_range = range(-18, 18)
        if self.ai.start_location.y < self.ai.game_info.map_center.y:
            y_range = range(-18, 18)[::-1]

        if self.knowledge.my_race == Race.Terran:
            for x in x_range:
                for y in y_range:
                    pos = Point2((x + center.x, y + center.y))
                    area: GridArea = self.grid[pos]

                    if area is None or area.ZoneIndex != zone_color:
                        continue

                    self.terran_massive_grid(pos)

            for x in x_range:
                for y in y_range:
                    pos = Point2((x + center.x, y + center.y))
                    area: GridArea = self.grid[pos]

                    if area is None or area.ZoneIndex != zone_color:
                        continue

                    self.terran_grid(pos)
        else:
            if zone_color == ZoneArea.OwnMainZone:
                for x in x_range:
                    for y in y_range:
                        pos = Point2((x + center.x, y + center.y))
                        area: GridArea = self.grid[pos]

                        if area is None or area.ZoneIndex != zone_color:
                            continue

                        self.massive_grid(pos)


            for x in x_range:
                for y in y_range:
                    pos = Point2((x + center.x, y + center.y))
                    area: GridArea = self.grid[pos]

                    if area is None or area.ZoneIndex != zone_color:
                        continue

                    action(pos)

    def massive_grid(self, pos):
        rect = Rectangle(pos.x, pos.y, 6, 9)
        unit_exit_rect = Rectangle(pos.x - 2, pos.y + 4, 2, 2)
        unit_exit_rect2 = Rectangle(pos.x + 6, pos.y + 4, 2, 2)
        padding = Rectangle(pos.x - 2, pos.y -2, 10, 12)

        if (self.grid.query_rect(rect, is_empty)
                and self.grid.query_rect(unit_exit_rect, is_free)
                and self.grid.query_rect(unit_exit_rect2, is_free)):
            pylons = [
                pos + Point2((1, 1)),
                pos + Point2((1+2, 1)),
                pos + Point2((1+4, 1))
            ]
            gates = [
                pos + Point2((1.5, 3.5)),
                pos + Point2((4.5, 3.5)),
                pos + Point2((1.5, 6.5)),
                pos + Point2((4.5, 6.5))
            ]

            pylon_check = pylons[0].offset(Point2((0, -1)))
            if not self.grid.query_area(pylon_check, BlockerType.Building2x2, is_free):
                pylons.pop(0)

            for pylon_pos in pylons:
                self.fill_and_save(pylon_pos, BlockerType.Building2x2, BuildArea.Pylon)

            for gate_pos in gates:
                self.fill_and_save(gate_pos, BlockerType.Building3x3, BuildArea.Building)

            self.grid.fill_rect(padding, fill_padding)

    def terran_grid(self, pos):
        rect = Rectangle(pos.x, pos.y, 6, 5)
        padding = Rectangle(pos.x, pos.y, 7, 5)

        if (self.grid.query_rect(rect, is_empty)):
            pylons = [
                pos + Point2((1, 4)),
                pos + Point2((1 + 2, 4)),
                pos + Point2((1 + 4, 4))
            ]
            gates = [
                pos + Point2((1.5, 1.5)),
            ]
            for pylon_pos in pylons:
                self.fill_and_save(pylon_pos, BlockerType.Building2x2, BuildArea.Pylon)

            for gate_pos in gates:
                self.fill_and_save(gate_pos, BlockerType.Building3x3, BuildArea.Building)

            self.grid.fill_rect(padding, fill_padding)

    def terran_massive_grid(self, pos):
        rect = Rectangle(pos.x, pos.y, 7, 8)
        # padding = Rectangle(pos.x, pos.y - 2, 7, 8)

        if (self.grid.query_rect(rect, is_empty)):
            pylons = [
                pos + Point2((1, 3)),
                pos + Point2((6, 4)),
                pos + Point2((6, 6))
            ]
            gates = [
                pos + Point2((1.5, 5.5)),
                pos + Point2((3.5, 2.5)),
            ]
            for pylon_pos in pylons:
                self.fill_and_save(pylon_pos, BlockerType.Building2x2, BuildArea.Pylon)

            for gate_pos in gates:
                self.fill_and_save(gate_pos, BlockerType.Building3x3, BuildArea.Building)

            self.grid.fill_rect(rect, fill_padding)

    def pylon_pair_normal(self, pos):
        rect_pylon = Rectangle(pos.x, pos.y, 2, 2)
        rect = Rectangle(rect_pylon.right, pos.y, 3, 3)
        if self.grid.query_rect(rect_pylon, is_empty) and self.grid.query_rect(rect, is_empty):
            pylon_pos = pos + Point2((1, 1))
            gate_pos = pos + Point2((3.5, 1.5))
            self.fill_and_save(pylon_pos, BlockerType.Building2x2, BuildArea.Pylon)
            self.fill_and_save(gate_pos, BlockerType.Building3x3, BuildArea.Building)
            self.grid.fill_area(gate_pos, BlockerType.Building5x5, fill_padding)

    def pylon_pair_reversed(self, pos):
        rect_pylon = Rectangle(pos.x, pos.y, 2, 2)
        rect = Rectangle(rect_pylon.x - 3, pos.y, 3, 3)
        if self.grid.query_rect(rect_pylon, is_empty) and self.grid.query_rect(rect, is_empty):
            pylon_pos = pos + Point2((1, 1))
            gate_pos = pos + Point2((-1.5, 1.5))
            self.fill_and_save(pylon_pos, BlockerType.Building2x2, BuildArea.Pylon)
            self.fill_and_save(gate_pos, BlockerType.Building3x3, BuildArea.Building)
            self.grid.fill_area(gate_pos, BlockerType.Building5x5, fill_padding)

    def protoss_wall(self):
        ramp: 'ExtendedRamp' = self.knowledge.base_ramp
        if ramp and ramp.positions:
            pylon = ramp.positions.get(RampPosition.Away)
            zealot = ramp.positions.get(RampPosition.GateZealot) # TODO: Incorrect!
            gate = ramp.positions.get(RampPosition.GateVsProtoss)
            core = ramp.positions.get(RampPosition.CoreVsProtoss)
            self.wall_save(pylon, zealot, [gate, core])

    def zerg_wall(self):
        ramp: 'ExtendedRamp' = self.knowledge.base_ramp
        if ramp and ramp.positions:
            pylon = ramp.positions.get(RampPosition.Away)
            zealot = ramp.positions.get(RampPosition.GateZealot)
            gate = ramp.positions.get(RampPosition.GateInner)
            core = ramp.positions.get(RampPosition.CoreInner)
            self.wall_save(pylon, zealot, [gate, core])

    async def natural_wall(self) -> bool:
        natural: Zone = self.knowledge.expansion_zones[1]

        search_vector: Point2 = natural.center_location - natural.behind_mineral_position_center
        wall_finders: List[WallFinder] = []
        if abs(search_vector.x) > abs(search_vector.y):
            search_vector = Point2((math.copysign(1, search_vector.x), 0))
            perpendicular = Point2((0, -search_vector.x))
            # Add horizontal walls
            wall_finders.extend(self.wall_finders_v)
        else:
            search_vector = Point2((0, math.copysign(1, search_vector.y)))
            perpendicular = Point2((search_vector.x, 0))
            # Add vertical walls
            wall_finders.extend(self.wall_finders_h)

        # Always add diagonal walls
        wall_finders.extend(self.wall_finders_d)

        center = natural.center_location
        if await self.find_wall_in_direction(center, perpendicular, search_vector, wall_finders):
            return True

        search_vector: Point2 = natural.center_location - natural.behind_mineral_position_center
        wall_finders: List[WallFinder] = []
        if abs(search_vector.x) < abs(search_vector.y):
            search_vector = Point2((math.copysign(1, search_vector.x), 0))
            perpendicular = Point2((0, -search_vector.x))
            # Add horizontal walls
            wall_finders.extend(self.wall_finders_v)
        else:
            search_vector = Point2((0, math.copysign(1, search_vector.y)))
            perpendicular = Point2((search_vector.y, 0))
            # Add vertical walls
            wall_finders.extend(self.wall_finders_h)

        # Always add diagonal walls
        wall_finders.extend(self.wall_finders_d)

        return await self.find_wall_in_direction(center, perpendicular, search_vector, wall_finders)

    def is_pathable(self, cell: GridArea) -> bool:
        if cell.Area != BuildArea.Empty and cell.Area != BuildArea.Ramp and cell.Area != BuildArea.VisionBlocker:
            return False
        return True

    async def find_wall_in_direction(self, center: Point2, perpendicular: Point2, search_vector: Point2, wall_finders: List[WallFinder]):
        zone_height = self.ai.get_terrain_height(center)
        enemy_natural: Point2 = self.knowledge.expansion_zones[-2].center_location

        wall: Optional[Tuple[int, Point2, Point2, List[Point2]]] = None

        for i in range(7, 15):
            for j in range(-15, 16):
                lookup = center + search_vector * i + perpendicular * j

                if zone_height != self.ai.get_terrain_height(lookup):
                    # height doesn't match with zone height
                    continue

                for finder in wall_finders:

                    if finder.query(self.grid, lookup, ZoneArea.OwnNaturalZone):
                        if not self.grid.query_area(lookup + search_vector * 5, BlockerType.Building1x1, self.is_pathable) \
                            or not self.grid.query_area(lookup - search_vector * 5, BlockerType.Building1x1, self.is_pathable):
                            # Wall was found, it seems like it's not towards open area
                            self.print(f"Wall was found at {lookup}, but disregarded due to not free area check", stats=False, log_level=logging.DEBUG)
                            continue

                        lookup_distance = await self.client.query_pathing(lookup, enemy_natural)
                        wall_distance = await self.client.query_pathing(lookup + search_vector * 5, enemy_natural)
                        if wall_distance > lookup_distance:
                            self.print(f"Wall was found at {lookup}, but disregarded due to distance check", stats=False, log_level=logging.DEBUG)
                            continue

                        pylon = lookup - 2.5 * search_vector
                        zealot = lookup + finder.zealot
                        gates = finder.positions(lookup)

                        if wall is None:
                            self.print(f'Natural wall found! ({lookup})', stats=False, log_level=logging.DEBUG)
                            wall = (finder.score, pylon, zealot, gates)
                        elif wall[0] < finder.score:
                            self.print(f'Better natural wall found! ({lookup})', stats=False, log_level=logging.DEBUG)
                            wall = (finder.score, pylon, zealot, gates)
                        else:
                            self.print(f'Natural wall found, but disregarded! ({lookup})', stats=False, log_level=logging.DEBUG)
                            wall = (finder.score, pylon, zealot, gates)

        if wall is not None:
            self.save_natural_wall(wall[1], wall[2], wall[3])
            return True
        return False

    def save_natural_wall(self, pylon: Point2, zealot: Point2, gates: List[Point2]):
        pylon = pylon.rounded
        # Fill padding in a way that pylon can't block the entrance
        self.fill_and_save(gates[0], BlockerType.Building5x5, BuildArea.BuildingPadding)
        self.fill_and_save(gates[1], BlockerType.Building5x5, BuildArea.BuildingPadding)
        self.fill_and_save(gates[2], BlockerType.Building3x3, BuildArea.BuildingPadding)
        for position in sc2math.spiral(7, 7):
            pylon_check = pylon + position
            if (
                    self.grid.query_area(pylon_check, BlockerType.Building2x2, is_empty)
                    and pylon_check.distance_to(gates[0]) < Constants.PYLON_POWERED_DISTANCE
                    and pylon_check.distance_to(gates[1]) < Constants.PYLON_POWERED_DISTANCE
                    and pylon_check.distance_to(gates[2]) < Constants.PYLON_POWERED_DISTANCE
            ):
                # That position is free to build on
                pylon = pylon_check
                break

        self.wall_save(pylon, zealot, gates)

    def wall_save(self, pylon: Point2, zealot: Point2, gates: List[Point2]):
        assert isinstance(pylon, Point2)
        assert isinstance(zealot, Point2)

        self.zealot_position = zealot

        self.wall_buildings = gates
        self.wall_pylons = [pylon]

        self.fill_and_save(pylon, BlockerType.Building4x4, BuildArea.BuildingPadding)
        for gate in gates:
            assert isinstance(gate, Point2)
            self.fill_and_save(gate, BlockerType.Building5x5, BuildArea.BuildingPadding)
        self.fill_and_save(pylon, BlockerType.Building2x2, BuildArea.Pylon)
        for gate in gates:
            self.fill_and_save(gate, BlockerType.Building3x3, BuildArea.Building)

    def fill_and_save(self, position: Point2, blocker_type: BlockerType, area: BuildArea):
        if blocker_type != BlockerType.Building2x2 and blocker_type != BlockerType.Building4x4:
            if position.x % 1 != 0.5:
                position = Point2((position.x + 0.5, position.y))
            if position.y % 1 != 0.5:
                position = Point2((position.x, position.y + 0.5))
        else:
            position = Point2((floor(position.x), floor(position.y)))

        if area != BuildArea.BuildingPadding:
            list: List[Point2] = self._building_positions.get(area, [])
            building_index = len(list)
            self._building_positions[area] = list
            list.append(position)
        else:
            building_index = -1

        def filler(cell: GridArea):
            if cell.Area == BuildArea.Empty or cell.Area == BuildArea.BuildingPadding:
                cell.BuildingIndex = building_index
                cell.Area = area
            return cell

        self.grid.fill_area(position, blocker_type, filler)

    def color_zone(self, zone: Zone, zone_type: ZoneArea):
        center = Point2((floor(zone.center_location.x), floor(zone.center_location.y)))

        radius = zone.radius
        height = self.ai.get_terrain_height(center)

        def fill_circle(cell: GridArea, point: Point2) -> GridArea:
            if cell.Area == BuildArea.Empty and height == self.ai.get_terrain_height(point)\
                    and point.distance_to_point2(center) <= zone.radius:
                cell.ZoneIndex = zone_type

            return cell

        rect = Rectangle(center.x - radius, center.y -radius, radius * 2, radius * 2)
        self.grid.fill_rect_func(rect, fill_circle)
