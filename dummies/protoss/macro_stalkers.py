from sc2 import UnitTypeId, Race
from sc2.ids.upgrade_id import UpgradeId

from sharpy.knowledges import KnowledgeBot
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sharpy.plans.acts import *
from sharpy.plans.acts.protoss import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *


class MacroStalkers(KnowledgeBot):

    def __init__(self):
        super().__init__("Sharp Spiders")

    async def create_plan(self) -> BuildOrder:
        return BuildOrder([
            Step(None, ChronoUnitProduction(UnitTypeId.PROBE, UnitTypeId.NEXUS),
                 skip=RequiredUnitExists(UnitTypeId.PROBE, 40, include_pending=True), skip_until=RequiredUnitExists(UnitTypeId.ASSIMILATOR, 1)),
            SequentialList([
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 14),
                GridBuilding(UnitTypeId.PYLON, 1),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 16),
                StepBuildGas(1),
                GridBuilding(UnitTypeId.GATEWAY, 1),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 20),
                ActExpand(2),
                GridBuilding(UnitTypeId.CYBERNETICSCORE, 1),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 21),
                StepBuildGas(2),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 22),
                GridBuilding(UnitTypeId.PYLON, 1),
                BuildOrder(
                    [
                        AutoPylon(),
                        ActTech(UpgradeId.WARPGATERESEARCH),
                        [
                            ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 22),
                            Step(RequiredUnitExists(UnitTypeId.NEXUS, 2), ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 44)),
                            StepBuildGas(3,skip=RequiredGas(300))
                        ],
                    [
                        GateUnit(UnitTypeId.STALKER, 100)
                    ],
                    [
                        GridBuilding(UnitTypeId.GATEWAY, 7),
                        StepBuildGas(4, skip=RequiredGas(200)),
                    ]
                ])
            ]),
            SequentialList([
                PlanZoneDefense(),
                RestorePower(),
                PlanDistributeWorkers(),
                PlanZoneGather(),
                Step(RequiredUnitReady(UnitTypeId.GATEWAY, 4), PlanZoneAttack(4)),
                PlanFinishEnemy(),
            ])
        ])


class LadderBot(MacroStalkers):
    @property
    def my_race(self):
        return Race.Protoss
