# Cancels a building when it's about to get destroyed
from sharpy.plans.acts import ActBase
from sc2.unit import Unit
from sc2.constants import *


# Plan that cancels a building if it is going down
class PlanCancelBuilding(ActBase):
    def __init__(self):
        super().__init__()

    async def execute(self) -> bool:
        for building in self.ai.structures: # type: Unit
            if 1 > building.build_progress > 0:
                if self.knowledge.building_going_down(building):
                    self.print(f'Cancelled {building.type_id.name} at {building.position} with {building.health} health')
                    self.do(building(AbilityId.CANCEL_BUILDINPROGRESS))
        return True


