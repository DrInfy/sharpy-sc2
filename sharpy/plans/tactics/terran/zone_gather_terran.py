import sc2
from sharpy.plans.acts import ActBase
from sc2 import UnitTypeId, AbilityId
from sc2.position import Point2
from sc2.unit import Unit

from sharpy.knowledges import Knowledge
from sharpy.managers import UnitValue


class PlanZoneGatherTerran(ActBase):
    def __init__(self):
        super().__init__()

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        self.unit_values: UnitValue = knowledge.unit_values
        self.gather_point = self.knowledge.gather_point
        self.gather_set: sc2.List[int] = []

    async def execute(self) -> bool:
        random_variable = (self.ai.state.game_loop % 120) * 0.1
        random_variable *= 0.6
        unit: Unit
        if self.gather_point != self.knowledge.gather_point:
            self.gather_set.clear()
            self.gather_point = self.knowledge.gather_point

        unit: Unit
        for unit in self.cache.own([sc2.UnitTypeId.BARRACKS, sc2.UnitTypeId.FACTORY]) \
                .tags_not_in(self.gather_set):
            # Rally point is set to prevent units from spawning on the wrong side of wall in
            pos: Point2 = unit.position
            pos = pos.towards(self.knowledge.gather_point, 3)
            self.do(unit(sc2.AbilityId.RALLY_BUILDING, pos))
            self.gather_set.append(unit.tag)

        units = []
        units.extend(self.knowledge.roles.idle)

        for unit in units:
            if self.knowledge.should_attack(unit):
                d = unit.position.distance_to(self.gather_point)
                if (unit.type_id == UnitTypeId.SIEGETANK and d < random_variable):
                    ramp = self.knowledge.base_ramp
                    if unit.distance_to(ramp.bottom_center) > 5 and unit.distance_to(ramp.top_center) > 4:
                        self.ai.do(unit(AbilityId.SIEGEMODE_SIEGEMODE))
                elif (d > 6.5 and unit.type_id != UnitTypeId.SIEGETANKSIEGED) or d > 9:
                    self.combat.add_unit(unit)

        self.combat.execute(self.gather_point)
        return True # Always non blocking
