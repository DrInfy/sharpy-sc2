import sc2
from sharpy.plans.acts import ActBase
from sharpy.plans.require import RequireBase
from sc2 import UnitTypeId, BotAI, Race
from sc2.constants import ALL_GAS
from sc2.unit import Unit
from sharpy.knowledges import Knowledge


class StepBuildGas(ActBase):
    """Builds a new gas mining facility closest to vespene geyser with closest worker"""

    def __init__(self, to_count: int, requirement=None, skip=None):
        assert to_count is not None and isinstance(to_count, int)

        assert requirement is None or isinstance(requirement, RequireBase)
        assert skip is None or isinstance(skip, RequireBase)

        super().__init__()

        self.requirement: RequireBase = requirement
        self.skip: RequireBase = skip

        self.to_count = to_count
        self.best_gas: Unit = None
        self.knowledge: Knowledge = None
        self.ai: BotAI = None
        self.all_types = ALL_GAS
        self.unit_type: UnitTypeId = None

    async def debug_draw(self):
        if self.requirement is not None:
            await self.requirement.debug_draw()
        if self.skip is not None:
            await self.skip.debug_draw()

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)

        self.unit_type = sc2.race_gas.get(knowledge.my_race)

        if self.requirement is not None and hasattr(self.requirement, "start"):
            await self.requirement.start(knowledge)
        if self.skip is not None and hasattr(self.skip, "start"):
            await self.skip.start(knowledge)

    @property
    def active_harvester_count(self):
        def harvester_is_active(harvester: Unit) -> bool:
            if harvester.vespene_contents > 100 or not harvester.is_ready:
                return True
            return False

        active_harvesters = self.ai.gas_buildings.filter(harvester_is_active)
        count = self.pending_build(self.unit_type)
        return len(active_harvesters) + count

    async def is_done(self):
        active_harvester_count = self.active_harvester_count
        unit: Unit

        harvesters_own = self.ai.gas_buildings

        # We have more than requested amount of harvesters
        if active_harvester_count > self.to_count:
            return True
        # If harvester has just finished, we need to move the worker away from it, thus delaying done.
        delayed = False
        if active_harvester_count == self.to_count:
            for unit in harvesters_own.not_ready:
                if unit.build_progress < 0.05:
                    delayed = True
            if not delayed:
                return True

        # No point in building harvester in somewhere with less than 50 gas left
        best_score = 50
        self.best_gas = None
        harvesters: list = []
        for unit in self.ai.all_units:
            # We need to check for all races, in case gas was stolen in order to not break here
            if unit.type_id in self.all_types:
                harvesters.append(unit)

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
                    score = geyser.vespene_contents
                    if score > best_score:
                        self.best_gas = geyser

        return self.best_gas is None and not delayed

    async def ready(self):
        if self.requirement is None:
            return True
        return self.requirement.check()

    async def execute(self) -> bool:
        # External check prevents us from building harvesters
        if self.skip is not None and self.skip.check():
            return True
        if self.requirement is not None and not self.requirement.check():
            return False

        if await self.is_done():
            return True

        workers = self.knowledge.roles.free_workers

        should_build = self.active_harvester_count < self.to_count
        can_build = workers.exists and self.knowledge.can_afford(self.unit_type)

        if self.best_gas is not None and should_build and can_build:
            target = self.best_gas
            worker = workers.closest_to(target.position)
            self.ai.do(worker.build_gas(target))

            if self.ai.race == Race.Protoss:
                # Protoss only do something else after starting gas
                mf = self.ai.mineral_field.closest_to(worker)
                self.ai.do(worker.gather(mf, queue=True))

            self.knowledge.print(f'Building {self.unit_type.name} to {target.position}')
        return False
