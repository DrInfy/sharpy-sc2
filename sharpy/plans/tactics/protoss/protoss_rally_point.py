from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sharpy.interfaces import IZoneManager
from sharpy.plans.acts import ActBase

from sharpy.tools import IntervalFunc


class ProtossRallyPoint(ActBase):
    """Handles setting worker rally points"""

    ability: AbilityId
    func: IntervalFunc
    zone_manager: IZoneManager

    def __init__(self):
        super().__init__()

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        # set rally point once every 5 seconds
        self.func = IntervalFunc(self.ai, self.set_rally_point, 5)
        self.zone_manager = knowledge.get_required_manager(IZoneManager)

    def set_rally_point(self):
        for building in self.ai.structures.of_type({UnitTypeId.GATEWAY, UnitTypeId.ROBOTICSFACILITY}):
            zone = self.zone_manager.zone_for_unit(building)
            if zone:
                target_direction = zone.center_location
            else:
                target_direction = self.ai.start_location

            pos = building.position.towards(target_direction, 1)
            building(AbilityId.RALLY_BUILDING, pos)

    async def execute(self) -> bool:
        self.func.execute()
        return True
