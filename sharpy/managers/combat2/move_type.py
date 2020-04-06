import enum


class MoveType(enum.IntEnum):
    # Look for enemies, even if they are further away.
    SearchAndDestroy = 0
    # Same as attack move
    Assault = 1
    # When attacked from sides, fight back while moving
    Push = 2
    # Shoot while retreating
    DefensiveRetreat = 3
    # Use everything in arsenal to escape the situation
    PanicRetreat = 4
    # Don't fight with buildings and skip enemy army units if possible
    Harass = 5
    # Attempt to regroup with other units.
    ReGroup = 6