import random

from sharpy.plans.acts import *
from sharpy.plans.acts.protoss import *
from sharpy.plans.require import *
from sharpy.plans.tactics.protoss import *
from sharpy.plans.tactics import *
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sharpy.knowledges import KnowledgeBot

from sharpy.knowledges import Knowledge

from sharpy.general.extended_power import ExtendedPower
from sc2 import UnitTypeId, AbilityId, Race
from sc2.ids.upgrade_id import UpgradeId

class TheAttack(PlanZoneAttack):

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)
        #self.combat.move_formation = Formation.Nothing
        #self.combat.offensive_stutter_step = False

    def _should_attack(self, power: ExtendedPower) -> bool:
        return len(self.cache.own(UnitTypeId.ADEPT)) > 10


class AdeptRush(KnowledgeBot):

    def __init__(self):
        super().__init__("Sharp Shades")

    async def create_plan(self) -> BuildOrder:
        number = random.randint(10, 15)
        attack = TheAttack(number + 1)
        return BuildOrder([
            Step(None, ChronoUnitProduction(UnitTypeId.PROBE, UnitTypeId.NEXUS),
                 skip=RequiredUnitExists(UnitTypeId.PROBE, 20, include_pending=True), skip_until=RequiredUnitExists(UnitTypeId.ASSIMILATOR, 1)),
            SequentialList([
                GridBuilding(UnitTypeId.PYLON, 1),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 14),
                GridBuilding(UnitTypeId.GATEWAY, 1),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 16),
                StepBuildGas(1),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 17),
                GridBuilding(UnitTypeId.GATEWAY, 2),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 20),
                ArtosisPylon(2),
                BuildOrder(
                    [
                        AutoPylon(),
                        SequentialList(
                        [
                            Step(None, GridBuilding(UnitTypeId.CYBERNETICSCORE, 1), skip_until=RequiredUnitReady(UnitTypeId.GATEWAY, 1)),
                            Step(RequiredUnitReady(UnitTypeId.CYBERNETICSCORE, 1), GateUnit(UnitTypeId.ADEPT, 2, only_once=True)),
                            ActTech(UpgradeId.WARPGATERESEARCH),
                            GateUnit(UnitTypeId.ADEPT, 100)
                        ]),
                        Step(RequiredUnitExists(UnitTypeId.CYBERNETICSCORE, 1), GridBuilding(UnitTypeId.GATEWAY, 4),
                             skip_until=RequiredMinerals(200)),

                        Step(None, ProtossUnit(UnitTypeId.ZEALOT, 100),
                             skip=RequiredGas(25),
                             skip_until=RequiredMinerals(200)),
                    ]),


            ]),
            SequentialList(
                [
                    PlanZoneDefense(),
                    RestorePower(),
                    PlanDistributeWorkers(),
                    PlanZoneGather(),
                    DoubleAdeptScout(number),
                    attack,
                    PlanFinishEnemy(),
                ])
        ])


class LadderBot(AdeptRush):
    @property
    def my_race(self):
        return Race.Protoss
