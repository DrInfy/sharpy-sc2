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
            Step(None, ActExpand(2)),
            Step(RequiredUnitReady(UnitTypeId.SPAWNINGPOOL, 1), ActExpand(3)),
            Step(RequiredSupply(80), MorphLair()),
            ActExpand(4),
            Step(RequiredSupply(100), ActBuilding(UnitTypeId.EVOLUTIONCHAMBER, 2)),
        ]

        bsus = [
            Step(RequiredUnitReady(UnitTypeId.LAIR, 1), None),
            Step(RequiredUnitExists(UnitTypeId.ROACHWARREN, 1),
                 ActTech(UpgradeId.GLIALRECONSTITUTION)),
        ]

        bsu = [
            Step(RequiredUnitExists(UnitTypeId.EVOLUTIONCHAMBER, 1),
                 ActTech(UpgradeId.ZERGMISSILEWEAPONSLEVEL1)),
            Step(None, ActTech(UpgradeId.ZERGGROUNDARMORSLEVEL1)),
            Step(None, ActTech(UpgradeId.ZERGMISSILEWEAPONSLEVEL2)),
            Step(None, ActTech(UpgradeId.ZERGGROUNDARMORSLEVEL2)),
        ]

        buildings = [
            Step(RequiredUnitExists(UnitTypeId.HATCHERY, 2, include_pending=True),
                 ActBuilding(UnitTypeId.SPAWNINGPOOL, 1)),
            Step(RequiredUnitExists(UnitTypeId.QUEEN, 2), ActBuilding(UnitTypeId.ROACHWARREN, 1)),
        ]

        extractors = [
            StepBuildGas(1, RequiredUnitReady(UnitTypeId.SPAWNINGPOOL, 0.5)),
            StepBuildGas(2, RequiredUnitReady(UnitTypeId.ROACHWARREN, 1)),
            StepBuildGas(3, RequiredUnitExists(UnitTypeId.HATCHERY, 3)),
            StepBuildGas(4, RequiredUnitReady(UnitTypeId.HATCHERY, 3)),
            StepBuildGas(5, RequiredUnitExists(UnitTypeId.OVERLORD, 10)),
            StepBuildGas(6, RequiredUnitExists(UnitTypeId.OVERLORD, 20)),
        ]

        # 6 zerglings for early defence... needs fiery micro
        build_steps_units_early_defense = [
            Step(RequiredUnitExists(UnitTypeId.SPAWNINGPOOL, 1), ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 2)),
            Step(RequiredUnitExists(UnitTypeId.HATCHERY, 2), ActUnitOnce(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 6)),
            Step(RequiredUnitExists(UnitTypeId.HATCHERY, 2, include_pending=True),
                 ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 3)),
            Step(RequiredUnitExists(UnitTypeId.HATCHERY, 3, include_pending=True),
                 ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 4)),
        ]
        # Add the roaches to here
        build_steps_units = [
            Step(RequiredUnitExists(UnitTypeId.HATCHERY, 2), ActUnit(UnitTypeId.ROACH, UnitTypeId.LARVA, 4)),
            Step(None, ActUnit(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 4)),
            Step(RequiredUnitExists(UnitTypeId.HATCHERY, 3, include_pending=True),
                 ActUnit(UnitTypeId.ROACH, UnitTypeId.LARVA))
        ]

        ravagers = [
            Step(RequiredUnitReady(UnitTypeId.ROACH, 4), None),
            Step(RequiredUnitReady(UnitTypeId.ROACHWARREN, 1), MorphRavager(5), skip_until=RequiredGas(200)),
            Step(RequiredUnitReady(UnitTypeId.ROACH, 10), MorphRavager(50), skip_until=RequiredGas(300))
        ]

        build = BuildOrder([
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
        ])

        attack = PlanZoneAttack(120)

        tactics = [
            PlanCancelBuilding(),
            SpreadCreep(),
            InjectLarva(),
            PlanDistributeWorkers(),
            PlanZoneDefense(),
            PlanZoneGather(),
            attack,
            PlanFinishEnemy(),
        ]

        return BuildOrder([
            build,
            tactics
        ])


class LadderBot(MacroRoach):
    @property
    def my_race(self):
        return Race.Zerg
