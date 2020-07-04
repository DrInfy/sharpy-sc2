from sharpy.plans.acts import *
from sharpy.plans.acts.protoss import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans.tactics.protoss import *
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sharpy.knowledges import KnowledgeBot, Knowledge
from sc2 import UnitTypeId, Race
from sc2.ids.upgrade_id import UpgradeId


class TheAttack(PlanZoneAttack):
    pass
    # async def start(self, knowledge: Knowledge):
    #     await super().start(knowledge)
    #     self.combat.move_formation = Formation.Nothing
    #     self.combat.offensive_stutter_step = False


class MacroRobo(KnowledgeBot):
    def __init__(self):
        super().__init__("Sharp Robots")

    async def create_plan(self) -> BuildOrder:
        attack = TheAttack(4)
        return BuildOrder(
            Step(
                None,
                ChronoUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS),
                skip=UnitExists(UnitTypeId.PROBE, 30, include_pending=True),
                skip_until=UnitExists(UnitTypeId.ASSIMILATOR, 1),
            ),
            ChronoUnit(UnitTypeId.IMMORTAL, UnitTypeId.ROBOTICSFACILITY),
            SequentialList(
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 14),
                GridBuilding(UnitTypeId.PYLON, 1),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 16),
                BuildGas(1),
                GridBuilding(UnitTypeId.GATEWAY, 1),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 20),
                Expand(2),
                GridBuilding(UnitTypeId.CYBERNETICSCORE, 1),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 21),
                BuildGas(2),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 22),
                GridBuilding(UnitTypeId.PYLON, 1),
                BuildOrder(
                    AutoPylon(),
                    ProtossUnit(UnitTypeId.STALKER, 2, priority=True),
                    Tech(UpgradeId.WARPGATERESEARCH),
                    [
                        ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 22),
                        Step(UnitExists(UnitTypeId.NEXUS, 2), ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 44)),
                        StepBuildGas(3, skip=Gas(300)),
                        Step(UnitExists(UnitTypeId.NEXUS, 3), ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 56)),
                        StepBuildGas(5, skip=Gas(200)),
                    ],
                    SequentialList(
                        [
                            Step(
                                UnitReady(UnitTypeId.CYBERNETICSCORE, 1), GridBuilding(UnitTypeId.TWILIGHTCOUNCIL, 1),
                            ),
                            GridBuilding(UnitTypeId.ROBOTICSFACILITY, 1),
                            Step(UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), Tech(UpgradeId.CHARGE)),
                        ]
                    ),
                    [
                        ActUnit(UnitTypeId.IMMORTAL, UnitTypeId.ROBOTICSFACILITY, 1, priority=True),
                        ActUnit(UnitTypeId.OBSERVER, UnitTypeId.ROBOTICSFACILITY, 1, priority=True),
                        ActUnit(UnitTypeId.IMMORTAL, UnitTypeId.ROBOTICSFACILITY, 20, priority=True),
                    ],
                    Step(Time(60 * 5), Expand(3)),
                    [ProtossUnit(UnitTypeId.ZEALOT, 100)],
                    [
                        GridBuilding(UnitTypeId.GATEWAY, 4),
                        StepBuildGas(4, skip=Gas(200)),
                        GridBuilding(UnitTypeId.ROBOTICSFACILITY, 2),
                    ],
                ),
            ),
            SequentialList(
                PlanCancelBuilding(),
                PlanHeatObserver(),
                PlanZoneDefense(),
                RestorePower(),
                DistributeWorkers(),
                PlanZoneGather(),
                Step(UnitReady(UnitTypeId.IMMORTAL, 3), attack),
                PlanFinishEnemy(),
            ),
        )


class LadderBot(MacroRobo):
    @property
    def my_race(self):
        return Race.Protoss
