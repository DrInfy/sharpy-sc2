import random
from typing import List, Optional

from sharpy.managers import BuildingSolver
from sharpy.managers.grids import BlockerType, BuildArea
from sharpy.plans.acts import ActBase
from sc2 import UnitTypeId, AbilityId
from sc2.position import Point2
from sc2.unit import Unit

SPREAD_CREEP_ENERGY = 25
CREEP_TUMOR_MAX_RANGE = 8  # not sure about this


# todo:
# * find edge of creep
# * don't spread creep if hostiles are near
# * how to prioritize between injecting larva and spawning creep tumors?
#       -> have a max number on active creep tumors?
#       -> create creep tumors if all hatcheries are already injected and there's enough energy for another round?
# * avoid blocking own hatchery locations with creep tumors

tumors = {UnitTypeId.CREEPTUMOR, UnitTypeId.CREEPTUMORBURROWED, UnitTypeId.CREEPTUMORQUEEN}
areas = {BuildArea.Empty, BuildArea.Ramp, BuildArea.BuildingPadding}

class SpreadCreep(ActBase):
    def __init__(self):
        self.building_solver: BuildingSolver = None
        super().__init__()

    async def start(self, knowledge: 'Knowledge'):
        self.building_solver = knowledge.building_solver
        return await super().start(knowledge)

    async def execute(self) -> bool:
        tumors = self.cache.own(UnitTypeId.CREEPTUMORBURROWED)

        if self.debug and tumors.amount > 0:
            self.print(f"{tumors.amount} creep tumors!")

        await self.spread_creep_tumors()

        await self.spawn_creep_tumors()

        return True

    async def spread_creep_tumors(self):
        tumors = self.cache.own(UnitTypeId.CREEPTUMORBURROWED)

        for tumor in tumors:  # type: Unit

            if self.knowledge.cooldown_manager.is_ready(tumor.tag, AbilityId.BUILD_CREEPTUMOR_TUMOR):
                position = self.get_next_creep_tumor_position(tumor)
                if position is not None:
                    self.knowledge.cooldown_manager.used_ability(tumor.tag, AbilityId.BUILD_CREEPTUMOR_TUMOR)
                    self.do(tumor(AbilityId.BUILD_CREEPTUMOR_TUMOR, position))

    async def spawn_creep_tumors(self):
        all_queens = self.cache.own(UnitTypeId.QUEEN)  # todo: include burrowed queens?
        if all_queens.empty:
            return

        idle_queens = all_queens.idle

        for queen in idle_queens:  # type: Unit
            if (
                self.knowledge.cooldown_manager.is_ready(queen.tag, AbilityId.BUILD_CREEPTUMOR_QUEEN)
                and (queen.energy >= SPREAD_CREEP_ENERGY * 2 or self.cache.own(UnitTypeId.LARVA).amount > 4)
            ):
                position = self.get_next_plant_position(queen)
                self.do(queen(AbilityId.BUILD_CREEPTUMOR_QUEEN, position))

    def get_next_plant_position(self, queen: Unit) -> Optional[Point2]:
        pos = queen.position
        close_tumors = self.cache.own_in_range(pos, 7).of_type(tumors)
        if close_tumors.of_type(tumors).amount > 3:
            # There's already enough
            return None

        towards = self.knowledge.enemy_main_zone.center_location

        for i in range(3):
            distance_interval = (1, CREEP_TUMOR_MAX_RANGE)
            distance = distance_interval[0] + random.random() * (distance_interval[1] - distance_interval[0])
            next_pos = pos.towards_with_random_angle(towards, distance).rounded

            if (
                    self.building_solver.grid.query_area(next_pos, BlockerType.Building1x1, lambda g: g.Area in areas)
                and self.ai.has_creep(next_pos)
            ):

                if not close_tumors or close_tumors.closest_distance_to(next_pos) > 3:
                    return next_pos

    def get_next_creep_tumor_position(self, tumor: Unit) -> Optional[Point2]:
        towards = self.knowledge.enemy_main_zone.center_location

        # iterate a few times so we find a suitable position
        for i in range(10):
            distance_interval = (CREEP_TUMOR_MAX_RANGE-3, CREEP_TUMOR_MAX_RANGE)
            distance = distance_interval[0] + random.random() * (distance_interval[1] - distance_interval[0])
            next_pos = tumor.position.towards_with_random_angle(towards, distance).rounded

            if (
                    self.building_solver.grid.query_area(next_pos, BlockerType.Building1x1, lambda g: g.Area in areas)
                and self.ai.has_creep(next_pos)
            ):

                close_tumors = self.cache.own_in_range(next_pos, 3).of_type(tumors)
                if not close_tumors:
                    return next_pos

        # suitable position not found
        return None

