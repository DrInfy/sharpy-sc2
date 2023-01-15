from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from sharpy.plans.acts import *
from sharpy.plans.acts.terran import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans.tactics.terran import *
from sharpy.plans import BuildOrder, Step, StepBuildGas
from sc2.ids.upgrade_id import UpgradeId

from sharpy.knowledges import KnowledgeBot


class TwoBaseTanks(KnowledgeBot):
    def __init__(self):

        super().__init__("Two base tanks")

    async def create_plan(self) -> BuildOrder:
        build_steps_scv = [
            Step(
                None,
                ActUnit(UnitTypeId.SCV, UnitTypeId.COMMANDCENTER, 16 + 6),
                skip=UnitExists(UnitTypeId.COMMANDCENTER, 2),
            ),
            Step(None, ActUnit(UnitTypeId.SCV, UnitTypeId.COMMANDCENTER, 32 + 12)),
        ]

        build_steps_buildings = [
            Step(Supply(13), GridBuilding(UnitTypeId.SUPPLYDEPOT, 1)),
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 0.95), GridBuilding(UnitTypeId.BARRACKS, 1)),
            StepBuildGas(1, Supply(16)),
            Expand(2),
            Step(Supply(16), GridBuilding(UnitTypeId.SUPPLYDEPOT, 2)),
            StepBuildGas(2, UnitExists(UnitTypeId.MARINE, 1, include_pending=True)),
            Step(None, GridBuilding(UnitTypeId.FACTORY, 1), skip_until=UnitReady(UnitTypeId.BARRACKS, 1)),
            Step(
                None,
                BuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 1),
                skip_until=UnitReady(UnitTypeId.FACTORY, 1),
            ),
            Step(Supply(28), GridBuilding(UnitTypeId.SUPPLYDEPOT, 4)),
            Step(None, GridBuilding(UnitTypeId.FACTORY, 2)),
            Step(None, BuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 2)),
            Step(Supply(38), GridBuilding(UnitTypeId.SUPPLYDEPOT, 5)),
            Step(None, Expand(3), skip_until=RequireCustom(self.should_expand)),
            Step(
                None,
                Expand(4),
                skip_until=All([RequireCustom(self.should_expand), UnitReady(UnitTypeId.COMMANDCENTER, 3)]),
            ),
            # BuildStep(None, GridBuilding(UnitTypeId.FACTORY, 3)),
            BuildGas(3),
            Step(Supply(45), GridBuilding(UnitTypeId.SUPPLYDEPOT, 8)),
            Step(None, GridBuilding(UnitTypeId.BARRACKS, 2)),
            Step(None, BuildAddon(UnitTypeId.BARRACKSTECHLAB, UnitTypeId.BARRACKS, 1)),
            Step(None, Tech(UpgradeId.SHIELDWALL)),
            BuildGas(4),
            # BuildStep(None, GridBuilding(UnitTypeId.ARMORY, 1)),
            Step(Supply(75), GridBuilding(UnitTypeId.SUPPLYDEPOT, 10)),
            Step(None, GridBuilding(UnitTypeId.BARRACKS, 5)),
            Step(None, BuildAddon(UnitTypeId.BARRACKSREACTOR, UnitTypeId.BARRACKS, 3)),
            Step(None, GridBuilding(UnitTypeId.FACTORY, 3)),
            Step(None, BuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 3)),
            Step(Supply(85), GridBuilding(UnitTypeId.SUPPLYDEPOT, 14)),
        ]

        build_steps_mech = [
            # Step(UnitExists(UnitTypeId.FACTORY, 1), ActUnit(UnitTypeId.HELLION, UnitTypeId.FACTORY, 2)),
            Step(UnitReady(UnitTypeId.FACTORYTECHLAB, 1), ActUnit(UnitTypeId.SIEGETANK, UnitTypeId.FACTORY, 20))
        ]

        build_steps_marines = [
            Step(UnitReady(UnitTypeId.BARRACKS, 1), ActUnit(UnitTypeId.MARINE, UnitTypeId.BARRACKS, 2)),
            Step(Minerals(250), ActUnit(UnitTypeId.MARINE, UnitTypeId.BARRACKS, 100)),
        ]

        build_order = BuildOrder(
            [
                build_steps_scv,
                build_steps_buildings,
                build_steps_mech,
                Step(None, MorphOrbitals(), skip_until=UnitReady(UnitTypeId.BARRACKS, 1)),
                build_steps_marines,
                BuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 99),
            ]
        )

        scout = Step(None, WorkerScout(), skip_until=UnitExists(UnitTypeId.BARRACKS, 1))

        self.attack = PlanZoneAttack(60)
        tactics = [
            MineOpenBlockedBase(),
            PlanCancelBuilding(),
            LowerDepots(),
            PlanZoneDefense(),
            scout,
            ScanEnemy(120),
            CallMule(),
            DistributeWorkers(),
            Step(None, SpeedMining(), lambda ai: ai.client.game_step > 5),
            Repair(),
            ContinueBuilding(),
            PlanZoneGatherTerran(),
            self.attack,
            PlanFinishEnemy(),
        ]
        return BuildOrder(build_order, tactics)

    def should_expand(self, knowledge):
        count = 0
        for zone in knowledge.zone_manager.our_zones:
            if zone.our_townhall is not None:
                count += zone.our_townhall.surplus_harvesters

        return count > 5


class LadderBot(TwoBaseTanks):
    @property
    def my_race(self):
        return Race.Terran
