from sharpy.managers.core.grids import BuildArea
from sharpy.managers.core.grids.zone_area import ZoneArea
from sharpy.managers.core.grids.cliff import Cliff


class GridArea:
    def __init__(self, area: BuildArea):
        self.Area: BuildArea = area
        self.ZoneIndex = ZoneArea.NoZone
        self.BuildingIndex = -1
        self.Cliff = Cliff.No
