from sharpy.plans.acts import *
from sharpy.plans.acts.protoss import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sharpy.knowledges import KnowledgeBot, Knowledge
from sc2 import UnitTypeId, Race
from sc2.ids.upgrade_id import UpgradeId


class TheAttack(PlanZoneAttack):
    pass
    # async def start(self, knowledge: Knowledge):
    #     await super().start(knowledge)
    #     #self.combat.move_formation = Formation.Nothing
    #     self.combat.offensive_stutter_step = False


class MacroVoidray(KnowledgeBot):

    def __init__(self):
        super().__init__("Sharp Rays")

    async def create_plan(self) -> BuildOrder:
        attack = TheAttack(4)
        return BuildOrder([
            Step(None, ChronoUnitProduction(UnitTypeId.PROBE, UnitTypeId.NEXUS),
                 skip=RequiredUnitExists(UnitTypeId.PROBE, 30, include_pending=True), skip_until=RequiredUnitExists(UnitTypeId.ASSIMILATOR, 1)),
            ChronoUnitProduction(UnitTypeId.VOIDRAY, UnitTypeId.STARGATE),
            
            SequentialList([
                ProtossUnit(UnitTypeId.PROBE, 14),
                GridBuilding(UnitTypeId.PYLON, 1),
                ProtossUnit(UnitTypeId.PROBE, 16),
                StepBuildGas(1),
                GridBuilding(UnitTypeId.GATEWAY, 1),
                ProtossUnit(UnitTypeId.PROBE, 20),
                GridBuilding(UnitTypeId.CYBERNETICSCORE, 1),
                ProtossUnit(UnitTypeId.PROBE, 21),
                ActExpand(2),
                ProtossUnit(UnitTypeId.PROBE, 22),
                StepBuildGas(2),
                GridBuilding(UnitTypeId.PYLON, 1),
                BuildOrder(
                [
                    AutoPylon(),
                    GateUnit(UnitTypeId.STALKER, 2, priority=True),
                    ActTech(UpgradeId.WARPGATERESEARCH),
                    [
                        ProtossUnit(UnitTypeId.PROBE, 22),
                        Step(RequiredUnitExists(UnitTypeId.NEXUS, 2), ProtossUnit(UnitTypeId.PROBE, 44)),
                        StepBuildGas(3, skip=RequiredGas(300)),
                        Step(RequiredUnitExists(UnitTypeId.NEXUS, 3), ProtossUnit(UnitTypeId.PROBE, 56)),
                        StepBuildGas(5, skip=RequiredGas(200)),
                    ],
                    SequentialList(
                    [
                        Step(RequiredUnitReady(UnitTypeId.CYBERNETICSCORE, 1),
                             GridBuilding(UnitTypeId.TWILIGHTCOUNCIL, 1)),
                        GridBuilding(UnitTypeId.STARGATE, 1),
                        Step(RequiredUnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
                             ActTech(UpgradeId.CHARGE)),
                        Step(RequiredUnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
                             ActTech(UpgradeId.ADEPTPIERCINGATTACK)),
                    ]),
                    [
                        ProtossUnit(UnitTypeId.VOIDRAY, 20, priority=True)
                    ],
                    Step(RequiredTime(60*5), ActExpand(3)),
                    [
                        GateUnit(UnitTypeId.ZEALOT, 6),
                        GateUnit(UnitTypeId.ADEPT, 10),
                        GateUnit(UnitTypeId.ZEALOT, 15),
                        GateUnit(UnitTypeId.ADEPT, 20),
                        GateUnit(UnitTypeId.ZEALOT, 23),
                        GateUnit(UnitTypeId.ADEPT, 30)
                    ],
                    [
                        GridBuilding(UnitTypeId.GATEWAY, 4),
                        StepBuildGas(4, skip=RequiredGas(200)),
                        GridBuilding(UnitTypeId.STARGATE, 2),
                    ]
                ])
            ]),
            SequentialList(
            [
                PlanZoneDefense(),
                RestorePower(),
                PlanDistributeWorkers(),
                PlanZoneGather(),
                Step(RequiredUnitReady(UnitTypeId.VOIDRAY, 3), attack),
                PlanFinishEnemy(),
            ])
        ])


class LadderBot(MacroVoidray):
    @property
    def my_race(self):
        return Race.Protoss
