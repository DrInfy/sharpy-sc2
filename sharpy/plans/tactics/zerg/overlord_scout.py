from typing import List, Optional

from sc2.position import Point2
from sc2 import UnitTypeId, AbilityId
from sharpy.plans.tactics.scouting import ScoutBaseAction, Scout


class OverlordScout(Scout):
    def __init__(self, *args: ScoutBaseAction):
        super().__init__(UnitTypeId.OVERLORD, 1, *args)
