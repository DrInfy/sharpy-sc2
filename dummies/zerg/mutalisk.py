from sharpy.plans.acts import *
from sharpy.plans.acts.zerg import *
from sharpy.plans.require import *
from sharpy.plans.require.required_supply import SupplyType
from sharpy.plans.tactics import *
from sharpy.plans.tactics.zerg import *
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sc2 import UnitTypeId, Race
from sc2.ids.upgrade_id import UpgradeId

from sharpy.knowledges import KnowledgeBot


class MutaliskBuild(BuildOrder):
    def __init__(self):

        gas_related = [
            StepBuildGas(1, RequiredUnitExists(UnitTypeId.HATCHERY, 2)),
            Step(None, ActTech(UpgradeId.ZERGLINGMOVEMENTSPEED), skip_until=RequiredGas(100)),
            Step(None, ActBuilding(UnitTypeId.ROACHWARREN, 1), skip_until=RequiredGas(100)),
            StepBuildGas(2, RequiredTime(4 * 60)),
            StepBuildGas(3, RequiredUnitExists(UnitTypeId.LAIR, 1)),
            StepBuildGas(5, None, RequiredGas(100)),
            StepBuildGas(8, RequiredSupply(50, supply_type=SupplyType.Workers)),
        ]
        buildings = [
            Step(RequiredUnitExists(UnitTypeId.DRONE, 14), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 2)),
            Step(RequiredSupply(16), ActExpand(2)),
            Step(RequiredUnitExists(UnitTypeId.EXTRACTOR, 1), ActBuilding(UnitTypeId.SPAWNINGPOOL, 1)),
            Step(None, ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 2), skip_until=RequiredUnitExists(UnitTypeId.SPAWNINGPOOL, 1)),

            Step(RequiredUnitReady(UnitTypeId.SPAWNINGPOOL),
                 DefensiveBuilding(UnitTypeId.SPINECRAWLER, DefensePosition.Entrance, 1)),

            # Step(RequiredUnitExists(UnitTypeId.DRONE, 24, include_killed=True, include_pending=True), ActExpand(3)),
            Step(None, MorphLair(), skip=RequiredUnitExists(UnitTypeId.HIVE, 1)),
            Step(RequiredUnitExists(UnitTypeId.DRONE, 30, include_killed=True), ActExpand(3)),
            Step(None, ZergUnit(UnitTypeId.QUEEN, 3)),
            Step(RequiredUnitExists(UnitTypeId.LAIR, 1), ActBuilding(UnitTypeId.SPIRE, 1)),
            MorphOverseer(1),
            Step(None, ZergUnit(UnitTypeId.QUEEN, 5)),
            Step(RequiredUnitExists(UnitTypeId.SPIRE), ActExpand(4)),
            ActTech(UpgradeId.ZERGFLYERWEAPONSLEVEL1),
            Step(RequiredUnitExists(UnitTypeId.MUTALISK, 10, include_killed=True), ActBuilding(UnitTypeId.INFESTATIONPIT)),
            Step(RequiredUnitReady(UnitTypeId.INFESTATIONPIT), MorphHive()),
            MorphGreaterSpire(),
            ActTech(UpgradeId.ZERGFLYERWEAPONSLEVEL2, UnitTypeId.GREATERSPIRE), # this can be researched from SPIRE as well.
            ActTech(UpgradeId.ZERGFLYERWEAPONSLEVEL3, UnitTypeId.GREATERSPIRE), # python-sc2 thinks this can be researched from SPIRE
        ]

        high_tier = [
            # Step(RequiredUnitReady(UnitTypeId.GREATERSPIRE), ZergUnit(UnitTypeId.DRONE, 70)),
            Step(None, ZergUnit(UnitTypeId.CORRUPTOR, 3, priority=True),
                 skip_until=RequiredUnitReady(UnitTypeId.GREATERSPIRE)),
            Step(None, MorphBroodLord(5)),
            # Step(RequiredGas(200), ZergUnit(UnitTypeId.MUTALISK, 20, priority=True))
        ]

        units = [
            Step(RequiredUnitExists(UnitTypeId.HATCHERY, 1), None),

            Step(None, ZergUnit(UnitTypeId.DRONE, 20)),

            # Early zerglings
            Step(RequiredUnitExists(UnitTypeId.SPAWNINGPOOL, 1), ZergUnit(UnitTypeId.ZERGLING, 4),
                 None),
            Step(None, ZergUnit(UnitTypeId.DRONE, 25)),
            Step(RequiredUnitExists(UnitTypeId.SPAWNINGPOOL, 1), ZergUnit(UnitTypeId.ZERGLING, 12),
                 None),
            # Queen for more larvae
            Step(None, ZergUnit(UnitTypeId.QUEEN, 1)),
            Step(None, ZergUnit(UnitTypeId.DRONE, 30), None),
            Step(None, ZergUnit(UnitTypeId.ZERGLING, 16, only_once=True), None),
            Step(None, ZergUnit(UnitTypeId.ROACH, 4, only_once=True), skip_until=RequiredGas(25)),

            Step(None, ZergUnit(UnitTypeId.MUTALISK, 4), skip_until=RequiredUnitReady(UnitTypeId.SPIRE, 1)),
            Step(None, ZergUnit(UnitTypeId.DRONE, 45), None),
            Step(None, ActUnitOnce(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 16), None),
            Step(None, ZergUnit(UnitTypeId.ROACH, 10), skip=RequiredUnitReady(UnitTypeId.SPIRE, 1),
                 skip_until=RequiredGas(25)),
            Step(None, ZergUnit(UnitTypeId.DRONE, 65), None),

            Step(None, ZergUnit(UnitTypeId.ZERGLING, 40),
                 skip_until=RequiredAll([RequiredUnitReady(UnitTypeId.SPIRE, 1), RequiredMinerals(300)])),
            Step(None, ActUnit(UnitTypeId.ROACH, UnitTypeId.LARVA), skip=RequiredUnitReady(UnitTypeId.SPIRE, 1)),

            Step(None, ZergUnit(UnitTypeId.ZERGLING, 100),
                 skip_until=RequiredAll([RequiredUnitReady(UnitTypeId.SPIRE, 1), RequiredMinerals(500)])),


            # Endless mutalisks
            Step(None, ActUnit(UnitTypeId.MUTALISK, UnitTypeId.LARVA), None)
        ]
        super().__init__([self.overlords, buildings, gas_related, high_tier, units])


class MutaliskBot(KnowledgeBot):
    """Zerg macro opener into longer game mass mutalisks and later builds broodlords."""

    def __init__(self):
        super().__init__("Blunt Flies")

    async def create_plan(self) -> BuildOrder:
        worker_scout = Step(None, WorkerScout(), skip=RequireCustom(
            lambda k: len(self.enemy_start_locations) == 1), skip_until=RequiredSupply(20))
        distribute = PlanDistributeWorkers()

        return BuildOrder([
            MutaliskBuild(),
            SequentialList([
                PlanCancelBuilding(),
                PlanZoneGather(),
                PlanZoneDefense(),
                worker_scout,
                SpreadCreep(),
                InjectLarva(),
                distribute,
                PlanZoneAttack(),
                PlanFinishEnemy()
            ]),
        ])


class LadderBot(MutaliskBot):
    @property
    def my_race(self):
        return Race.Zerg
