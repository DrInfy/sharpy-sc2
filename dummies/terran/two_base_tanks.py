from sharpy.plans.acts import *
from sharpy.plans.acts.terran import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans.tactics.terran import *
from sharpy.plans import BuildOrder, Step, StepBuildGas
from sc2 import UnitTypeId, Race
from sc2.ids.upgrade_id import UpgradeId

from sharpy.knowledges import KnowledgeBot


class TwoBaseTanks(KnowledgeBot):
    def __init__(self):

        super().__init__("Two base tanks")

    async def create_plan(self) -> BuildOrder:
        build_steps_scv = [
            Step(None, ActUnit(UnitTypeId.SCV, UnitTypeId.COMMANDCENTER, 16 + 6),
                 skip=RequiredUnitExists(UnitTypeId.COMMANDCENTER, 2)),
            Step(None, ActUnit(UnitTypeId.SCV, UnitTypeId.COMMANDCENTER, 32 + 12))
        ]

        build_steps_buildings = [
            Step(RequiredSupply(13), GridBuilding(UnitTypeId.SUPPLYDEPOT, 1)),
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 0.95),
                 GridBuilding(UnitTypeId.BARRACKS, 1)),
            StepBuildGas(1, RequiredSupply(16)),
            ActExpand(2),
            Step(RequiredSupply(16), GridBuilding(UnitTypeId.SUPPLYDEPOT, 2)),
            StepBuildGas(2, RequiredUnitExists(UnitTypeId.MARINE, 1, include_pending=True)),
            Step(None, GridBuilding(UnitTypeId.FACTORY, 1),
                 skip_until=RequiredUnitReady(UnitTypeId.BARRACKS, 1)),
            Step(None, ActBuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 1),
                 skip_until=RequiredUnitReady(UnitTypeId.FACTORY, 1)),
            Step(RequiredSupply(28), GridBuilding(UnitTypeId.SUPPLYDEPOT, 4)),
            Step(None, GridBuilding(UnitTypeId.FACTORY, 2)),
            Step(None, ActBuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 2)),
            Step(RequiredSupply(38), GridBuilding(UnitTypeId.SUPPLYDEPOT, 5)),
            Step(None, ActExpand(3), skip_until=RequireCustom(self.should_expand)),
            Step(None, ActExpand(4), skip_until=RequiredAll([RequireCustom(self.should_expand),
                                                             RequiredUnitReady(UnitTypeId.COMMANDCENTER, 3)])),
            # BuildStep(None, GridBuilding(UnitTypeId.FACTORY, 3)),
            StepBuildGas(3),
            Step(RequiredSupply(45), GridBuilding(UnitTypeId.SUPPLYDEPOT, 8)),
            Step(None, GridBuilding(UnitTypeId.BARRACKS, 2)),
            Step(None, ActBuildAddon(UnitTypeId.BARRACKSTECHLAB, UnitTypeId.BARRACKS, 1)),
            Step(None, ActTech(UpgradeId.SHIELDWALL)),
            StepBuildGas(4),
            # BuildStep(None, GridBuilding(UnitTypeId.ARMORY, 1)),
            Step(RequiredSupply(75), GridBuilding(UnitTypeId.SUPPLYDEPOT, 10)),
            Step(None, GridBuilding(UnitTypeId.BARRACKS, 5)),
            Step(None, ActBuildAddon(UnitTypeId.BARRACKSREACTOR, UnitTypeId.BARRACKS, 3)),
            Step(None, GridBuilding(UnitTypeId.FACTORY, 3)),
            Step(None, ActBuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 3)),
            Step(RequiredSupply(85), GridBuilding(UnitTypeId.SUPPLYDEPOT, 14)),
        ]

        build_steps_mech = [
            # Step(RequiredUnitExists(UnitTypeId.FACTORY, 1), ActUnit(UnitTypeId.HELLION, UnitTypeId.FACTORY, 2)),
            Step(RequiredUnitReady(UnitTypeId.FACTORYTECHLAB, 1), ActUnit(UnitTypeId.SIEGETANK, UnitTypeId.FACTORY, 20))
        ]

        build_steps_marines = [
            Step(RequiredUnitReady(UnitTypeId.BARRACKS, 1), ActUnit(UnitTypeId.MARINE, UnitTypeId.BARRACKS, 2)),
            Step(RequiredMinerals(250), ActUnit(UnitTypeId.MARINE, UnitTypeId.BARRACKS, 100))
        ]

        build_order = BuildOrder([
            build_steps_scv,

            build_steps_buildings,
            build_steps_mech,
            Step(None, MorphOrbitals(), skip_until=RequiredUnitReady(UnitTypeId.BARRACKS, 1)),
            build_steps_marines,
            ActBuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 99)
        ])

        scout = Step(None, WorkerScout(), skip_until=RequiredUnitExists(UnitTypeId.BARRACKS, 1))

        self.attack = PlanZoneAttack(60)
        tactics = [
            PlanCancelBuilding(),
            LowerDepots(),
            PlanZoneDefense(),
            scout,
            ScanEnemy(120),
            CallMule(),
            PlanDistributeWorkers(),
            Repair(),
            ContinueBuilding(),
            PlanZoneGatherTerran(),
            self.attack,
            PlanFinishEnemy(),
        ]
        return BuildOrder([
            build_order,
            tactics
        ])

    def should_expand(self, knowledge):
        count = 0
        for zone in self.knowledge.our_zones:
            if zone.our_townhall != None:
                count += zone.our_townhall.surplus_harvesters

        return count > 5


class LadderBot(TwoBaseTanks):
    @property
    def my_race(self):
        return Race.Terran
