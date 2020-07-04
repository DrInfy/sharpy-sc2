from sharpy.plans.acts import *
from sharpy.plans.acts.terran import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans.tactics.terran import *
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sharpy.knowledges import KnowledgeBot
from sc2 import UnitTypeId, AbilityId, Race
from sc2.ids.upgrade_id import UpgradeId
import random


class BuildTanks(BuildOrder):
    def __init__(self):
        viking_counters = [
            UnitTypeId.COLOSSUS,
            UnitTypeId.MEDIVAC,
            UnitTypeId.RAVEN,
            UnitTypeId.VOIDRAY,
            UnitTypeId.CARRIER,
            UnitTypeId.TEMPEST,
            UnitTypeId.BROODLORD,
        ]
        scv = [
            Step(None, MorphOrbitals(), skip_until=UnitReady(UnitTypeId.BARRACKS, 1)),
            Step(
                None,
                ActUnit(UnitTypeId.SCV, UnitTypeId.COMMANDCENTER, 16 + 6),
                skip=UnitExists(UnitTypeId.COMMANDCENTER, 2),
            ),
            Step(None, ActUnit(UnitTypeId.SCV, UnitTypeId.COMMANDCENTER, 32 + 12)),
        ]

        dt_counter = [
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
            Step(None, GridBuilding(UnitTypeId.ENGINEERINGBAY, 1)),
            Step(None, DefensiveBuilding(UnitTypeId.MISSILETURRET, DefensePosition.Entrance, 2)),
            Step(None, DefensiveBuilding(UnitTypeId.MISSILETURRET, DefensePosition.CenterMineralLine, None)),
        ]
        dt_counter2 = [
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
            GridBuilding(UnitTypeId.STARPORT, 2),
            Step(None, BuildAddon(UnitTypeId.STARPORTTECHLAB, UnitTypeId.STARPORT, 1)),
            Step(UnitReady(UnitTypeId.STARPORT, 1), ActUnit(UnitTypeId.RAVEN, UnitTypeId.STARPORT, 2)),
        ]

        buildings = [
            Step(Supply(13), GridBuilding(UnitTypeId.SUPPLYDEPOT, 1)),
            StepBuildGas(1, Supply(16)),
            Step(UnitExists(UnitTypeId.SUPPLYDEPOT), GridBuilding(UnitTypeId.BARRACKS, 1),),
            Step(UnitReady(UnitTypeId.BARRACKS, 0.25), GridBuilding(UnitTypeId.SUPPLYDEPOT, 2)),
            StepBuildGas(1, Supply(18)),
            Step(UnitExists(UnitTypeId.MARINE, 1), Expand(2)),
            StepBuildGas(2, Supply(20)),
            Step(None, GridBuilding(UnitTypeId.FACTORY, 1), skip_until=UnitReady(UnitTypeId.BARRACKS, 1)),
            Step(None, GridBuilding(UnitTypeId.FACTORY, 1)),
            Step(None, BuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 1)),
            # BuildStep(None, GridBuilding(UnitTypeId.FACTORY, 3)),
            Step(UnitExists(UnitTypeId.SIEGETANK, 1, include_killed=True), GridBuilding(UnitTypeId.FACTORY, 2)),
            BuildGas(4),
            Step(None, BuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 2)),
            Step(None, GridBuilding(UnitTypeId.BARRACKS, 2)),
            # BuildStep(None, GridBuilding(UnitTypeId.ARMORY, 1)),
            Step(None, GridBuilding(UnitTypeId.STARPORT, 1)),
            Step(None, GridBuilding(UnitTypeId.BARRACKS, 5)),
            Step(None, BuildAddon(UnitTypeId.BARRACKSTECHLAB, UnitTypeId.BARRACKS, 1)),
            Step(None, Tech(UpgradeId.SHIELDWALL)),
            Step(None, BuildAddon(UnitTypeId.STARPORTREACTOR, UnitTypeId.STARPORT, 1)),
            Step(None, BuildAddon(UnitTypeId.BARRACKSREACTOR, UnitTypeId.BARRACKS, 3)),
            Step(None, Expand(3)),
        ]

        mech = [
            Step(
                UnitExists(UnitTypeId.FACTORY, 1),
                ActUnit(UnitTypeId.HELLION, UnitTypeId.FACTORY, 2),
                skip=UnitReady(UnitTypeId.FACTORYTECHLAB, 1),
            ),
            Step(UnitReady(UnitTypeId.FACTORYTECHLAB, 1), ActUnit(UnitTypeId.SIEGETANK, UnitTypeId.FACTORY, 20)),
        ]
        air = [
            Step(UnitReady(UnitTypeId.STARPORT, 1), ActUnit(UnitTypeId.MEDIVAC, UnitTypeId.STARPORT, 2)),
            Step(None, ActUnit(UnitTypeId.VIKINGFIGHTER, UnitTypeId.STARPORT, 1)),
            Step(
                None,
                ActUnit(UnitTypeId.VIKINGFIGHTER, UnitTypeId.STARPORT, 3),
                skip_until=self.RequireAnyEnemyUnits(viking_counters, 1),
            ),
            Step(UnitReady(UnitTypeId.STARPORT, 1), ActUnit(UnitTypeId.MEDIVAC, UnitTypeId.STARPORT, 4)),
            Step(
                None,
                ActUnit(UnitTypeId.VIKINGFIGHTER, UnitTypeId.STARPORT, 10),
                skip_until=self.RequireAnyEnemyUnits(viking_counters, 4),
            ),
            Step(UnitReady(UnitTypeId.STARPORT, 1), ActUnit(UnitTypeId.MEDIVAC, UnitTypeId.STARPORT, 6)),
        ]
        marines = [
            Step(UnitReady(UnitTypeId.BARRACKS, 1), ActUnit(UnitTypeId.MARINE, UnitTypeId.BARRACKS, 2)),
            Step(Minerals(250), ActUnit(UnitTypeId.MARINE, UnitTypeId.BARRACKS, 100)),
        ]

        super().__init__([scv, dt_counter, dt_counter2, self.depots, buildings, mech, air, marines])


class Rusty(KnowledgeBot):
    def __init__(self):
        super().__init__("Old Rusty")

    async def pre_step_execute(self):
        pass

    async def create_plan(self) -> BuildOrder:
        self.attack = Step(None, PlanZoneAttack(random.randint(50, 80)))
        worker_scout = Step(None, WorkerScout(), skip_until=UnitExists(UnitTypeId.SUPPLYDEPOT, 1))

        tactics = [
            PlanCancelBuilding(),
            LowerDepots(),
            PlanZoneDefense(),
            worker_scout,
            CallMule(100),
            ScanEnemy(),
            DistributeWorkers(),
            ManTheBunkers(),
            Repair(),
            ContinueBuilding(),
            PlanZoneGatherTerran(),
            self.attack,
            PlanFinishEnemy(),
        ]

        return BuildOrder([BuildTanks(), SequentialList(tactics)])


class LadderBot(Rusty):
    @property
    def my_race(self):
        return Race.Terran
