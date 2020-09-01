from sc2 import UnitTypeId
from sharpy.plans.tactics import Scout
from sharpy.plans.tactics.scouting import ScoutBaseAction


class LingScout(Scout):
    def __init__(self, unit_count: int = 2, *args: ScoutBaseAction):
        super().__init__(UnitTypeId.ZERGLING, unit_count, *args)
