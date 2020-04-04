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
        viking_counters = [UnitTypeId.COLOSSUS, UnitTypeId.MEDIVAC, UnitTypeId.RAVEN, UnitTypeId.VOIDRAY,
                           UnitTypeId.CARRIER, UnitTypeId.TEMPEST, UnitTypeId.BROODLORD]
        scv = [
            Step(None, MorphOrbitals(), skip_until=RequiredUnitReady(UnitTypeId.BARRACKS, 1)),
            Step(None, ActUnit(UnitTypeId.SCV, UnitTypeId.COMMANDCENTER, 16 + 6),
                 skip=RequiredUnitExists(UnitTypeId.COMMANDCENTER, 2)),
            Step(None, ActUnit(UnitTypeId.SCV, UnitTypeId.COMMANDCENTER, 32 + 12))
        ]

        dt_counter = [
            Step(RequiredAny([RequiredEnemyBuildingExists(UnitTypeId.DARKSHRINE),
                              RequiredEnemyUnitExistsAfter(UnitTypeId.DARKTEMPLAR),
                              RequiredEnemyUnitExistsAfter(UnitTypeId.BANSHEE)]), None),
            Step(None, GridBuilding(UnitTypeId.ENGINEERINGBAY, 1)),
            Step(None, DefensiveBuilding(UnitTypeId.MISSILETURRET, DefensePosition.Entrance, 2)),
            Step(None, DefensiveBuilding(UnitTypeId.MISSILETURRET, DefensePosition.CenterMineralLine, None))
        ]
        dt_counter2 = [
            Step(RequiredAny([RequiredEnemyBuildingExists(UnitTypeId.DARKSHRINE),
                              RequiredEnemyUnitExistsAfter(UnitTypeId.DARKTEMPLAR),
                              RequiredEnemyUnitExistsAfter(UnitTypeId.BANSHEE)]), None),
            GridBuilding(UnitTypeId.STARPORT, 2),
            Step(None, ActBuildAddon(UnitTypeId.STARPORTTECHLAB, UnitTypeId.STARPORT, 1)),
            Step(RequiredUnitReady(UnitTypeId.STARPORT, 1), ActUnit(UnitTypeId.RAVEN, UnitTypeId.STARPORT, 2)),
        ]

        buildings = [
            Step(RequiredSupply(13), GridBuilding(UnitTypeId.SUPPLYDEPOT, 1),
                 RequiredTotalUnitExists(
                          [UnitTypeId.SUPPLYDEPOT, UnitTypeId.SUPPLYDEPOTDROP, UnitTypeId.SUPPLYDEPOTLOWERED], 1)),
            StepBuildGas(1, RequiredSupply(16)),
            Step(RequiredTotalUnitExists(
                [UnitTypeId.SUPPLYDEPOT, UnitTypeId.SUPPLYDEPOTDROP, UnitTypeId.SUPPLYDEPOTLOWERED], 1),
                      GridBuilding(UnitTypeId.BARRACKS, 1)),
            Step(RequiredUnitReady(UnitTypeId.BARRACKS, 0.25), GridBuilding(UnitTypeId.SUPPLYDEPOT, 2),
                 RequiredTotalUnitExists(
                          [UnitTypeId.SUPPLYDEPOT, UnitTypeId.SUPPLYDEPOTDROP, UnitTypeId.SUPPLYDEPOTLOWERED], 2)),
            StepBuildGas(1, RequiredSupply(18)),
            Step(RequiredUnitExists(UnitTypeId.MARINE, 1), ActExpand(2)),

            StepBuildGas(2, RequiredSupply(20)),
            Step(None, GridBuilding(UnitTypeId.FACTORY, 1),
                 skip_until=RequiredUnitReady(UnitTypeId.BARRACKS, 1)),
            Step(None, GridBuilding(UnitTypeId.FACTORY, 1)),
            Step(None, ActBuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 1)),
            # BuildStep(None, GridBuilding(UnitTypeId.FACTORY, 3)),
            Step(RequiredUnitExists(UnitTypeId.SIEGETANK, 1, include_killed=True), GridBuilding(UnitTypeId.FACTORY, 2)),
            StepBuildGas(4),
            Step(None, ActBuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 2)),

            Step(None, GridBuilding(UnitTypeId.BARRACKS, 2)),
            # BuildStep(None, GridBuilding(UnitTypeId.ARMORY, 1)),
            Step(None, GridBuilding(UnitTypeId.STARPORT, 1)),
            Step(None, GridBuilding(UnitTypeId.BARRACKS, 5)),
            Step(None, ActBuildAddon(UnitTypeId.BARRACKSTECHLAB, UnitTypeId.BARRACKS, 1)),
            Step(None, ActTech(UpgradeId.SHIELDWALL)),
            Step(None, ActBuildAddon(UnitTypeId.STARPORTREACTOR, UnitTypeId.STARPORT, 1)),
            Step(None, ActBuildAddon(UnitTypeId.BARRACKSREACTOR, UnitTypeId.BARRACKS, 3)),
            Step(None, ActExpand(3)),
        ]

        mech = [
            Step(RequiredUnitExists(UnitTypeId.FACTORY, 1), ActUnit(UnitTypeId.HELLION, UnitTypeId.FACTORY, 2),
                 skip=RequiredUnitReady(UnitTypeId.FACTORYTECHLAB, 1)),
            Step(RequiredUnitReady(UnitTypeId.FACTORYTECHLAB, 1),
                 ActUnit(UnitTypeId.SIEGETANK, UnitTypeId.FACTORY, 20))
        ]
        air = [
            Step(RequiredUnitReady(UnitTypeId.STARPORT, 1),
                 ActUnit(UnitTypeId.MEDIVAC, UnitTypeId.STARPORT, 2)),
            Step(None, ActUnit(UnitTypeId.VIKINGFIGHTER, UnitTypeId.STARPORT, 1)),
            Step(None, ActUnit(UnitTypeId.VIKINGFIGHTER, UnitTypeId.STARPORT, 3), skip_until=
                self.RequireAnyEnemyUnits(viking_counters, 1)),
            Step(RequiredUnitReady(UnitTypeId.STARPORT, 1),
                 ActUnit(UnitTypeId.MEDIVAC, UnitTypeId.STARPORT, 4)),
            Step(None, ActUnit(UnitTypeId.VIKINGFIGHTER, UnitTypeId.STARPORT, 10), skip_until=
                self.RequireAnyEnemyUnits(viking_counters, 4)),
            Step(RequiredUnitReady(UnitTypeId.STARPORT, 1),
                 ActUnit(UnitTypeId.MEDIVAC, UnitTypeId.STARPORT, 6)),
            ]
        marines = [
            Step(RequiredUnitReady(UnitTypeId.BARRACKS, 1), ActUnit(UnitTypeId.MARINE, UnitTypeId.BARRACKS, 2)),
            Step(RequiredMinerals(250), ActUnit(UnitTypeId.MARINE, UnitTypeId.BARRACKS, 100))
        ]

        super().__init__([scv,
                          dt_counter, dt_counter2,
                          self.depots, buildings, mech, air, marines])


class Rusty(KnowledgeBot):
    def __init__(self):
        super().__init__("Old Rusty")

    async def pre_step_execute(self):
        pass

    async def create_plan(self) -> BuildOrder:
        self.attack = Step(None, PlanZoneAttack(random.randint(50, 80)))
        worker_scout = Step(None, WorkerScout(), skip_until=RequiredUnitExists(UnitTypeId.SUPPLYDEPOT, 1))

        tactics = [
            PlanCancelBuilding(),
            LowerDepots(),
            PlanZoneDefense(),
            worker_scout,
            CallMule(100),
            ScanEnemy(),

            PlanDistributeWorkers(),
            ManTheBunkers(),
            Repair(),
            ContinueBuilding(),
            PlanZoneGatherTerran(),
            self.attack,
            PlanFinishEnemy(),
        ]

        return BuildOrder([
            BuildTanks(),
            SequentialList(tactics)
        ])


class LadderBot(Rusty):
    @property
    def my_race(self):
        return Race.Terran
