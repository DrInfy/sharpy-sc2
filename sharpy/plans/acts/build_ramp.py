from sharpy.plans.acts import ActBuilding
from sc2 import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit

from sharpy.general.extended_ramp import ExtendedRamp, RampPosition

# Build a building on a ramp
from sharpy.managers.roles import UnitTask


class ActBuildingRamp(ActBuilding):
    def __init__(self, name: UnitTypeId, to_count: int, position: RampPosition):
        assert position is not None and isinstance(position, RampPosition)

        self.position = position
        self.builder_tag: int = None
        super().__init__(name, to_count)

    async def execute(self) -> bool:
        count = self.get_count(self.unit_type)

        if count >= self.to_count:
            if self.builder_tag is not None:
                self.knowledge.roles.clear_task(self.builder_tag)
                self.builder_tag = None

            return True  # Step is done

        ramp: ExtendedRamp = self.knowledge.base_ramp
        position = ramp.positions[self.position]

        worker = self.get_worker(position)
        if worker is None:
            return True # No worker to build with.

        if self.knowledge.can_afford(self.unit_type):
            self.print(f'Building {self.unit_type.name} to {position}')
            # await ai.build(self.name, position, max_distance=0) # For debugging only, too risky to use in live matches!
            self.do(worker.build(self.unit_type, position))
        else:
            unit = self.ai._game_data.units[self.unit_type.value]
            cost = self.ai._game_data.calculate_ability_cost(unit.creation_ability)

            d = worker.distance_to(position)
            time = d / worker.movement_speed
            if self.ai.minerals - self.knowledge.reserved_minerals > (cost.minerals - 10 * time) \
                    and self.ai.vespene - self.knowledge.reserved_gas > (cost.vespene - time):

                if worker is not None:
                    self.do(worker.move(position))

            self.knowledge.reserve(cost.minerals, cost.vespene)

        return False

    def get_worker(self, position: Point2):
        worker: Unit = None
        if self.builder_tag is None:
            free_workers = self.knowledge.roles.free_workers
            if free_workers.exists:
                worker = free_workers.closest_to(position)
                self.knowledge.roles.set_task(UnitTask.Building, worker)
                self.builder_tag = worker.tag
        else:
            worker: Unit = self.ai.workers.find_by_tag(self.builder_tag)
            if worker is None or worker.is_constructing_scv:
                # Worker is probably dead or it is already building something else.
                self.builder_tag = None
        return worker

    def print(self, msg):
        self.knowledge.print(f"[ActBuildingRamp] {msg}")
