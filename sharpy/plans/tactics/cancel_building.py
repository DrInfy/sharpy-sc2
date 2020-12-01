from sharpy.interfaces import IPreviousUnitsManager
from sharpy.plans.acts import ActBase
from sc2.unit import Unit
from sc2.constants import *


class PlanCancelBuilding(ActBase):
    # Cancels a building when it's about to get destroyed
    def __init__(self):
        super().__init__()

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.previous_units_manager = knowledge.get_required_manager(IPreviousUnitsManager)

    async def execute(self) -> bool:
        for building in self.ai.structures:  # type: Unit
            if 1 > building.build_progress > 0:
                if self.building_going_down(building):
                    self.print(
                        f"Cancelled {building.type_id.name} at {building.position} with {building.health} health"
                    )
                    building(AbilityId.CANCEL_BUILDINPROGRESS)
        return True

    def building_going_down(self, building: Unit) -> bool:
        """Returns boolean indicating whether a building is low on health and under attack."""
        previous_building = self.previous_units_manager.last_unit(building.tag)
        if previous_building:
            health = building.health
            compare_health = max(70, building.health_max * 0.09)
            if health < previous_building.health < compare_health:
                return True
        return False
