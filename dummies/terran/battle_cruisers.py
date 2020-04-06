from sharpy.knowledges import KnowledgeBot
from sharpy.plans.acts import *
from sharpy.plans.acts.terran import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans.tactics.terran import *
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sc2 import UnitTypeId, AbilityId, Race
from sc2.ids.upgrade_id import UpgradeId
import random


class JumpIn(ActBase):
    def __init__(self):
        self.done = False
        super().__init__()

    async def execute(self) -> bool:
        if self.done:
            return True
        bcs = self.cache.own(UnitTypeId.BATTLECRUISER)
        if bcs.amount > 1:
            self.done = True
            for bc in bcs:
                self.knowledge.cooldown_manager.used_ability(bc.tag, AbilityId.EFFECT_TACTICALJUMP)
                self.do(bc(AbilityId.EFFECT_TACTICALJUMP, self.knowledge.enemy_main_zone.behind_mineral_position_center))
        return True


class BattleCruisers(KnowledgeBot):

    def __init__(self):
        super().__init__("Flying Rust")

    async def pre_step_execute(self):
        pass

    async def create_plan(self) -> BuildOrder:
        attack_value = random.randint(50, 80)
        self.attack = Step(None, PlanZoneAttack(attack_value))
        empty = BuildOrder([])
        self.jump = random.randint(0,2)

        if self.jump == 0:
            self.knowledge.print(f"Att at {attack_value}", "Build")
        else:
            self.knowledge.print(f"Jump, att at {attack_value }", "Build")
        worker_scout = Step(None, WorkerScout(), skip_until=RequiredUnitExists(UnitTypeId.SUPPLYDEPOT, 1))
        self.distribute_workers = PlanDistributeWorkers(4)
        tactics = [
            PlanCancelBuilding(),
            LowerDepots(),
            PlanZoneDefense(),
            worker_scout,
            Step(None, CallMule(50), skip=RequiredTime(5* 60)),
            Step(None, CallMule(100), skip_until=RequiredTime(5 * 60)),
            Step(None, ScanEnemy(), skip_until=RequiredTime(5 * 60)),

            self.distribute_workers,
            ManTheBunkers(),
            Repair(),
            ContinueBuilding(),
            PlanZoneGatherTerran(),
            Step(None, JumpIn(), RequireCustom(lambda k: self.jump == 0)),
            self.attack,
            PlanFinishEnemy(),
        ]

        return BuildOrder([
            empty.depots,
            Step(None, MorphOrbitals(), skip_until=RequiredUnitReady(UnitTypeId.BARRACKS, 1)),
            [
                Step(None, ActUnit(UnitTypeId.SCV, UnitTypeId.COMMANDCENTER, 34 + 12))
            ],
            [
                Step(RequiredSupply(13), GridBuilding(UnitTypeId.SUPPLYDEPOT, 1)),

                Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 0.95), GridBuilding(UnitTypeId.BARRACKS, 1)),
                StepBuildGas(1),
                ActExpand(2),
                Step(RequiredSupply(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 2)),
                StepBuildGas(2),
                Step(None, GridBuilding(UnitTypeId.FACTORY, 1),
                     skip_until=RequiredUnitReady(UnitTypeId.BARRACKS, 1)),
                Step(RequiredUnitReady(UnitTypeId.FACTORY, 1), GridBuilding(UnitTypeId.STARPORT, 1)),
                DefensiveBuilding(UnitTypeId.BUNKER, DefensePosition.Entrance, 1),
                Step(None, GridBuilding(UnitTypeId.BARRACKS, 2)),
                StepBuildGas(3),

                Step(None, ActBuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 1)),
                Step(RequiredUnitReady(UnitTypeId.STARPORT, 1), GridBuilding(UnitTypeId.FUSIONCORE, 1)),
                Step(None, ActBuildAddon(UnitTypeId.STARPORTTECHLAB, UnitTypeId.STARPORT, 1)),
                StepBuildGas(4, None, RequiredUnitExists(UnitTypeId.BATTLECRUISER,1,include_killed=True, include_pending=True)),
                Step(RequiredUnitExists(UnitTypeId.BATTLECRUISER,1,include_killed=True), GridBuilding(UnitTypeId.BARRACKS, 3)),
                Step(None, ActBuildAddon(UnitTypeId.BARRACKSTECHLAB, UnitTypeId.BARRACKS, 1)),
                Step(None, ActBuildAddon(UnitTypeId.BARRACKSREACTOR, UnitTypeId.BARRACKS, 1)),

                Step(None, GridBuilding(UnitTypeId.STARPORT, 2)),

                Step(RequiredUnitReady(UnitTypeId.STARPORT, 2), ActBuildAddon(UnitTypeId.STARPORTTECHLAB, UnitTypeId.STARPORT, 2)),
                Step(None, ActTech(UpgradeId.SHIELDWALL)),

                Step(RequiredMinerals(600), GridBuilding(UnitTypeId.BARRACKS, 5)),
                ActExpand(3),
            ],
            [
                Step(RequiredAny([RequiredEnemyBuildingExists(UnitTypeId.DARKSHRINE),
                                  RequiredEnemyUnitExistsAfter(UnitTypeId.DARKTEMPLAR),
                                  RequiredEnemyUnitExistsAfter(UnitTypeId.BANSHEE)]), None),
                Step(RequiredUnitReady(UnitTypeId.STARPORT, 1), ActUnit(UnitTypeId.RAVEN, UnitTypeId.STARPORT, 2, priority=True)),
            ],
            Step(None, SequentialList([
                ActUnit(UnitTypeId.BATTLECRUISER, UnitTypeId.STARPORT, 20, priority=True)
            ]), skip_until=RequiredUnitReady(UnitTypeId.FUSIONCORE, 1)),
            ActUnit(UnitTypeId.SIEGETANK, UnitTypeId.FACTORY, 10),
            ActUnit(UnitTypeId.MARINE, UnitTypeId.BARRACKS, 50),
            SequentialList(tactics)
        ])


class LadderBot(BattleCruisers):
    @property
    def my_race(self):
        return Race.Terran
