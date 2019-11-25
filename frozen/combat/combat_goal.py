import sc2
from sc2 import UnitTypeId, AbilityId
from sc2.position import Point2
from sc2.unit import Unit

from .move_type import MoveType


class CombatGoal:
    move_type: MoveType
    target: Point2
    unit: Unit

    def __init__(self, unit: Unit, target: Point2, move_type: MoveType):
        self.unit = unit
        self.target: Point2 = target
        self.move_type = move_type
        self.ready_to_shoot = False
        self.to_shoot = 2 # This should be the same as client.step_size

    def set_shoot_status(self, knowledge: 'Knowledge'):
        if self.unit.type_id == UnitTypeId.CYCLONE:
            # if knowledge.cooldown_manager.is_ready(self.unit.tag, AbilityId.LOCKON_LOCKON):
            #     self.ready_to_shoot = True
            #     return
            if knowledge.cooldown_manager.is_ready(self.unit.tag, AbilityId.CANCEL_LOCKON):
                self.ready_to_shoot = False
                return

        if self.unit.type_id == UnitTypeId.DISRUPTOR:
            self.ready_to_shoot = knowledge.cooldown_manager.is_ready(self.unit.tag, AbilityId.EFFECT_PURIFICATIONNOVA)
            return

        if self.unit.type_id == UnitTypeId.ORACLE:
            tick = knowledge.ai.state.game_loop % 16
            if tick < 8:
                self.ready_to_shoot = True
            else:
                self.ready_to_shoot = False
            return

        if self.unit.type_id == UnitTypeId.CARRIER:
            tick = knowledge.ai.state.game_loop % 32
            if tick < 8:
                self.ready_to_shoot = True
            else:
                self.ready_to_shoot = False
            return

        if self.unit.weapon_cooldown <= self.to_shoot:
            self.ready_to_shoot = True