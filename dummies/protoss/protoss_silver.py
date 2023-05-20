from typing import Optional, List

from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from sharpy.knowledges import KnowledgeBot
from sharpy.managers.extensions import BuildDetector, ChatManager
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sharpy.plans.acts import *
from sharpy.plans.acts.protoss import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans.tactics.weak import WeakAttack, WeakDefense


class SilverProtoss(KnowledgeBot):
    def __init__(self):
        super().__init__("Silver Protoss")

    def configure_managers(self) -> Optional[List["ManagerBase"]]:
        self.client.game_step = 20
        return [BuildDetector(), ChatManager()]

    async def create_plan(self) -> BuildOrder:
        return BuildOrder(
            Step(
                None,
                ChronoUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS),
                skip=UnitExists(UnitTypeId.PROBE, 40, include_pending=True),
                skip_until=UnitExists(UnitTypeId.ASSIMILATOR, 1),
            ),
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
                    Tech(UpgradeId.WARPGATERESEARCH),
                    [
                        ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 22),
                        Step(UnitExists(UnitTypeId.NEXUS, 2), ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 44)),
                        StepBuildGas(3, skip=Gas(300)),
                        GridBuilding(UnitTypeId.TWILIGHTCOUNCIL, 1, priority=True),  # this does nothing on purpose
                    ],
                    [ProtossUnit(UnitTypeId.STALKER, 100)],
                    [GridBuilding(UnitTypeId.GATEWAY, 7), StepBuildGas(4, skip=Gas(200))],
                ),
            ),
            SequentialList(
                MineOpenBlockedBase(),
                WeakDefense(),
                RestorePower(),
                DistributeWorkers(),
                # PlanZoneGather(),
                WeakAttack(30),
                PlanFinishEnemy(),
            ),
        )


class LadderBot(SilverProtoss):
    @property
    def my_race(self):
        return Race.Protoss
