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
            Step(RequiredSupply(13), GridBuilding(UnitTypeId.SUPPLYDEPOT, 1)),
            Step(RequiredSupply(16), ActExpand(2)),

            Step(RequiredSupply(18), GridBuilding(UnitTypeId.BARRACKS, 1)),
            StepBuildGas(1),
            Step(RequiredSupply(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 2)),
            Step(None, StepBuildGas(2), skip_until=RequiredUnitExists(UnitTypeId.MARINE, 2)),
            Step(None, GridBuilding(UnitTypeId.FACTORY, 1),
                 skip_until=RequiredUnitReady(UnitTypeId.BARRACKS, 1)),
            GridBuilding(UnitTypeId.FACTORY, 1),
            ActBuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 1),
            StepBuildGas(4),
            Step(None, ActExpand(3)),
            GridBuilding(UnitTypeId.FACTORY, 2),
            ActBuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 2),
            Step(None, ActTech(UpgradeId.CYCLONELOCKONDAMAGEUPGRADE),
                 skip_until=RequiredUnitReady(UnitTypeId.FACTORYTECHLAB, 1)),
            StepBuildGas(5),
            Step(None, ActTech(UpgradeId.HIGHCAPACITYBARRELS),
                 skip_until=RequiredUnitReady(UnitTypeId.FACTORYTECHLAB, 2)),
            StepBuildGas(6, None, RequiredGas(100)),
            Step(RequiredMinerals(400), GridBuilding(UnitTypeId.FACTORY, 4)),
            Step(None, ActBuildAddon(UnitTypeId.FACTORYREACTOR, UnitTypeId.FACTORY, 1)),
            ActBuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 3),
            Step(RequiredMinerals(400), ActExpand(4)),
            GridBuilding(UnitTypeId.ENGINEERINGBAY, 1),
            StepBuildGas(8),
            GridBuilding(UnitTypeId.FACTORY, 6),
            Step(RequiredMinerals(400), GridBuilding(UnitTypeId.FACTORY, 8)),
            ActBuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 7),
            Step(RequiredSupply(120), GridBuilding(UnitTypeId.ARMORY, 2)),

        ]

        upgrades = [
            Step(RequiredUnitReady(UnitTypeId.ARMORY, 1), ActTech(UpgradeId.TERRANVEHICLEWEAPONSLEVEL1)),
            ActTech(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL1),
            ActTech(UpgradeId.TERRANVEHICLEWEAPONSLEVEL2),
            ActTech(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL2),
            ActTech(UpgradeId.TERRANVEHICLEWEAPONSLEVEL3),
            ActTech(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL3),
        ]

        self.attack = PlanZoneAttack(40)

        worker_scout = Step(None, WorkerScout(), skip_until=RequiredUnitExists(UnitTypeId.SUPPLYDEPOT, 1))
        self.distribute_workers = PlanDistributeWorkers()

        tactics = [
            PlanCancelBuilding(),
            LowerDepots(),
            PlanZoneDefense(),
            worker_scout,
            Step(None, CallMule(50), skip=RequiredTime(5 * 60)),
            Step(None, CallMule(100), skip_until=RequiredTime(5 * 60)),
            Step(None, ScanEnemy(), skip_until=RequiredTime(5 * 60)),

            self.distribute_workers,
            ManTheBunkers(),
            Repair(),
            ContinueBuilding(),
            PlanZoneGatherTerran(),
            Step(RequiredTechReady(UpgradeId.CYCLONELOCKONDAMAGEUPGRADE, 0.95), self.attack),
            PlanFinishEnemy(),
        ]

        return BuildOrder([
            Step(RequiredUnitExists(UnitTypeId.BARRACKS, 1), SequentialList(self.depots)),
            [
                Step(RequiredUnitExists(UnitTypeId.COMMANDCENTER, 2), MorphOrbitals(3), skip_until=RequiredUnitReady(UnitTypeId.BARRACKS, 1)),
                Step(None, MorphPlanetary(2), skip_until=RequiredUnitReady(UnitTypeId.ENGINEERINGBAY, 1)),
            ],
            [
                Step(None, ActUnit(UnitTypeId.SCV, UnitTypeId.COMMANDCENTER, 40)),
                Step(RequiredUnitExists(UnitTypeId.COMMANDCENTER, 3), ActUnit(UnitTypeId.SCV, UnitTypeId.COMMANDCENTER, 70))
            ],
            upgrades,
            ActUnit(UnitTypeId.MARINE, UnitTypeId.BARRACKS, 4),
            [
                ActUnit(UnitTypeId.CYCLONE, UnitTypeId.FACTORY, 4),
                ActUnitOnce(UnitTypeId.HELLION, UnitTypeId.FACTORY, 1),
                ActUnit(UnitTypeId.CYCLONE, UnitTypeId.FACTORY, 4),
                ActUnit(UnitTypeId.CYCLONE, UnitTypeId.FACTORY, 120, priority=True),
            ],
            Step(RequiredUnitReady(UnitTypeId.FACTORYREACTOR, 1),
                 ActUnit(UnitTypeId.HELLION, UnitTypeId.FACTORY, 60),
                 skip_until=RequiredMinerals(300),
                 ),

            buildings,
            SequentialList(tactics)
        ])

    @property
    def depots(self) -> List[Step]:
        return [
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 1), None),
            Step(RequiredSupplyLeft(6), GridBuilding(UnitTypeId.SUPPLYDEPOT, 2)),
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 2), None),
            Step(RequiredSupplyLeft(14), GridBuilding(UnitTypeId.SUPPLYDEPOT, 4)),
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 4), None),
            Step(RequiredSupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 6)),
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 5), None),
            Step(RequiredSupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 7)),
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 6), None),
            Step(RequiredSupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 10)),
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 8), None),
            Step(RequiredSupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 12)),
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 10), None),
            Step(RequiredSupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 14)),
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 13), None),
            Step(RequiredSupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 16)),
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 16), GridBuilding(UnitTypeId.SUPPLYDEPOT, 20)),
        ]


class LadderBot(CycloneBot):
    @property
    def my_race(self):
        return Race.Terran
