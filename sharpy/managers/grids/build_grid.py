import string

from s2clientprotocol.debug_pb2 import Color
from sc2 import UnitTypeId

from sharpy import sc2math
from sharpy.managers.grids.build_area import BuildArea
from sharpy.managers.grids.cliff import Cliff
from sc2.pixel_map import PixelMap
from sharpy.general.rocks import *
from sc2.game_info import GameInfo

import sc2
from sharpy.managers.grids import Grid, GridArea, BlockerType
from sharpy.managers.grids.zone_area import ZoneArea
from sc2.position import Point2, Point3
from sc2.unit import Unit



class BuildGrid(Grid):
    def __init__(self, knowledge):
        """

        :type knowledge: Knowledge
        """
        ai = knowledge.ai
        self.game_info: GameInfo = ai.game_info
        super().__init__(self.game_info.placement_grid.width, self.game_info.placement_grid.height)
        # noinspection PyUnresolvedReferences
        self.knowledge = knowledge # type: Knowledge
        self.Generate(ai)
        self.SolveCliffs(ai)
        self.townhall_color = Point3((200, 170, 55))
        self.building_color = Point3((255, 155, 55))
        self.pylon_color = Point3((55, 255, 200))
        self.mineral_color = Point3((55, 200, 255))
        self.gas_color = Point3((0, 155, 0))
        self.empty_color = Point3((255, 255, 255))
        self.not_buildable_color = Point3((0, 0, 0))
        self.ramp_color = Point3((139, 0, 0))
        self.vision_blocker_color = Point3((139, 0, 80))

    def get_default(self):
        return GridArea(BuildArea.NotBuildable)

    def Generate(self, ai: sc2.BotAI):
        self.copy_build_map(self.game_info.placement_grid)

        for ramp in self.game_info.map_ramps:
            is_ramp = len(ramp.lower) != len(ramp.points)
            for point in ramp.points: # type: Point2
                x = point.x
                y = point.y
                cell: GridArea = self.get(x, y)
                if is_ramp:
                    cell.Area = BuildArea.Ramp
                else:
                    cell.Area = BuildArea.VisionBlocker

        def low_rock_filler(cell):
            cell.Area = BuildArea.LowRock
            return cell

        def high_rock_filler(cell):
            cell.Area = BuildArea.HighRock
            return cell

        for low_blocker in ai.all_units: # type: Unit
            type_id = low_blocker.type_id
            if type_id in unbuildable_rocks:
                self.fill_area(low_blocker.position, BlockerType.Building2x2, low_rock_filler)
            if type_id in breakable_rocks_2x2:
                self.fill_area(low_blocker.position, BlockerType.Building2x2, high_rock_filler)
            if type_id in breakable_rocks_4x4:
                self.fill_area(low_blocker.position, BlockerType.Building4x4, high_rock_filler)
            if type_id in breakable_rocks_6x6:
                self.fill_area(low_blocker.position, BlockerType.Building6x6, high_rock_filler)

        def building_filler(cell):
            cell.Area = BuildArea.TownHall
            cell.BuildingIndex = 0
            return cell

        def mineral_filler(cell):
            cell.Area = BuildArea.Mineral
            cell.BuildingIndex = 0
            return cell

        def vespene_filler(cell):
            cell.Area = BuildArea.Gas
            cell.BuildingIndex = 0
            return cell

        def mining_filler(cell):
            if cell.Area == BuildArea.Empty:
                cell.Area = BuildArea.InMineralLine
            return cell

        for zone in self.knowledge.expansion_zones:
            self.fill_area(zone.center_location, BlockerType.Building5x5, building_filler)

        for neutral_unit in ai.mineral_field: # type: Unit
            self.fill_area(neutral_unit.position, BlockerType.Minerals, mineral_filler)
            self.fill_line(ai, mining_filler, neutral_unit)
            
        for neutral_unit in ai.vespene_geyser: # type: Unit
            self.fill_area(neutral_unit.position, BlockerType.Building3x3, vespene_filler)
            self.fill_line(ai, mining_filler, neutral_unit)

    def fill_line(self, ai, mining_filler, neutral_unit):
        pos: Point2 = neutral_unit.position
        closest_expansion = pos.closest(ai.expansion_locations.keys())
        direction = closest_expansion - neutral_unit.position
        direction = sc2math.point_normalize(direction)
        i = 1
        while i < 5:
            self.fill_area(neutral_unit.position + direction * i, BlockerType.Building2x2, mining_filler)
            i += 1

    def copy_build_map(self, buildGrid:PixelMap):
        for x in range(0, buildGrid.width):
            for y in range(0, buildGrid.height):
                if buildGrid.is_set((x, y)):
                    self.set(x, y, GridArea(BuildArea.Empty))
                else:
                    self.set(x, y, GridArea(BuildArea.NotBuildable))

    def SolveCliffs(self, ai: sc2.BotAI):
        maxDifference = 3
        hMap = self.game_info.terrain_height
        correction = Point2((0, 1))

        x = 2
        while x < self.width - 3:
            y = 3
            while y < self.height - 3:
                pos = Point2((x, y))
                h = hMap[pos + correction]
                possibles = [Point2((x - 2, y - 2)), Point2((x + 2, y - 2)), Point2((x - 2, y + 2)), Point2((x + 2, y + 2))]

                for possible in possibles:
                    # To ensure rounding errors don't drop it to previous pixel.
                    middle = (possible + pos) * 0.500001
                    cell_possible: GridArea = self[possible]
                    cell_middle: GridArea = self[middle]

                    if cell_possible.Area == BuildArea.Empty and cell_middle.Area == BuildArea.NotBuildable:
                        h2 = hMap[possible + correction]
                        difference = h - h2
                        if abs(difference) > maxDifference:
                            continue

                        cell: GridArea = self.get(x, y)

                        if difference < 0:
                            if cell.Cliff == Cliff.HighCliff:
                                cell.Cliff = Cliff.BothCliff
                            else:
                                cell.Cliff = Cliff.LowCliff
                        if difference > 0:
                            if cell.Cliff == Cliff.LowCliff:
                                cell.Cliff = Cliff.BothCliff
                            else:
                                cell.Cliff = Cliff.HighCliff
                y += 1
            x += 1

    def save(self, filename: string):
        if self.knowledge.debug:
            self.save_image(filename, self.select_color)

    def select_color(self, cell: GridArea) -> Color:
        if cell.Area == BuildArea.Building:
            return self.building_color
        elif cell.Area == BuildArea.TownHall:
            return self.townhall_color
        elif cell.Area == BuildArea.Pylon:
            return self.pylon_color
        elif cell.Area == BuildArea.Mineral:
            return self.mineral_color
        elif cell.Area == BuildArea.Gas:
            return self.gas_color
        elif cell.Area == BuildArea.NotBuildable:
            return self.not_buildable_color
        elif cell.Area == BuildArea.Ramp:
            return self.ramp_color
        elif cell.Area == BuildArea.VisionBlocker:
            return self.vision_blocker_color
        elif cell.Area == BuildArea.LowRock:
            return Point3((69, 69, 69))
        elif cell.Area == BuildArea.HighRock:
            return Point3((35, 35, 35))
        elif cell.Area == BuildArea.Empty:
            return self.empty_color
        elif cell.Cliff == Cliff.HighCliff:
            return Point3((169, 169, 169))
        elif cell.Cliff == Cliff.BothCliff:
            return Point3((139, 139, 139))
        elif cell.Cliff == Cliff.LowCliff:
            return Point3((109, 109, 109))
        elif cell.ZoneIndex == ZoneArea.OwnMainZone:
            return Point3((90, 255, 90))
        elif cell.ZoneIndex == ZoneArea.OwnNaturalZone:
            return Point3((255, 255, 90))
        return self.empty_color
