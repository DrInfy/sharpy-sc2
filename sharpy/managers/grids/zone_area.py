import enum


class ZoneArea(enum.Enum):
    NoZone = 0,
    OwnMainZone = 1,
    OwnNaturalZone = 2,
    OwnThirdZone = 3,
    EnemyMainZone = 4,
    EnemyNaturalZone = 5,
    EnemyThirdZone = 6,