from typing import List

import sc2
from sc2.ids.ability_id import AbilityId
from sharpy.interfaces import IGatherPointSolver, IUnitValues
from sharpy.plans.acts import ActBase
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit

from sharpy.knowledges import Knowledge


class PlanZoneGatherTerran(ActBase):
    gather_point: Point2
    gather_set: List[int]
    gather_point_solver: IGatherPointSolver
    unit_values: IUnitValues

    def __init__(self):
        super().__init__()

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.gather_point_solver = knowledge.get_required_manager(IGatherPointSolver)
        self.unit_values = knowledge.get_required_manager(IUnitValues)
        self.gather_point = self.gather_point_solver.gather_point
        self.gather_set: List[int] = []

    async def execute(self) -> bool:
        random_variable = (self.ai.state.game_loop % 120) * 0.1
        random_variable *= 0.6
        unit: Unit
        if self.gather_point != self.gather_point_solver.gather_point:
            self.gather_set.clear()
            self.gather_point = self.gather_point_solver.gather_point
            main_ramp = self.zone_manager.own_main_zone.ramp
            if main_ramp and main_ramp.bottom_center.distance_to(self.gather_point) < 5:
                # Nudge gather point just a slightly further
                self.gather_point = self.gather_point.towards(main_ramp.bottom_center, -3)

        unit: Unit
        for unit in self.cache.own([UnitTypeId.BARRACKS, UnitTypeId.FACTORY]).tags_not_in(self.gather_set):
            # Rally point is set to prevent units from spawning on the wrong side of wall in
            pos: Point2 = unit.position
            pos = pos.towards(self.gather_point_solver.gather_point, 3)
            unit(AbilityId.RALLY_BUILDING, pos)
            self.gather_set.append(unit.tag)

        units = []
        units.extend(self.roles.idle)

        for unit in units:
            if self.unit_values.should_attack(unit):
                d = unit.position.distance_to(self.gather_point)
                if unit.type_id == UnitTypeId.SIEGETANK and d < random_variable:
                    ramp = self.zone_manager.expansion_zones[0].ramp
                    if unit.distance_to(ramp.bottom_center) > 5 and unit.distance_to(ramp.top_center) > 4:
                        unit(AbilityId.SIEGEMODE_SIEGEMODE)
                elif (d > 6.5 and unit.type_id != UnitTypeId.SIEGETANKSIEGED) or d > 9:
                    self.combat.add_unit(unit)

        self.combat.execute(self.gather_point)
        return True  # Always non blocking
