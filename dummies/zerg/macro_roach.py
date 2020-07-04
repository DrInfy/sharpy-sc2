from sharpy.knowledges import KnowledgeBot
from sharpy.plans.acts import *
from sharpy.plans.acts.zerg import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans.tactics.zerg import *
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sc2 import BotAI, UnitTypeId, Race
from sc2.ids.upgrade_id import UpgradeId


class MacroRoach(KnowledgeBot):
    def __init__(self):
        super().__init__("200 roach")

    async def create_plan(self) -> BuildOrder:
        build_steps_exps = [
            Step(None, Expand(2)),
            Step(UnitReady(UnitTypeId.SPAWNINGPOOL, 1), Expand(3)),
            Step(Supply(80), MorphLair()),
            Expand(4),
            Step(Supply(100), ActBuilding(UnitTypeId.EVOLUTIONCHAMBER, 2)),
        ]

        bsus = [
            Step(UnitReady(UnitTypeId.LAIR, 1), None),
            Step(UnitExists(UnitTypeId.ROACHWARREN, 1), Tech(UpgradeId.GLIALRECONSTITUTION)),
        ]

        bsu = [
            Step(UnitExists(UnitTypeId.EVOLUTIONCHAMBER, 1), Tech(UpgradeId.ZERGMISSILEWEAPONSLEVEL1)),
            Step(None, Tech(UpgradeId.ZERGGROUNDARMORSLEVEL1)),
            Step(None, Tech(UpgradeId.ZERGMISSILEWEAPONSLEVEL2)),
            Step(None, Tech(UpgradeId.ZERGGROUNDARMORSLEVEL2)),
        ]

        buildings = [
            Step(UnitExists(UnitTypeId.HATCHERY, 2, include_pending=True), ActBuilding(UnitTypeId.SPAWNINGPOOL, 1),),
            Step(UnitExists(UnitTypeId.QUEEN, 2), ActBuilding(UnitTypeId.ROACHWARREN, 1)),
        ]

        extractors = [
            StepBuildGas(1, UnitReady(UnitTypeId.SPAWNINGPOOL, 0.5)),
            StepBuildGas(2, UnitReady(UnitTypeId.ROACHWARREN, 1)),
            StepBuildGas(3, UnitExists(UnitTypeId.HATCHERY, 3)),
            StepBuildGas(4, UnitReady(UnitTypeId.HATCHERY, 3)),
            StepBuildGas(5, UnitExists(UnitTypeId.OVERLORD, 10)),
            StepBuildGas(6, UnitExists(UnitTypeId.OVERLORD, 20)),
        ]

        # 6 zerglings for early defence... needs fiery micro
        build_steps_units_early_defense = [
            Step(UnitExists(UnitTypeId.SPAWNINGPOOL, 1), ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 2)),
            Step(UnitExists(UnitTypeId.HATCHERY, 2), ActUnitOnce(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 6)),
            Step(
                UnitExists(UnitTypeId.HATCHERY, 2, include_pending=True),
                ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 3),
            ),
            Step(
                UnitExists(UnitTypeId.HATCHERY, 3, include_pending=True),
                ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 4),
            ),
        ]
        # Add the roaches to here
        build_steps_units = [
            Step(UnitExists(UnitTypeId.HATCHERY, 2), ActUnit(UnitTypeId.ROACH, UnitTypeId.LARVA, 4)),
            Step(None, ActUnit(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 4)),
            Step(
                UnitExists(UnitTypeId.HATCHERY, 3, include_pending=True), ActUnit(UnitTypeId.ROACH, UnitTypeId.LARVA),
            ),
        ]

        ravagers = [
            Step(UnitReady(UnitTypeId.ROACH, 4), None),
            Step(UnitReady(UnitTypeId.ROACHWARREN, 1), MorphRavager(5), skip_until=Gas(200)),
            Step(UnitReady(UnitTypeId.ROACH, 10), MorphRavager(50), skip_until=Gas(300)),
        ]

        build = BuildOrder(
            ZergUnit(UnitTypeId.DRONE, 70),
            AutoOverLord(),
            build_steps_exps,
            buildings,
            extractors,
            build_steps_units_early_defense,
            bsu,
            bsus,
            ravagers,
            build_steps_units,
        )

        attack = PlanZoneAttack(120)

        tactics = [
            PlanCancelBuilding(),
            SpreadCreep(),
            InjectLarva(),
            DistributeWorkers(),
            PlanZoneDefense(),
            PlanZoneGather(),
            attack,
            PlanFinishEnemy(),
        ]

        return BuildOrder(build, tactics)


class LadderBot(MacroRoach):
    @property
    def my_race(self):
        return Race.Zerg
