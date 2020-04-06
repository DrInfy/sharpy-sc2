import enum


class UnitTask(enum.Enum):
    # Do NOT change order or the number values!
    Idle = 0
    Building = 1 # Worker only
    Gathering = 2 # Worker only
    Scouting = 3  # Scouting
    Moving = 4 # Moving to a position, i.e. gather point
    Fighting = 5 # Fighting against enemy somewhere
    Defending = 6 # Defending a zone
    Attacking = 7 # Attacking enemy base
    Reserved = 8 # Reserved for some unknown purpose, i.e. gate keeper
    Hallucination = 9 # Not a real unit.