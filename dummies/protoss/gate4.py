from sharpy.plans.acts import *
from sharpy.plans.acts.protoss import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sharpy.knowledges import KnowledgeBot
from sc2 import UnitTypeId, AbilityId, Race
from sc2.ids.upgrade_id import UpgradeId


class Stalkers4Gate(KnowledgeBot):

    def __init__(self):
        super().__init__("The Sharp Four")

    async def create_plan(self) -> BuildOrder:
        attack = PlanZoneAttack(6)
        return BuildOrder([
            Step(None, ChronoUnitProduction(UnitTypeId.PROBE, UnitTypeId.NEXUS),
                 skip=RequiredUnitExists(UnitTypeId.PROBE, 20, include_pending=True), skip_until=RequiredUnitExists(UnitTypeId.ASSIMILATOR, 1)),
            ChronoTech(AbilityId.RESEARCH_BLINK, UnitTypeId.TWILIGHTCOUNCIL),
            SequentialList([
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 14),
                GridBuilding(UnitTypeId.PYLON, 1),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 16),
                GridBuilding(UnitTypeId.GATEWAY, 1),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 17),
                StepBuildGas(2),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 19),
                GridBuilding(UnitTypeId.GATEWAY, 2),
                BuildOrder(
                    [
                        AutoPylon(),
                        ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 22),
                        SequentialList(
                        [
                            Step(RequiredUnitReady(UnitTypeId.CYBERNETICSCORE, 1), GridBuilding(UnitTypeId.TWILIGHTCOUNCIL, 1)),
                            Step(RequiredUnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), ActTech(UpgradeId.BLINKTECH)),
                        ]),
                        SequentialList(
                        [
                            Step(None, GridBuilding(UnitTypeId.CYBERNETICSCORE, 1), skip_until=RequiredUnitReady(UnitTypeId.GATEWAY, 1)),
                            Step(RequiredUnitReady(UnitTypeId.CYBERNETICSCORE, 1), GateUnit(UnitTypeId.ADEPT, 2, only_once=True)),
                            ActTech(UpgradeId.WARPGATERESEARCH),
                            GateUnit(UnitTypeId.STALKER, 100)
                        ]),
                        Step(RequiredUnitExists(UnitTypeId.CYBERNETICSCORE, 1), GridBuilding(UnitTypeId.GATEWAY, 4))
                    ]),

            ]),
            SequentialList(
                [
                    PlanZoneDefense(),
                    RestorePower(),
                    PlanDistributeWorkers(),
                    PlanZoneGather(),
                    Step(RequiredTechReady(UpgradeId.BLINKTECH, 0.9), attack),
                    PlanFinishEnemy(),
                ])
        ])


class LadderBot(Stalkers4Gate):
    @property
    def my_race(self):
        return Race.Protoss
