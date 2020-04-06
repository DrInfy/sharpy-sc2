from typing import Optional, Dict

from sharpy.managers.combat2 import Action, MoveType, GenericMicro
from sc2 import UnitTypeId, AbilityId
from sc2.unit import Unit


class SiegingStatus():
    def __init__(self, tank: Unit):
        self.requested_time = 0
        self.status = 0
        self.requested_status: Optional[AbilityId] = None
        self.delay = (tank.tag % 10) * 0.4

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
            if order == AbilityId.SIEGEMODE_SIEGEMODE:
                delay = delay * 0.25

            if time > self.requested_time + delay:
                return Action(None, False, self.requested_status)
        else:
            self.requested_status = order
            self.requested_time = time
        return None


class MicroTanks(GenericMicro):

    def __init__(self, knowledge):
        super().__init__(knowledge)
        self.siege_status: Dict[int, SiegingStatus] = {}

    def get_siege_status(self, tank: Unit)-> SiegingStatus:
        status = self.siege_status.get(tank.tag)
        if status is None:
            status = SiegingStatus(tank)
            self.siege_status[tank.tag] = status

        return status

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        relevant_enemies = self.enemies_near_by.not_flying.visible
        siege_mode: Optional[AbilityId] = None

        if self.move_type in {MoveType.PanicRetreat, MoveType.DefensiveRetreat}:
            if unit.type_id == UnitTypeId.SIEGETANKSIEGED and not relevant_enemies.exists:
                siege_mode = AbilityId.UNSIEGE_UNSIEGE
        else:
            if relevant_enemies.exists:
                distance = relevant_enemies.closest_distance_to(unit)
            else:
                distance = 100

            # distance_closest = enemies.closest.distance_to(unit)

            unsiege_threshold = 15
            if self.move_type == MoveType.SearchAndDestroy:
                unsiege_threshold = 20

            status = self.get_siege_status(unit)

            if unit.type_id == UnitTypeId.SIEGETANK and distance > 5 and distance < 13:
                # don't siege up on the main base ramp!
                if unit.distance_to(self.knowledge.enemy_base_ramp.bottom_center) > 7:
                    siege_mode = AbilityId.SIEGEMODE_SIEGEMODE

            if distance > unsiege_threshold and \
                    (unit.type_id == UnitTypeId.SIEGETANKSIEGED and distance > unsiege_threshold):
                siege_mode = AbilityId.UNSIEGE_UNSIEGE

            if unit.type_id == UnitTypeId.SIEGETANKSIEGED and not relevant_enemies.exists:
                siege_mode = AbilityId.UNSIEGE_UNSIEGE

        status = self.get_siege_status(unit)
        order = status.relay_order(unit, siege_mode, self.ai.time)

        if order:
            return order

        if unit.type_id == UnitTypeId.SIEGETANKSIEGED:
            return current_command
        else:
            return super().unit_solve_combat(unit, current_command)

