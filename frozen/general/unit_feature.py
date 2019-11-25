import enum


class UnitFeature(enum.Enum):
    Nothing = 0,
    Structure = 1
    Flying = 2
    HitsGround = 3
    ShootsAir = 4
    Cloak = 5
    Detector = 6