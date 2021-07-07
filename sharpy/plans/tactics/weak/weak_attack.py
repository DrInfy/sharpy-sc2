from enum import Enum
from typing import Optional

from sharpy.interfaces import IGatherPointSolver, IZoneManager, IEnemyUnitsManager, IGameAnalyzer
from sharpy.managers.extensions import GameAnalyzer
from sharpy.plans.acts import ActBase
from sharpy.managers.extensions.game_states.advantage import (
    at_least_small_disadvantage,
    at_least_small_advantage,
    at_least_clear_advantage,
    at_least_clear_disadvantage,
)
from sharpy.general.zone import Zone
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from sharpy.managers.core.roles import UnitTask
from sharpy.combat import MoveType
from sharpy.general.extended_power import ExtendedPower
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sharpy.managers.core import *
    from sharpy.knowledges import Knowledge


ENEMY_TOTAL_POWER_MULTIPLIER = 1.2

RETREAT_TIME = 20

RETREAT_STOP_DISTANCE = 5
RETREAT_STOP_DISTANCE_SQUARED = RETREAT_STOP_DISTANCE * RETREAT_STOP_DISTANCE


class AttackStatus(Enum):
    NotActive = 0
    GatheringForAttack = 1  # Not in use yet
    Attacking = 2
    MovingToExpansion = 3  # NYI, moving to hold enemy expansion
    ProtectingExpansion = 4  # NYI, holding enemy expansion and preventing enemy expansions
    Retreat = 10  # Prefers to escape without fighting
    Withdraw = 11  # Fights any enemies while escaping


class WeakAttack(ActBase):
    gather_point_solver: IGatherPointSolver
    zone_manager: IZoneManager
    enemy_units_manager: IEnemyUnitsManager
    game_analyzer: Optional[IGameAnalyzer]
    pather: "PathingManager"

    DISTANCE_TO_INCLUDE = 18
    DISTANCE2_TO_INCLUDE = 18 * 18
    RETREAT_POWER_PERCENTAGE = 0.8

    def __init__(self, start_attack_power: float = 20):
        assert isinstance(start_attack_power, float) or isinstance(start_attack_power, int)
        super().__init__()
        self.retreat_multiplier = WeakAttack.RETREAT_POWER_PERCENTAGE
        self.attack_retreat_started: Optional[float] = None

        self.start_attack_power = start_attack_power
        self.status = AttackStatus.NotActive

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.unit_values = knowledge.unit_values
        self.pather = self.knowledge.pathing_manager
        self.game_analyzer = self.knowledge.get_manager(IGameAnalyzer)
        if self.game_analyzer is None:
            self.print(f"IGameAnalyzer not found, turning attack_on_advantage off.")
            self.attack_on_advantage = False
        self.gather_point_solver = knowledge.get_required_manager(IGatherPointSolver)
        self.zone_manager = knowledge.get_required_manager(IZoneManager)
        self.enemy_units_manager = knowledge.get_required_manager(IEnemyUnitsManager)

    async def execute(self) -> bool:
        target = self._get_target()

        if target is None:
            # Enemy known bases destroyed.
            self.status = AttackStatus.NotActive
            return True

        unit: Unit
        if self.status == AttackStatus.Attacking:
            self.handle_attack(target)

        elif self.attack_retreat_started is not None:
            attacking_units = self.roles.attacking_units
            self.roles.refresh_tasks(attacking_units)

            for unit in attacking_units:
                pos: Point2 = unit.position
                at_gather_point = pos.distance_to(self.gather_point_solver.gather_point) < RETREAT_STOP_DISTANCE_SQUARED
                if at_gather_point:
                    # self.print(f"Unit {unit.type_id} {unit.tag} has reached gather point. Stopping retreat.")
                    self.roles.clear_task(unit)
                elif self.status == AttackStatus.Withdraw:
                    self.combat.add_unit(unit)
                else:
                    self.combat.add_unit(unit)

            self.combat.execute(self.gather_point_solver.gather_point, MoveType.DefensiveRetreat)

            if self.attack_retreat_started + RETREAT_TIME < self.ai.time:
                # Stop retreat next turn
                self._stop_retreat()
        else:
            self.roles.attack_ended()
            attackers = Units([], self.ai)
            for unit in self.roles.free_units:
                if self.unit_values.should_attack(unit):
                    attackers.append(unit)

            own_power = self.unit_values.calc_total_power(attackers)

            if self._should_attack(own_power):
                self._start_attack(own_power, attackers)

        return False  # Blocks!

    async def debug_actions(self):
        if self.status == AttackStatus.NotActive:
            return

        if self.status == AttackStatus.Retreat:
            attacking_status = moving_status = "retreating"
        elif self.status == AttackStatus.Withdraw:
            attacking_status = moving_status = "withdrawing"
        elif self.status == AttackStatus.Attacking:
            moving_status = "moving"
            attacking_status = "attacking"
        elif self.status == AttackStatus.ProtectingExpansion:
            moving_status = "moving"
            attacking_status = "preventing"
        else:
            attacking_status = moving_status = "unknown attack task"

        for unit in self.roles.units(UnitTask.Moving):
            self.client.debug_text_world(moving_status, unit.position3d)
        for unit in self.roles.units(UnitTask.Attacking):
            self.client.debug_text_world(attacking_status, unit.position3d)

    def handle_attack(self, target):
        already_attacking: Units = self.roles.units(UnitTask.Attacking)
        if not already_attacking.exists:
            self.print("No attacking units, starting retreat")
            # All attacking units have been destroyed.
            self._start_retreat(AttackStatus.Retreat)
            return True

        front_runner = already_attacking.closest_to(target)
        attackers = Units([], self.ai)

        for unit in already_attacking:
            # Only units in group are included to current combat force
            attackers.append(unit)

        self.roles.refresh_tasks(already_attacking)

        for unit in self.roles.free_units:
            if self.unit_values.should_attack(unit):
                attackers.append(unit)

        # Execute
        for unit in attackers:
            unit.attack(target)

        retreat = self._should_retreat(front_runner.position, already_attacking)

        if retreat != AttackStatus.NotActive:
            self._start_retreat(retreat)

    def _should_attack(self, power: ExtendedPower) -> bool:
        enemy_total_power: ExtendedPower = self.enemy_units_manager.enemy_total_power
        enemy_total_power.multiply(ENEMY_TOTAL_POWER_MULTIPLIER)
        multiplier = ENEMY_TOTAL_POWER_MULTIPLIER

        zone_count = 0
        for zone in self.zone_manager.expansion_zones:  # type: Zone
            if zone.is_enemys:
                zone_count += 1

        enemy_main: Zone = self.zone_manager.expansion_zones[-1]
        enemy_natural: Zone = self.zone_manager.expansion_zones[-2]

        if zone_count == 1 and enemy_main.is_enemys:
            # We should seriously consider whether we want to crash and burn against a one base defense
            enemy_total_power.add_units(enemy_main.enemy_static_defenses)
            # multiplier *= 2

        elif zone_count == 2 and enemy_natural.is_enemys:
            enemy_total_power.add_units(enemy_natural.enemy_static_defenses)

        enemy_total_power.power = max(self.start_attack_power, enemy_total_power.power)

        if power.is_enough_for(enemy_total_power, 1 / multiplier):
            self.print(
                f"Power {power.power:.2f} is larger than required attack power {enemy_total_power.power:.2f} -> attack!"
            )
            return True
        if self.ai.supply_used > 190:
            self.print(f"Supply is {self.ai.supply_used} -> attack!")
            return True
        return False

    def _start_attack(self, power: ExtendedPower, attackers: Units):
        self.roles.set_tasks(UnitTask.Attacking, attackers)
        self.status = AttackStatus.Attacking
        self.print(f"Attack started at {power.power:.2f} power.")

    def _should_retreat(self, fight_center: Point2, already_attacking: Units) -> AttackStatus:
        enemy_local_units: Units = self.ai.all_enemy_units.closer_than(WeakAttack.DISTANCE_TO_INCLUDE, fight_center)

        if self.unit_values.enemy_worker_type is not None:
            enemy_local_units = enemy_local_units.exclude_type(self.unit_values.enemy_worker_type)

        own_local_power = self.unit_values.calc_total_power(already_attacking)
        enemy_local_power = self.unit_values.calc_total_power(enemy_local_units)

        if enemy_local_power.is_enough_for(own_local_power, self.retreat_multiplier):
            # Start retreat next turn
            self.print(
                f"Retreat started at {own_local_power.power:.2f} own local power "
                f"against {enemy_local_power.power:.2f} enemy local power."
            )
            return AttackStatus.Retreat

        return AttackStatus.NotActive

    def _start_retreat(self, status: AttackStatus):
        self.status = status
        self.attack_retreat_started = self.ai.time

    def _stop_retreat(self):
        self.status = AttackStatus.NotActive
        self.attack_retreat_started = None
        self.roles.attack_ended()
        self.print("Retreat stopped.")

    def _get_target(self) -> Optional[Point2]:
        our_main = self.zone_manager.expansion_zones[0].center_location
        proxy_buildings = self.ai.enemy_structures.closer_than(70, our_main)

        if proxy_buildings.exists:
            return proxy_buildings.closest_to(our_main).position

        # Select expansion to attack.
        # Enemy main zone should the last element in expansion_zones.
        enemy_zones = list(filter(lambda z: z.is_enemys, self.zone_manager.expansion_zones))

        best_zone = None
        best_score = 100000
        start_position = self.gather_point_solver.gather_point
        if self.roles.attacking_units:
            start_position = self.roles.attacking_units.center

        for zone in enemy_zones:  # type: Zone
            not_like_points = zone.center_location.distance_to(start_position)
            not_like_points += zone.enemy_static_power.power * 5
            if not_like_points < best_score:
                best_zone = zone
                best_score = not_like_points

        if best_zone is not None:
            return best_zone.center_location

        if self.ai.enemy_structures.exists:
            return self.ai.enemy_structures.closest_to(our_main).position

        return None
