from typing import List

from sharpy.plans.acts import *
from sharpy.plans.acts.terran import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans.tactics.terran import *
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sc2 import BotAI, UnitTypeId, AbilityId, Race
from sc2.ids.upgrade_id import UpgradeId

from sharpy.knowledges import Knowledge, KnowledgeBot


class CycloneBot(KnowledgeBot):
    def __init__(self):
        super().__init__("Rusty Locks")

    async def create_plan(self) -> BuildOrder:
        buildings = [
            Step(Supply(13), GridBuilding(UnitTypeId.SUPPLYDEPOT, 1)),
            Step(Supply(16), Expand(2)),
            Step(Supply(18), GridBuilding(UnitTypeId.BARRACKS, 1)),
            BuildGas(1),
            Step(Supply(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 2)),
            Step(None, BuildGas(2), skip_until=UnitExists(UnitTypeId.MARINE, 2)),
            Step(None, GridBuilding(UnitTypeId.FACTORY, 1), skip_until=UnitReady(UnitTypeId.BARRACKS, 1)),
            GridBuilding(UnitTypeId.FACTORY, 1),
            BuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 1),
            BuildGas(4),
            Step(None, Expand(3)),
            GridBuilding(UnitTypeId.FACTORY, 2),
            BuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 2),
            Step(None, Tech(UpgradeId.CYCLONELOCKONDAMAGEUPGRADE), skip_until=UnitReady(UnitTypeId.FACTORYTECHLAB, 1),),
            BuildGas(5),
            Step(None, Tech(UpgradeId.HIGHCAPACITYBARRELS), skip_until=UnitReady(UnitTypeId.FACTORYTECHLAB, 2)),
            StepBuildGas(6, None, Gas(100)),
            Step(Minerals(400), GridBuilding(UnitTypeId.FACTORY, 4)),
            Step(None, BuildAddon(UnitTypeId.FACTORYREACTOR, UnitTypeId.FACTORY, 1)),
            BuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 3),
            Step(Minerals(400), Expand(4)),
            GridBuilding(UnitTypeId.ENGINEERINGBAY, 1),
            BuildGas(8),
            GridBuilding(UnitTypeId.FACTORY, 6),
            Step(Minerals(400), GridBuilding(UnitTypeId.FACTORY, 8)),
            BuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 7),
            Step(Supply(120), GridBuilding(UnitTypeId.ARMORY, 2)),
        ]

        upgrades = [
            Step(UnitReady(UnitTypeId.ARMORY, 1), Tech(UpgradeId.TERRANVEHICLEWEAPONSLEVEL1)),
            Tech(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL1),
            Tech(UpgradeId.TERRANVEHICLEWEAPONSLEVEL2),
            Tech(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL2),
            Tech(UpgradeId.TERRANVEHICLEWEAPONSLEVEL3),
            Tech(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL3),
        ]

        self.attack = PlanZoneAttack(40)

        worker_scout = Step(None, WorkerScout(), skip_until=UnitExists(UnitTypeId.SUPPLYDEPOT, 1))
        self.distribute_workers = DistributeWorkers()

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
            Step(TechReady(UpgradeId.CYCLONELOCKONDAMAGEUPGRADE, 0.95), self.attack),
            PlanFinishEnemy(),
        ]

        return BuildOrder(
            Step(UnitExists(UnitTypeId.BARRACKS, 1), SequentialList(self.depots)),
            [
                Step(
                    UnitExists(UnitTypeId.COMMANDCENTER, 2),
                    MorphOrbitals(3),
                    skip_until=UnitReady(UnitTypeId.BARRACKS, 1),
                ),
                Step(None, MorphPlanetary(2), skip_until=UnitReady(UnitTypeId.ENGINEERINGBAY, 1)),
            ],
            [
                Step(None, ActUnit(UnitTypeId.SCV, UnitTypeId.COMMANDCENTER, 40)),
                Step(UnitExists(UnitTypeId.COMMANDCENTER, 3), ActUnit(UnitTypeId.SCV, UnitTypeId.COMMANDCENTER, 70),),
            ],
            upgrades,
            ActUnit(UnitTypeId.MARINE, UnitTypeId.BARRACKS, 4),
            [
                ActUnit(UnitTypeId.CYCLONE, UnitTypeId.FACTORY, 4),
                ActUnitOnce(UnitTypeId.HELLION, UnitTypeId.FACTORY, 1),
                ActUnit(UnitTypeId.CYCLONE, UnitTypeId.FACTORY, 4),
                ActUnit(UnitTypeId.CYCLONE, UnitTypeId.FACTORY, 120, priority=True),
            ],
            Step(
                UnitReady(UnitTypeId.FACTORYREACTOR, 1),
                ActUnit(UnitTypeId.HELLION, UnitTypeId.FACTORY, 60),
                skip_until=Minerals(300),
            ),
            buildings,
            SequentialList(tactics),
        )

    @property
    def depots(self) -> List[Step]:
        return [
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 1), None),
            Step(SupplyLeft(6), GridBuilding(UnitTypeId.SUPPLYDEPOT, 2)),
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 2), None),
            Step(SupplyLeft(14), GridBuilding(UnitTypeId.SUPPLYDEPOT, 4)),
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 4), None),
            Step(SupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 6)),
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 5), None),
            Step(SupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 7)),
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 6), None),
            Step(SupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 10)),
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 8), None),
            Step(SupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 12)),
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 10), None),
            Step(SupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 14)),
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 13), None),
            Step(SupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 16)),
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 16), GridBuilding(UnitTypeId.SUPPLYDEPOT, 20)),
        ]


class LadderBot(CycloneBot):
    @property
    def my_race(self):
        return Race.Terran
