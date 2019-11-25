from typing import List, Optional, Dict

from sc2.constants import *

from frozen.combat import CombatGoal, CombatAction, EnemyData, MoveType
from .state_step import StateStep
from frozen.knowledges import Knowledge
from sc2.unit import Unit


class SiegingStatus():
    def __init__(self, tank: Unit):
        self.requested_time = 0
        self.status = 0
        self.requested_status: Optional[AbilityId]= None
        self.delay = (tank.tag % 10) * 0.4

    def clear_order(self):
        self.requested_status = None
        self.requested_time = 0

    def relay_order(self, tank: Unit, order:AbilityId, time:float) -> List[CombatAction]:
        if order is None:
            self.clear_order()
            return []

        if self.requested_status == order:
            # Do the change when delay matches request
            delay = self.delay
            if order == AbilityId.SIEGEMODE_SIEGEMODE:
                delay = delay * 0.25

            if time > self.requested_time + delay:
                return [CombatAction(tank, None, False, self.requested_status)]
        else:
            self.requested_status = order
            self.requested_time = time
        return []

class StateSiegetank(StateStep):
    def __init__(self, knowledge: Knowledge):
        super().__init__(knowledge)
        self.knowledge = knowledge
        self.siege_status: Dict[int, SiegingStatus] = {}

    def get_siege_status(self, tank: Unit)->  SiegingStatus:
        status = self.siege_status.get(tank.tag)
        if status is None:
            status = SiegingStatus(tank)
            self.siege_status[tank.tag] = status

        return status

    def FinalSolve(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> CombatAction:
        if goal.unit.type_id == UnitTypeId.SIEGETANKSIEGED and not enemies.close_enemies.not_flying.exists:
            status = self.get_siege_status(goal.unit)
            orders = status.relay_order(goal.unit, AbilityId.UNSIEGE_UNSIEGE, self.ai.time)
            if len(orders) > 0:
                return orders[0]

        return command

    def solve_combat(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> List[CombatAction]:
        if not self.knowledge.known_enemy_units.exists:
            return []

        relevant_enemies = enemies.powered_enemies.not_flying.visible

        if relevant_enemies.exists:
            distance = relevant_enemies.closest_distance_to(goal.unit)
        else:
            distance = 100

        distance_closest = enemies.closest.distance_to(goal.unit)

        unsiege_threshold = 15
        if goal.move_type == MoveType.SearchAndDestroy:
            unsiege_threshold = 20

        status = self.get_siege_status(goal.unit)


        if goal.unit.type_id == UnitTypeId.SIEGETANK and distance > 5 and distance < 13:
            # don't siege up on the main base ramp!
            if goal.unit.distance_to(self.knowledge.enemy_base_ramp.bottom_center) > 7:
                return status.relay_order(goal.unit, AbilityId.SIEGEMODE_SIEGEMODE, self.ai.time)

        if (distance_closest > unsiege_threshold or not enemies.closest.is_visible) and \
                (goal.unit.type_id == UnitTypeId.SIEGETANKSIEGED and distance > unsiege_threshold):
            return status.relay_order(goal.unit, AbilityId.UNSIEGE_UNSIEGE, self.ai.time)

        status.clear_order()
        return []
