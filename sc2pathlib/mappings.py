from enum import IntEnum

class MapsType(IntEnum):
    PureGround = 0
    Ground = 1
    Air = 2
    Both = 3

class MapType(IntEnum):
    Ground = 0
    Reaper = 1
    Colossus = 2
    Air = 3