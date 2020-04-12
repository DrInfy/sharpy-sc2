from typing import Union, Callable, List

from sc2 import UnitTypeId, Race
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit
from sharpy.knowledges import KnowledgeBot, Knowledge
from sharpy.plans.zerg import *


class LingsAndRoaches(BuildOrder):
    def __init__(self):
        self.roaches = ZergUnit(UnitTypeId.ROACH, priority=True)
        self.lings = ZergUnit(UnitTypeId.ZERGLING)
        super().__init__(self.roaches, self.lings)

    async def execute(self) -> bool:
        self.roaches.to_count = self.get_count(UnitTypeId.ZERGLING) / 2
        return await super().execute()


class LingsAndRoachesAndHydras(BuildOrder):
    def __init__(self):

        self.hydras = ZergUnit(UnitTypeId.HYDRALISK, priority=True)
        self.roaches = ZergUnit(UnitTypeId.ROACH, priority=True)
        self.lings = ZergUnit(UnitTypeId.ZERGLING)
        super().__init__(self.hydras, self.roaches, self.lings)

    async def execute(self) -> bool:
        self.hydras.to_count = self.get_count(UnitTypeId.ROACH) + 2
        self.roaches.to_count = self.get_count(UnitTypeId.ZERGLING) / 2
        return await super().execute()


class RoachesAndHydrasAndLurkers(BuildOrder):
    def __init__(self):
        self.lurkers = ZergUnit(UnitTypeId.LURKERMP, priority=True)
        self.hydras = ZergUnit(UnitTypeId.HYDRALISK, priority=True)
        self.roaches = ZergUnit(UnitTypeId.ROACH)

        super().__init__(self.lurkers, self.hydras, self.roaches)

    async def execute(self) -> bool:
        self.lurkers.to_count = self.get_count(UnitTypeId.HYDRALISK) / 3 + 1
        self.hydras.to_count = self.get_count(UnitTypeId.ROACH) + 1
        return await super().execute()


class LurkerBuild(BuildOrder):
    def __init__(self):
        gas = SequentialList(
            [
                Step(
                    None,
                    StepBuildGas(2),
                    skip=RequiredGas(200),
                    skip_until=RequiredSupply(25, supply_type=SupplyType.Workers),
                ),
                Step(
                    None,
                    StepBuildGas(3),
                    skip=RequiredGas(200),
                    skip_until=RequiredSupply(40, supply_type=SupplyType.Workers),
                ),
                Step(
                    None,
                    StepBuildGas(4),
                    skip=RequiredGas(200),
                    skip_until=RequiredSupply(50, supply_type=SupplyType.Workers),
                ),
                Step(
                    RequiredMinerals(1000),
                    StepBuildGas(6),
                    skip=RequiredGas(200),
                    skip_until=RequiredSupply(50, supply_type=SupplyType.Workers),
                ),
                Step(
                    RequiredMinerals(2000),
                    StepBuildGas(8),
                    skip=RequiredGas(200),
                    skip_until=RequiredSupply(50, supply_type=SupplyType.Workers),
                ),
            ]
        )

        heavy_gas = SequentialList(
            [
                Step(
                    None,
                    StepBuildGas(2),
                    skip=RequiredGas(300),
                    skip_until=RequiredSupply(20, supply_type=SupplyType.Workers),
                ),
                Step(
                    None,
                    StepBuildGas(3),
                    skip=RequiredGas(300),
                    skip_until=RequiredSupply(30, supply_type=SupplyType.Workers),
                ),
                Step(
                    None,
                    StepBuildGas(4),
                    skip=RequiredGas(300),
                    skip_until=RequiredSupply(40, supply_type=SupplyType.Workers),
                ),
                Step(
                    None,
                    StepBuildGas(5),
                    skip=RequiredGas(300),
                    skip_until=RequiredSupply(50, supply_type=SupplyType.Workers),
                ),
                Step(
                    None,
                    StepBuildGas(6),
                    skip=RequiredGas(300),
                    skip_until=RequiredSupply(60, supply_type=SupplyType.Workers),
                ),
                Step(
                    None,
                    StepBuildGas(7),
                    skip=RequiredGas(300),
                    skip_until=RequiredSupply(65, supply_type=SupplyType.Workers),
                ),
                Step(
                    None,
                    StepBuildGas(8),
                    skip=RequiredGas(300),
                    skip_until=RequiredSupply(70, supply_type=SupplyType.Workers),
                ),
            ]
        )

        super().__init__(
            SequentialList(
                # Overlords
                Step(UnitExists(UnitTypeId.DRONE, 13), ZergUnit(UnitTypeId.OVERLORD, 2, priority=True)),
                AutoOverLord(),
            ),
            SequentialList(
                # Opener
                Step(RequiredSupply(16), ActExpand(2)),
                Step(
                    RequiredSupply(18),
                    PositionBuilding(UnitTypeId.SPAWNINGPOOL, DefensePosition.BehindMineralLineLeft, 0),
                ),
                StepBuildGas(1, RequiredSupply(20)),
                ActUnit(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 4),
                ZergUnit(UnitTypeId.QUEEN, 2),
                Step(self.build_workers, None, skip=RequiredTime(8 * 60)),
                Step(RequiredTime(3 * 60), ActExpand(3)),
                ZergUnit(UnitTypeId.QUEEN, 4),
                Step(RequiredSupply(40, SupplyType.Workers), ActExpand(4)),
            ),
            SequentialList(
                # Workers
                ZergUnit(UnitTypeId.DRONE, 20),
                Step(self.build_workers, ZergUnit(UnitTypeId.DRONE, 80), skip=self.max_workers_reached),
            ),
            Step(RequiredGas(90), ActTech(UpgradeId.ZERGLINGMOVEMENTSPEED)),
            SequentialList(
                [
                    Step(
                        RequiredUnitReady(UnitTypeId.ROACHWARREN), gas, skip=RequiredUnitReady(UnitTypeId.HYDRALISKDEN)
                    ),
                    Step(RequiredUnitReady(UnitTypeId.HYDRALISKDEN), heavy_gas),
                ]
            ),
            SequentialList(
                Step(RequireCustom(lambda k: k.enemy_units_manager.enemy_cloak_trigger), MorphLair()),
                Step(RequiredUnitReady(UnitTypeId.LAIR), MorphOverseer(2)),
            ),
            SequentialList(
                # Tech
                Step(
                    RequiredUnitReady(UnitTypeId.SPAWNINGPOOL),
                    PositionBuilding(UnitTypeId.ROACHWARREN, DefensePosition.BehindMineralLineRight, 0),
                ),
                MorphLair(),
                ActBuilding(UnitTypeId.HYDRALISKDEN),
                ActBuilding(UnitTypeId.LURKERDENMP),
            ),
            Step(
                None,
                SequentialList(
                    # Units
                    Step(None, RoachesAndHydrasAndLurkers(), skip_until=RequiredUnitReady(UnitTypeId.LURKERDENMP)),
                    Step(None, LingsAndRoachesAndHydras(), skip_until=RequiredUnitReady(UnitTypeId.HYDRALISKDEN)),
                    Step(None, LingsAndRoaches(), skip_until=RequiredUnitReady(UnitTypeId.ROACHWARREN)),
                    ZergUnit(UnitTypeId.ZERGLING),
                ),
            ),
        )

    def build_workers(self, knowledge: Knowledge) -> bool:
        for zone in knowledge.zone_manager.expansion_zones:
            if zone.is_ours and zone.is_under_attack:
                return False

        return knowledge.game_analyzer.army_can_survive

    def max_workers_reached(self, knowledge: Knowledge) -> bool:
        count = 1
        for townhall in self.ai.townhalls:  # type: Unit
            count += townhall.ideal_harvesters
        for gas in self.ai.gas_buildings:  # type: Unit
            count += gas.ideal_harvesters

        if len(knowledge.unit_cache.own(UnitTypeId.DRONE)) >= count:
            return True

        return False


class LurkerBot(KnowledgeBot):
    def __init__(self):
        super().__init__("Blunt Lurkers")

    async def create_plan(self) -> BuildOrder:
        return BuildOrder(
            CounterTerranTie([LurkerBuild()]),
            SequentialList(
                PlanZoneDefense(),
                OverlordScout(),
                Step(None, LingScoutMain(), skip_until=RequiredTime(4 * 60)),
                Step(None, LingScoutMain(), skip_until=RequiredTime(8 * 60)),
                PlanCancelBuilding(),
                PlanZoneGather(),
                Step(None, WorkerScout(), skip_until=RequiredSupply(20)),
                SpreadCreep(),
                InjectLarva(),
                PlanDistributeWorkers(),
                PlanZoneAttack(),
                PlanFinishEnemy(),
            ),
        )


class LadderBot(LurkerBot):
    @property
    def my_race(self):
        return Race.Zerg
