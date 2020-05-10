from typing import Optional

import sc2
from sharpy.managers.roles import UnitTask
from sharpy.plans.acts import ActBase
from sharpy.plans.require import RequireBase
from sc2 import UnitTypeId, BotAI, Race
from sc2.constants import ALL_GAS
from sc2.unit import Unit
from sharpy.knowledges import Knowledge


class BuildGas(ActBase):
    """Builds a new gas mining facility closest to vespene geyser with closest worker"""

    def __init__(self, to_count: int):
        assert to_count is not None and isinstance(to_count, int)

        super().__init__()

        self.to_count = to_count
        self.best_gas: Unit = None
        self.knowledge: Knowledge = None
        self.ai: BotAI = None
        self.all_types = ALL_GAS
        self.unit_type: UnitTypeId = None
        self.builder_tag: Optional[int] = None

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)

        self.unit_type = sc2.race_gas.get(knowledge.my_race)

    @property
    def active_harvester_count(self):
        def harvester_is_active(harvester: Unit) -> bool:
            if harvester.vespene_contents > 100 or not harvester.is_ready:
                return True
            return False

        active_harvesters = self.ai.gas_buildings.filter(harvester_is_active)
        return len(active_harvesters)

    def find_best(self):
        # No point in building harvester in somewhere with less than 50 gas left
        best_score = 50
        self.best_gas = None
        harvesters: list = []
        # We need to check for all races, in case gas was stolen in order to not break here
        harvesters.extend(self.cache.own(self.all_types))
        harvesters.extend(self.cache.enemy(self.all_types))

        for townhall in self.ai.townhalls:  # type: Unit
            if not townhall.is_ready or townhall.build_progress < 0.9:
                # Only build gas for bases that are almost finished
                continue

            for geyser in self.ai.vespene_geyser.closer_than(15, townhall):  # type: Unit
                exists = False
                for harvester in harvesters:  # type: Unit
                    if harvester.position.distance_to(geyser.position) <= 1:
                        exists = True
                        break
                if not exists:
                    score = geyser.vespene_contents - 0.01 * self.knowledge.own_main_zone.center_location.distance_to(
                        geyser
                    )
                    if score > best_score:
                        self.best_gas = geyser

    async def execute(self) -> bool:
        active_harvester_count = self.active_harvester_count
        pending_count = self.pending_build(self.unit_type)

        if active_harvester_count >= self.to_count:
            # All buildings have been started, we can safely exit now
            self.clear_worker()
            return True

        self.find_best()

        if self.best_gas is None:
            self.clear_worker()
            return False  # Cannot proceed

        worker = self.get_worker_builder(self.best_gas.position, self.builder_tag)

        if pending_count:
            self.set_worker(worker)
            return active_harvester_count + pending_count >= self.to_count

        if worker:
            return await self.build_gas(worker)
        return False

    def clear_worker(self):
        if self.builder_tag is not None:
            self.knowledge.roles.clear_task(self.builder_tag)
            self.builder_tag = None

    async def build_gas(self, worker: Unit):
        if self.best_gas is not None and self.knowledge.can_afford(self.unit_type):
            target = self.best_gas

            if not self.set_worker(worker):
                return False

            self.builder_tag = worker.tag

            cmd = worker.build_gas(target, queue=self.has_build_order(worker))
            self.do(cmd)

            if self.ai.race == Race.Protoss:
                # Protoss only do something else after starting gas
                mf = self.ai.mineral_field.closest_to(worker)
                self.ai.do(worker.gather(mf, queue=True))

            self.print(f"Building {self.unit_type.name} to {target.position}")
        return False

    def set_worker(self, worker: Optional[Unit]) -> bool:
        if worker:
            self.knowledge.roles.set_task(UnitTask.Building, worker)
            self.builder_tag = worker.tag
            return True

        self.builder_tag = None
        return False
