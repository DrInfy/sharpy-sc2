from sc2 import UnitTypeId, Race

from sharpy.knowledges import KnowledgeBot
from sharpy.plans import BuildOrder, Step, StepBuildGas
from sharpy.plans.acts import *
from sharpy.plans.acts.terran import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans.tactics.terran import *


class OneBaseTurtle(KnowledgeBot):
    def __init__(self):

        super().__init__("One Base Turtle Defence")

    async def create_plan(self) -> BuildOrder:

        build_steps_buildings = [
            TerranUnit(UnitTypeId.SCV, 13),
            Step(Supply(13), GridBuilding(UnitTypeId.SUPPLYDEPOT, 1)),
            TerranUnit(UnitTypeId.SCV, 15),
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 0.95), GridBuilding(UnitTypeId.BARRACKS, 1)),
            TerranUnit(UnitTypeId.SCV, 16),
            BuildGas(1),
            Step(Supply(16), GridBuilding(UnitTypeId.SUPPLYDEPOT, 2)),
            TerranUnit(UnitTypeId.SCV, 18),
            Step(None, MorphOrbitals(), skip_until=UnitReady(UnitTypeId.BARRACKS, 1)),
            Step(None, GridBuilding(UnitTypeId.FACTORY, 1), skip_until=UnitReady(UnitTypeId.BARRACKS, 1)),
            TerranUnit(UnitTypeId.SCV, 20),
            Step(Supply(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 3)),
            Step(None, GridBuilding(UnitTypeId.BUNKER, 1), skip_until=UnitReady(UnitTypeId.BARRACKS, 1)),
            BuildGas(2),
            Step(None, GridBuilding(UnitTypeId.FACTORY, 2)),
            TerranUnit(UnitTypeId.SCV, 22),
            Step(
                None,
                BuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 2),
                skip_until=UnitReady(UnitTypeId.FACTORY, 1),
            ),
            Step(Supply(28), GridBuilding(UnitTypeId.SUPPLYDEPOT, 4)),
            Step(None, GridBuilding(UnitTypeId.BARRACKS, 3)),
            Step(Supply(38), GridBuilding(UnitTypeId.SUPPLYDEPOT, 5)),
            AutoDepot(),
        ]

        build_step_tanks = [
            Step(UnitReady(UnitTypeId.FACTORYTECHLAB, 1), ActUnit(UnitTypeId.SIEGETANK, UnitTypeId.FACTORY, 20))
        ]

        build_steps_marines = [
            Step(UnitReady(UnitTypeId.BARRACKS, 1), ActUnit(UnitTypeId.MARINE, UnitTypeId.BARRACKS, 100)),
        ]

        build_order = BuildOrder([build_steps_buildings, build_step_tanks, build_steps_marines])

        attack = PlanZoneAttack(4)
        tactics = [
            PlanCancelBuilding(),
            ManTheBunkers(),
            LowerDepots(),
            PlanZoneDefense(),
            CallMule(),
            DistributeWorkers(),
            Repair(),
            ContinueBuilding(),
            PlanZoneGatherTerran(),
            # once enough marines to guard the tanks, attack
            Step(UnitExists(UnitTypeId.MARINE, 18, include_killed=True), attack),
            PlanFinishEnemy(),
        ]
        return BuildOrder(build_order, tactics)


class LadderBot(OneBaseTurtle):
    @property
    def my_race(self):
        return Race.Terran
