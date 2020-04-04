from sharpy.plans.acts import *
from sharpy.plans.acts.zerg import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans.tactics.zerg import *
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sharpy.knowledges import Knowledge, KnowledgeBot
from sc2 import BotAI, UnitTypeId
from sc2 import run_game, maps, Race, Difficulty
from sc2.ids.upgrade_id import UpgradeId


class MacroBuild(BuildOrder):
    def __init__(self):
        ultras = [
            Step(RequiredUnitExists(UnitTypeId.ULTRALISKCAVERN, 1), None),
            Step(RequiredGas(500), ActUnit(UnitTypeId.ULTRALISK, UnitTypeId.LARVA, priority=True)),
        ]

        units = [
            Step(None, ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 100), skip=RequiredUnitExists(UnitTypeId.HIVE, 1)),
            Step(None, ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 50)),
            Step(RequiredUnitExists(UnitTypeId.SPAWNINGPOOL, 1), ActUnit(UnitTypeId.ZERGLING, UnitTypeId.LARVA),
                 None)
        ]

        build_step_expansions = [
            Step(None, ActExpand(999)),
        ]

        queens = [
            Step(RequiredUnitExists(UnitTypeId.SPAWNINGPOOL, 1), None),
            Step(RequiredMinerals(500), ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 5)),
        ]

        pool_and_tech = [
            Step(None, ActBuilding(UnitTypeId.SPAWNINGPOOL, 1)),
            StepBuildGas(2, None),
            Step(None, ActTech(UpgradeId.ZERGLINGMOVEMENTSPEED)),
            Step(RequiredGas(120), ActBuilding(UnitTypeId.EVOLUTIONCHAMBER, 2)),

            Step(RequiredUnitExists(UnitTypeId.EVOLUTIONCHAMBER, 1),
                 ActTech(UpgradeId.ZERGMELEEWEAPONSLEVEL1)),
            Step(None, ActTech(UpgradeId.ZERGGROUNDARMORSLEVEL1)),
            Step(None, MorphLair(), skip=RequiredUnitExists(UnitTypeId.HIVE, 1)),
            StepBuildGas(4, None),
            Step(None, ActTech(UpgradeId.ZERGMELEEWEAPONSLEVEL2)),
            Step(None, ActTech(UpgradeId.ZERGGROUNDARMORSLEVEL2)),
            # Infestation pit required
            Step(None, ActBuilding(UnitTypeId.INFESTATIONPIT, 1)),
            Step(RequiredUnitReady(UnitTypeId.INFESTATIONPIT, 1), MorphHive()),

            Step(RequiredUnitReady(UnitTypeId.HIVE, 1), ActTech(UpgradeId.ZERGLINGATTACKSPEED)),
            StepBuildGas(6, None),
            Step(None, ActBuilding(UnitTypeId.ULTRALISKCAVERN, 1)),
            Step(None, ActTech(UpgradeId.ZERGMELEEWEAPONSLEVEL3)),
            Step(None, ActTech(UpgradeId.ZERGGROUNDARMORSLEVEL3)),
            Step(None, ActTech(UpgradeId.CHITINOUSPLATING)),
            Step(None, ActTech(UpgradeId.ANABOLICSYNTHESIS)),
        ]

        super().__init__([
            self.overlords,
            ultras,
            units,
            build_step_expansions,
            queens,
            pool_and_tech
        ])


class MacroZergV2(KnowledgeBot):
    """Macro Zerg bot that expands like crazy, makes drones and finally transitions to waves of zerglings."""
    def __init__(self):
        super().__init__("Macro zerg")

    async def create_plan(self) -> BuildOrder:
        attack = PlanZoneAttack(120)
        attack.retreat_multiplier = 0.3
        tactics = [
            PlanCancelBuilding(),
            InjectLarva(),
            PlanDistributeWorkers(),
            attack,
            PlanFinishEnemy(),
        ]
        return BuildOrder([
            MacroBuild(),
            tactics,
        ])


class LadderBot(MacroZergV2):
    @property
    def my_race(self):
        return Race.Zerg
