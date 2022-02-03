from typing import Optional, List

from sc2.data import Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sharpy.combat.group_combat_manager import GroupCombatManager
from sharpy.managers.core import *
from sharpy.managers.core import ActManager, GatherPointSolver
from sharpy.managers.core import EnemyUnitsManager
from sharpy.managers.extensions import MemoryManager
from sharpy.plans.acts import *
from sharpy.plans.acts.protoss import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sharpy.knowledges import SkeletonBot
from sc2.ids.upgrade_id import UpgradeId


class Stalkers4Gate(SkeletonBot):
    def __init__(self):
        super().__init__("The Sharp Four")

    def configure_managers(self) -> Optional[List[ManagerBase]]:
        return [
            MemoryManager(),
            PreviousUnitsManager(),
            LostUnitsManager(),
            EnemyUnitsManager(),
            UnitCacheManager(),
            UnitValue(),
            UnitRoleManager(),
            PathingManager(),
            ZoneManager(),
            BuildingSolver(),
            IncomeCalculator(),
            CooldownManager(),
            GroupCombatManager(),
            GatherPointSolver(),
            ActManager(self.create_plan()),
        ]

    def create_plan(self) -> BuildOrder:
        attack = PlanZoneAttack(6)
        attack.attack_on_advantage = False  # Disables requirement for game analyzer
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
                Step(None, SpeedMining(), lambda ai: ai.client.game_step > 5),
                PlanZoneGather(),
                Step(TechReady(UpgradeId.BLINKTECH, 0.9), attack),
                PlanFinishEnemy(),
            ),
        )


class LadderBot(Stalkers4Gate):
    @property
    def my_race(self):
        return Race.Protoss
