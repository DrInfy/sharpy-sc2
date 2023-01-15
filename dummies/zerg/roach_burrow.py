from typing import Optional, List

from sc2.data import Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit
from sharpy.interfaces import IEnemyUnitsManager

from sharpy.knowledges import KnowledgeBot
from sharpy.managers.core import ManagerBase
from sharpy.combat import GenericMicro, Action
from sharpy.plans.zerg import *


class MicroBurrowRoaches(GenericMicro):
    """
    Basic micro for Roaches that uses burrow.

    todo: take advantage of possible UpgradeId.TUNNELINGCLAWS and move while burrowed.
    todo: maybe unburrow when under
        * EffectId.SCANNERSWEEP,
        * EffectId.PSISTORMPERSISTENT,
        * revealed by raven/observer/overseer, etc.
    """

    def __init__(self):
        super().__init__()
        self.burrow_up_percentage = 0.7
        self.burrow_down_percentage = 0.4

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        burrow_ready = self.cd_manager.is_ready(unit.tag, AbilityId.BURROWDOWN_ROACH)

        if unit.is_burrowed and unit.health_percentage > self.burrow_up_percentage:
            return Action(None, False, AbilityId.BURROWUP_ROACH)

        if not unit.is_burrowed and unit.health_percentage < self.burrow_down_percentage and burrow_ready:
            return Action(None, False, AbilityId.BURROWDOWN_ROACH)

        return super().unit_solve_combat(unit, current_command)


class AutoRavager(ZergUnit):
    enemy_units_manager: IEnemyUnitsManager

    def __init__(self):
        """
        @summary Make ravagers according to the enemy siege tanks and photon cannons
        """
        super().__init__(UnitTypeId.RAVAGER, 0, True, False)

    async def start(self, knowledge: "Knowledge"):
        self.enemy_units_manager = knowledge.get_required_manager(IEnemyUnitsManager)
        await super().start(knowledge)

    async def execute(self) -> bool:
        self.to_count = 0
        self.to_count += self.enemy_units_manager.unit_count(UnitTypeId.SIEGETANK)
        self.to_count += self.enemy_units_manager.unit_count(UnitTypeId.PHOTONCANNON)
        return await super().execute()


class RoachBurrowBuild(BuildOrder):
    def __init__(self):
        super().__init__(
            Step(None, AutoRavager(), skip_until=Supply(20, SupplyType.Workers)),
            Step(Any(Supply(13, SupplyType.Workers), SupplyLeft(0)), AutoOverLord()),
            SequentialList(
                # Opener
                Step(UnitExists(UnitTypeId.DRONE, 13), ZergUnit(UnitTypeId.OVERLORD, 2, priority=True)),
                Step(UnitExists(UnitTypeId.DRONE, 16), Expand(2, priority=True)),
                StepBuildGas(1),
                Step(Supply(17), ActBuilding(UnitTypeId.SPAWNINGPOOL)),
                Step(Supply(20), ZergUnit(UnitTypeId.QUEEN, 1, priority=True)),
                Step(Supply(20), ZergUnit(UnitTypeId.ZERGLING, 6)),
                Step(Gas(100), Tech(UpgradeId.BURROW)),
                Step(Supply(24), ActBuilding(UnitTypeId.ROACHWARREN)),
                Step(Supply(24), ZergUnit(UnitTypeId.QUEEN, 2, priority=True)),
                Step(Supply(27), ZergUnit(UnitTypeId.ROACH, 5)),
                StepBuildGas(2),
                Step(None, ZergUnit(UnitTypeId.ROACH, 999)),
            ),
            SequentialList(
                # Workers
                ZergUnit(UnitTypeId.DRONE, 25),
                # Step(self.zones_are_safe, ZergUnit(UnitTypeId.DRONE, 80), skip=self.ideal_workers_reached),
            ),
        )


class RoachBurrowBot(KnowledgeBot):
    """
    Dummy bot that rushes to roaches and burrow for an early timing attack.
    """

    def __init__(self):
        super().__init__("Blunt Burrow")

    def configure_managers(self) -> Optional[List[ManagerBase]]:
        # Set the burrow roach micro
        self.combat.default_rules.unit_micros[UnitTypeId.ROACH] = MicroBurrowRoaches()
        return []

    async def create_plan(self) -> BuildOrder:
        attack = PlanZoneAttack(8)
        attack.retreat_multiplier = 0.01
        return BuildOrder(
            CounterTerranTie([RoachBurrowBuild()]),
            SequentialList(
                MineOpenBlockedBase(),
                OverlordScout(),
                DistributeWorkers(),
                Step(None, SpeedMining(), lambda ai: ai.client.game_step > 5),
                InjectLarva(),
                PlanZoneDefense(),
                PlanZoneGather(),
                attack,
                PlanFinishEnemy(),
            ),
        )


class LadderBot(RoachBurrowBot):
    @property
    def my_race(self):
        return Race.Zerg
