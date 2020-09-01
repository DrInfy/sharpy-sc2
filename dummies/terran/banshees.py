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


class Banshees(KnowledgeBot):
    def __init__(self):
        super().__init__("Rusty Screams")

    async def pre_step_execute(self):
        pass

    async def create_plan(self) -> BuildOrder:
        attack_value = random.randint(4, 7) * 10
        self.attack = Step(None, PlanZoneAttack(attack_value))
        self.jump = random.randint(0, 2)

        self.knowledge.print(f"Att at {attack_value}", "Build")

        worker_scout = Step(None, WorkerScout(), skip_until=UnitExists(UnitTypeId.SUPPLYDEPOT, 1))
        self.distribute_workers = DistributeWorkers(4)
        tactics = [
            PlanCancelBuilding(),
            LowerDepots(),
            PlanZoneDefense(),
            worker_scout,
            Step(None, CallMule(50), skip=Time(5 * 60)),
            Step(None, CallMule(100), skip_until=Time(5 * 60)),
            Step(None, ScanEnemy(), skip_until=Time(5 * 60)),
            self.distribute_workers,
            ManTheBunkers(),
            Repair(),
            ContinueBuilding(),
            PlanZoneGatherTerran(),
            self.attack,
            PlanFinishEnemy(),
        ]

        return BuildOrder(
            AutoDepot(),
            Step(None, MorphOrbitals(), skip_until=UnitReady(UnitTypeId.BARRACKS, 1)),
            [Step(None, ActUnit(UnitTypeId.SCV, UnitTypeId.COMMANDCENTER, 34 + 12))],
            [
                Step(Supply(13), GridBuilding(UnitTypeId.SUPPLYDEPOT, 1)),
                Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 0.95), GridBuilding(UnitTypeId.BARRACKS, 1)),
                BuildGas(1),
                Expand(2),
                Step(Supply(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 2)),
                BuildGas(2),
                Step(None, GridBuilding(UnitTypeId.FACTORY, 1), skip_until=UnitReady(UnitTypeId.BARRACKS, 1)),
                Step(UnitReady(UnitTypeId.FACTORY, 1), GridBuilding(UnitTypeId.STARPORT, 1)),
                DefensiveBuilding(UnitTypeId.BUNKER, DefensePosition.Entrance, 1),
                Step(None, GridBuilding(UnitTypeId.BARRACKS, 2)),
                StepBuildGas(3, None, Gas(150)),
                Step(None, BuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 1)),
                # Step(RequiredUnitReady(UnitTypeId.STARPORT, 1), GridBuilding(UnitTypeId.FUSIONCORE, 1)),
                Step(None, BuildAddon(UnitTypeId.STARPORTTECHLAB, UnitTypeId.STARPORT, 1)),
                StepBuildGas(4, None, Gas(100)),
                Step(UnitExists(UnitTypeId.BANSHEE, 1, include_killed=True), GridBuilding(UnitTypeId.BARRACKS, 3)),
                Step(None, BuildAddon(UnitTypeId.BARRACKSTECHLAB, UnitTypeId.BARRACKS, 1)),
                Step(None, BuildAddon(UnitTypeId.BARRACKSREACTOR, UnitTypeId.BARRACKS, 1)),
                Step(None, GridBuilding(UnitTypeId.STARPORT, 2)),
                Step(
                    UnitReady(UnitTypeId.STARPORT, 2), BuildAddon(UnitTypeId.STARPORTTECHLAB, UnitTypeId.STARPORT, 2),
                ),
                Step(None, Tech(UpgradeId.SHIELDWALL)),
                Step(Minerals(600), GridBuilding(UnitTypeId.BARRACKS, 5)),
                Expand(3),
            ],
            [
                Step(
                    Any(
                        [
                            EnemyBuildingExists(UnitTypeId.DARKSHRINE),
                            EnemyUnitExistsAfter(UnitTypeId.DARKTEMPLAR),
                            EnemyUnitExistsAfter(UnitTypeId.BANSHEE),
                        ]
                    ),
                    None,
                ),
                Step(
                    UnitReady(UnitTypeId.STARPORT, 1), ActUnit(UnitTypeId.RAVEN, UnitTypeId.STARPORT, 2, priority=True),
                ),
            ],
            ActUnit(UnitTypeId.BANSHEE, UnitTypeId.STARPORT, 20, priority=True),
            ActUnit(UnitTypeId.SIEGETANK, UnitTypeId.FACTORY, 10),
            ActUnit(UnitTypeId.MARINE, UnitTypeId.BARRACKS, 50),
            SequentialList(tactics),
        )


class LadderBot(Banshees):
    @property
    def my_race(self):
        return Race.Terran
