from typing import Optional

from sharpy.plans.acts import ActBase
from sharpy.managers.roles import UnitTask
from sc2 import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit


class BuildPosition(ActBase):

    def __init__(self, unit_type: UnitTypeId, position: Point2, exact: bool = True, only_once: bool = False):
        super().__init__()
        self.exact = exact
        self.position = position
        self.unit_type = unit_type
        self.only_once = only_once
        self.builder_tag: Optional[int] = None

    async def execute(self) -> bool:
        if self.position is None:
            return True

        for building in self.cache.own(self.unit_type): # type: Unit
            if building.distance_to(self.position) < 2:
                if self.only_once:
                    self.position = None
                return True

        position = self.position

        worker = self.get_worker(position)
        if worker is None:
            return True  # No worker to build with.

        if self.knowledge.can_afford(self.unit_type) and worker.distance_to(position) < 5:
            if not self.exact:
                self.position = await self.ai.find_placement(self.unit_type, self.position, 20)
                position = self.position

            if position is not None:
                self.print(f'Building {self.unit_type.name} to {position}')
                self.do(worker.build(self.unit_type, position))
                self.set_worker(worker)
            else:
                self.print(f'Could not build {self.unit_type.name} to {position}')
        else:
            unit = self.ai._game_data.units[self.unit_type.value]
            cost = self.ai._game_data.calculate_ability_cost(unit.creation_ability)

            d = worker.distance_to(position)
            time = d / worker.movement_speed
            if self.ai.minerals - self.knowledge.reserved_minerals > (cost.minerals - 10 * time) \
                    and self.ai.vespene - self.knowledge.reserved_gas > (cost.vespene - time):

                if worker is not None:
                    self.set_worker(worker)
                    self.do(worker.move(position))

            self.knowledge.reserve(cost.minerals, cost.vespene)

        return False

    def set_worker(self, worker: Unit):
        self.knowledge.roles.set_task(UnitTask.Building, worker)
        self.builder_tag = worker.tag

    def get_worker(self, position: Point2):
        worker: Unit = None
        if self.builder_tag is None:
            free_workers = self.knowledge.roles.free_workers
            if free_workers.exists:
                worker = free_workers.closest_to(position)
        else:
            worker: Unit = self.ai.workers.find_by_tag(self.builder_tag)
            if worker is None or worker.is_constructing_scv:
                # Worker is probably dead or it is already building something else.
                self.builder_tag = None
        return worker
