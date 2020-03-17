from typing import Optional, Dict

from sharpy.managers.combat2 import Action, MoveType, GenericMicro
from sc2 import UnitTypeId, AbilityId
from sc2.unit import Unit


class SiegingStatus():
    def __init__(self, tank: Unit):
        self.requested_time = 0
        self.status = 0
        self.requested_status: Optional[AbilityId] = None
        self.delay = (tank.tag % 10) * 0.2

    def clear_order(self):
        self.requested_status = None
        self.requested_time = 0

    def relay_order(self, tank: Unit, order: AbilityId, time: float) -> Optional[Action]:
        if order is None:
            self.clear_order()
            return None

        if self.requested_status == order:
            # Do the change when delay matches request
            delay = self.delay
            if order == AbilityId.BURROWDOWN_LURKER:
                delay = delay * 0.25

            if time > self.requested_time + delay:
                return Action(None, False, self.requested_status)
        else:
            self.requested_status = order
            self.requested_time = time
        return None


class MicroLurkers(GenericMicro):

    def __init__(self, knowledge):
        super().__init__(knowledge)
        self.siege_status: Dict[int, SiegingStatus] = {}

    def get_siege_status(self, tank: Unit) -> SiegingStatus:
        status = self.siege_status.get(tank.tag)
        if status is None:
            status = SiegingStatus(tank)
            self.siege_status[tank.tag] = status

        return status

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        relevant_enemies = self.enemies_near_by.not_flying
        siege_mode: Optional[AbilityId] = None
        status = self.get_siege_status(unit)

        if self.move_type in {MoveType.PanicRetreat, MoveType.DefensiveRetreat}:
            if unit.type_id == UnitTypeId.LURKERMPBURROWED and not relevant_enemies.exists:
                siege_mode = AbilityId.BURROWUP_LURKER
        else:

            if relevant_enemies.exists:
                distance = relevant_enemies.closest_distance_to(unit)
            else:
                distance = 100

            # distance_closest = enemies.closest.distance_to(unit)

            unsiege_threshold = 9
            if self.move_type == MoveType.SearchAndDestroy:
                unsiege_threshold = 10

            if unit.type_id == UnitTypeId.LURKERMP and distance < unsiege_threshold - 2:
                siege_mode = AbilityId.BURROWDOWN_LURKER

            if unit.type_id == UnitTypeId.LURKERMPBURROWED and distance > unsiege_threshold:
                siege_mode = AbilityId.BURROWUP_LURKER

            if unit.type_id == UnitTypeId.LURKERMPBURROWED and not relevant_enemies.exists:
                siege_mode = AbilityId.BURROWUP_LURKER

        order = status.relay_order(unit, siege_mode, self.ai.time)

        if (order and order.ability == AbilityId.BURROWDOWN_LURKER
                and self.cache.own_in_range(unit.position, 0.9375 * 2).filter(lambda u: u.is_burrowed).amount > 0):
            return current_command

        if order:
            return order

        return current_command

