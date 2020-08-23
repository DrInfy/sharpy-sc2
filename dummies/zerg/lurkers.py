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
                Step(None, BuildGas(2), skip=Gas(200), skip_until=Supply(25, supply_type=SupplyType.Workers),),
                Step(None, BuildGas(3), skip=Gas(200), skip_until=Supply(40, supply_type=SupplyType.Workers),),
                Step(None, BuildGas(4), skip=Gas(200), skip_until=Supply(50, supply_type=SupplyType.Workers),),
                Step(
                    Minerals(1000), BuildGas(6), skip=Gas(200), skip_until=Supply(50, supply_type=SupplyType.Workers),
                ),
                Step(
                    Minerals(2000), BuildGas(8), skip=Gas(200), skip_until=Supply(50, supply_type=SupplyType.Workers),
                ),
            ]
        )

        heavy_gas = SequentialList(
            [
                Step(None, BuildGas(2), skip=Gas(300), skip_until=Supply(20, supply_type=SupplyType.Workers),),
                Step(None, BuildGas(3), skip=Gas(300), skip_until=Supply(30, supply_type=SupplyType.Workers),),
                Step(None, BuildGas(4), skip=Gas(300), skip_until=Supply(40, supply_type=SupplyType.Workers),),
                Step(None, BuildGas(5), skip=Gas(300), skip_until=Supply(50, supply_type=SupplyType.Workers),),
                Step(None, BuildGas(6), skip=Gas(300), skip_until=Supply(60, supply_type=SupplyType.Workers),),
                Step(None, BuildGas(7), skip=Gas(300), skip_until=Supply(65, supply_type=SupplyType.Workers),),
                Step(None, BuildGas(8), skip=Gas(300), skip_until=Supply(70, supply_type=SupplyType.Workers),),
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
                Step(Supply(16), Expand(2)),
                Step(Supply(18), PositionBuilding(UnitTypeId.SPAWNINGPOOL, DefensePosition.BehindMineralLineLeft, 0),),
                StepBuildGas(1, Supply(20)),
                ActUnit(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 4),
                ZergUnit(UnitTypeId.QUEEN, 2),
                Step(self.build_workers, None, skip=Time(8 * 60)),
                Step(Time(3 * 60), Expand(3)),
                ZergUnit(UnitTypeId.QUEEN, 4),
                Step(Supply(40, SupplyType.Workers), Expand(4)),
            ),
            SequentialList(
                # Workers
                ZergUnit(UnitTypeId.DRONE, 20),
                Step(self.build_workers, ZergUnit(UnitTypeId.DRONE, 80), skip=self.max_workers_reached),
            ),
            Step(Gas(90), Tech(UpgradeId.ZERGLINGMOVEMENTSPEED)),
            SequentialList(
                [
                    Step(UnitReady(UnitTypeId.ROACHWARREN), gas, skip=UnitReady(UnitTypeId.HYDRALISKDEN)),
                    Step(UnitReady(UnitTypeId.HYDRALISKDEN), heavy_gas),
                ]
            ),
            SequentialList(
                Step(RequireCustom(lambda k: k.enemy_units_manager.enemy_cloak_trigger), MorphLair()),
                Step(UnitReady(UnitTypeId.LAIR), MorphOverseer(2)),
            ),
            SequentialList(
                # Tech
                Step(
                    UnitReady(UnitTypeId.SPAWNINGPOOL),
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
                    Step(None, RoachesAndHydrasAndLurkers(), skip_until=UnitReady(UnitTypeId.LURKERDENMP)),
                    Step(None, LingsAndRoachesAndHydras(), skip_until=UnitReady(UnitTypeId.HYDRALISKDEN)),
                    Step(None, LingsAndRoaches(), skip_until=UnitReady(UnitTypeId.ROACHWARREN)),
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
            if townhall.is_ready:
                count += townhall.ideal_harvesters
            else:
                count += 8
        for gas in self.ai.gas_buildings:  # type: Unit
            if gas.is_ready:
                count += gas.ideal_harvesters
            else:
                count += 3

        if self.ai.supply_workers >= count:
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
                Step(None, LingScout(), skip_until=Time(4 * 60)),
                Step(None, LingScout(), skip_until=Time(8 * 60)),
                PlanCancelBuilding(),
                PlanZoneGather(),
                Step(None, WorkerScout(), skip_until=Supply(20)),
                SpreadCreep(),
                InjectLarva(),
                DistributeWorkers(),
                PlanZoneAttack(),
                PlanFinishEnemy(),
            ),
        )


class LadderBot(LurkerBot):
    @property
    def my_race(self):
        return Race.Zerg
