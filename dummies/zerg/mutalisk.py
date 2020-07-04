from sharpy.plans.acts import *
from sharpy.plans.acts.zerg import *
from sharpy.plans.require import *
from sharpy.plans.require.supply import SupplyType
from sharpy.plans.tactics import *
from sharpy.plans.tactics.zerg import *
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sc2 import UnitTypeId, Race
from sc2.ids.upgrade_id import UpgradeId

from sharpy.knowledges import KnowledgeBot


class MutaliskBuild(BuildOrder):
    def __init__(self):

        gas_related = [
            StepBuildGas(1, UnitExists(UnitTypeId.HATCHERY, 2)),
            Step(None, Tech(UpgradeId.ZERGLINGMOVEMENTSPEED), skip_until=Gas(100)),
            Step(None, ActBuilding(UnitTypeId.ROACHWARREN, 1), skip_until=Gas(100)),
            StepBuildGas(2, Time(4 * 60)),
            StepBuildGas(3, UnitExists(UnitTypeId.LAIR, 1)),
            StepBuildGas(5, None, Gas(100)),
            StepBuildGas(8, Supply(50, supply_type=SupplyType.Workers)),
        ]
        buildings = [
            Step(UnitExists(UnitTypeId.DRONE, 14), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 2)),
            Step(Supply(16), Expand(2)),
            Step(UnitExists(UnitTypeId.EXTRACTOR, 1), ActBuilding(UnitTypeId.SPAWNINGPOOL, 1)),
            Step(
                None,
                ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 2),
                skip_until=UnitExists(UnitTypeId.SPAWNINGPOOL, 1),
            ),
            Step(
                UnitReady(UnitTypeId.SPAWNINGPOOL),
                DefensiveBuilding(UnitTypeId.SPINECRAWLER, DefensePosition.Entrance, 1),
            ),
            # Step(UnitExists(UnitTypeId.DRONE, 24, include_killed=True, include_pending=True), ActExpand(3)),
            Step(None, MorphLair(), skip=UnitExists(UnitTypeId.HIVE, 1)),
            Step(UnitExists(UnitTypeId.DRONE, 30, include_killed=True), Expand(3)),
            Step(None, ZergUnit(UnitTypeId.QUEEN, 3)),
            Step(UnitExists(UnitTypeId.LAIR, 1), ActBuilding(UnitTypeId.SPIRE, 1)),
            MorphOverseer(1),
            Step(None, ZergUnit(UnitTypeId.QUEEN, 5)),
            Step(UnitExists(UnitTypeId.SPIRE), Expand(4)),
            Tech(UpgradeId.ZERGFLYERWEAPONSLEVEL1),
            Step(UnitExists(UnitTypeId.MUTALISK, 10, include_killed=True), ActBuilding(UnitTypeId.INFESTATIONPIT)),
            Step(UnitReady(UnitTypeId.INFESTATIONPIT), MorphHive()),
            MorphGreaterSpire(),
            Tech(UpgradeId.ZERGFLYERWEAPONSLEVEL2),
            Tech(UpgradeId.ZERGFLYERWEAPONSLEVEL3),
        ]

        high_tier = [
            # Step(RequiredUnitReady(UnitTypeId.GREATERSPIRE), ZergUnit(UnitTypeId.DRONE, 70)),
            Step(
                None, ZergUnit(UnitTypeId.CORRUPTOR, 3, priority=True), skip_until=UnitReady(UnitTypeId.GREATERSPIRE),
            ),
            Step(None, MorphBroodLord(5)),
            # Step(RequiredGas(200), ZergUnit(UnitTypeId.MUTALISK, 20, priority=True))
        ]

        units = [
            Step(UnitExists(UnitTypeId.HATCHERY, 1), None),
            Step(None, ZergUnit(UnitTypeId.DRONE, 20)),
            # Early zerglings
            Step(UnitExists(UnitTypeId.SPAWNINGPOOL, 1), ZergUnit(UnitTypeId.ZERGLING, 4), None),
            Step(None, ZergUnit(UnitTypeId.DRONE, 25)),
            Step(UnitExists(UnitTypeId.SPAWNINGPOOL, 1), ZergUnit(UnitTypeId.ZERGLING, 12), None),
            # Queen for more larvae
            Step(None, ZergUnit(UnitTypeId.QUEEN, 1)),
            Step(None, ZergUnit(UnitTypeId.DRONE, 30), None),
            Step(None, ZergUnit(UnitTypeId.ZERGLING, 16, only_once=True), None),
            Step(None, ZergUnit(UnitTypeId.ROACH, 4, only_once=True), skip_until=Gas(25)),
            Step(None, ZergUnit(UnitTypeId.MUTALISK, 4), skip_until=UnitReady(UnitTypeId.SPIRE, 1)),
            Step(None, ZergUnit(UnitTypeId.DRONE, 45), None),
            Step(None, ActUnitOnce(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 16), None),
            Step(None, ZergUnit(UnitTypeId.ROACH, 10), skip=UnitReady(UnitTypeId.SPIRE, 1), skip_until=Gas(25),),
            Step(None, ZergUnit(UnitTypeId.DRONE, 65), None),
            Step(
                None,
                ZergUnit(UnitTypeId.ZERGLING, 40),
                skip_until=All([UnitReady(UnitTypeId.SPIRE, 1), Minerals(300)]),
            ),
            Step(None, ActUnit(UnitTypeId.ROACH, UnitTypeId.LARVA), skip=UnitReady(UnitTypeId.SPIRE, 1)),
            Step(
                None,
                ZergUnit(UnitTypeId.ZERGLING, 100),
                skip_until=All([UnitReady(UnitTypeId.SPIRE, 1), Minerals(500)]),
            ),
            # Endless mutalisks
            Step(None, ActUnit(UnitTypeId.MUTALISK, UnitTypeId.LARVA), None),
        ]
        super().__init__([self.overlords, buildings, gas_related, high_tier, units])


class MutaliskBot(KnowledgeBot):
    """Zerg macro opener into longer game mass mutalisks and later builds broodlords."""

    def __init__(self):
        super().__init__("Blunt Flies")

    async def create_plan(self) -> BuildOrder:
        worker_scout = Step(
            None,
            WorkerScout(),
            skip=RequireCustom(lambda k: len(self.enemy_start_locations) == 1),
            skip_until=Supply(20),
        )
        distribute = DistributeWorkers()

        return BuildOrder(
            MutaliskBuild(),
            SequentialList(
                PlanCancelBuilding(),
                PlanZoneGather(),
                PlanZoneDefense(),
                worker_scout,
                SpreadCreep(),
                InjectLarva(),
                distribute,
                PlanZoneAttack(),
                PlanFinishEnemy(),
            ),
        )


class LadderBot(MutaliskBot):
    @property
    def my_race(self):
        return Race.Zerg
