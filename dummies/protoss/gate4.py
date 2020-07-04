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
        return BuildOrder(
            Step(
                None,
                ChronoUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS),
                skip=UnitExists(UnitTypeId.PROBE, 20, include_pending=True),
                skip_until=UnitExists(UnitTypeId.ASSIMILATOR, 1),
            ),
            ChronoTech(AbilityId.RESEARCH_BLINK, UnitTypeId.TWILIGHTCOUNCIL),
            SequentialList(
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 14),
                GridBuilding(UnitTypeId.PYLON, 1),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 16),
                GridBuilding(UnitTypeId.GATEWAY, 1),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 17),
                BuildGas(2),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 19),
                GridBuilding(UnitTypeId.GATEWAY, 2),
                BuildOrder(
                    AutoPylon(),
                    ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 22),
                    SequentialList(
                        Step(UnitReady(UnitTypeId.CYBERNETICSCORE, 1), GridBuilding(UnitTypeId.TWILIGHTCOUNCIL, 1),),
                        Step(UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), Tech(UpgradeId.BLINKTECH)),
                    ),
                    SequentialList(
                        Step(
                            None,
                            GridBuilding(UnitTypeId.CYBERNETICSCORE, 1),
                            skip_until=UnitReady(UnitTypeId.GATEWAY, 1),
                        ),
                        Step(
                            UnitReady(UnitTypeId.CYBERNETICSCORE, 1), ProtossUnit(UnitTypeId.ADEPT, 2, only_once=True),
                        ),
                        Tech(UpgradeId.WARPGATERESEARCH),
                        ProtossUnit(UnitTypeId.STALKER, 100),
                    ),
                    Step(UnitExists(UnitTypeId.CYBERNETICSCORE, 1), GridBuilding(UnitTypeId.GATEWAY, 4)),
                ),
            ),
            SequentialList(
                PlanZoneDefense(),
                RestorePower(),
                DistributeWorkers(),
                PlanZoneGather(),
                Step(TechReady(UpgradeId.BLINKTECH, 0.9), attack),
                PlanFinishEnemy(),
            ),
        )


class LadderBot(Stalkers4Gate):
    @property
    def my_race(self):
        return Race.Protoss
