import enum


class BuildArea(enum.Enum):
    Empty = -1
    NotBuildable = 0
    TownHall = -2
    Mineral = -3
    Gas = -4
    InMineralLine = -5
    Ramp = -6
    VisionBlocker = -7
    LowRock = -8
    HighRock = -9
    Pylon = 1
    Building = 101
    BuildingPadding = 102