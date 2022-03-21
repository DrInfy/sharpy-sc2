from abc import ABC
from typing import List, Dict, Optional, TYPE_CHECKING

from sharpy.general.extended_power import ExtendedPower
from sharpy.combat.move_type import MoveType
from sc2.ids.buff_id import BuffId
from .action import Action
from .combat_units import CombatUnits

from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from sharpy.general.component import Component

if TYPE_CHECKING:
    from .micro_rules import MicroRules

changelings = {
    UnitTypeId.CHANGELING,
    UnitTypeId.CHANGELINGMARINE,
    UnitTypeId.CHANGELINGMARINESHIELD,
    UnitTypeId.CHANGELINGZEALOT,
    UnitTypeId.CHANGELINGZERGLING,
    UnitTypeId.CHANGELINGZERGLINGWINGS,
}


class MicroStep(ABC, Component):
    rules: "MicroRules"
    engaged_power: ExtendedPower
    our_power: ExtendedPower
    delay_to_shoot: float
    enemies_near_by: Units
    closest_group: CombatUnits
    closest_group_distance: float
    original_target: Point2
    group: CombatUnits

    def __init__(self):
        self.enemy_groups: List[CombatUnits] = []
        self.ready_to_attack_ratio: float = 0.0
        self.center: Point2 = Point2((0, 0))
        self.engage_ratio = 0
        self.can_engage_ratio = 0
        self.engaged: Dict[int, List[int]] = dict()

        self.closest_units: Dict[int, Optional[Unit]] = dict()
        self.move_type = MoveType.Assault
        self.attack_range = 0
        self.enemy_attack_range = 0

        self.focus_fired: Dict[int, float] = dict()

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.engaged_power = ExtendedPower(knowledge.unit_values)
        self.our_power = ExtendedPower(knowledge.unit_values)

    def init_group(
        self,
        rules: "MicroRules",
        group: CombatUnits,
        units: Units,
        enemy_groups: List[CombatUnits],
        move_type: MoveType,
        original_target: Point2,
    ):
        self.rules = rules

        self.focus_fired.clear()
        self.group = group
        self.move_type = move_type
        self.original_target = original_target
        self.our_power = group.power
        self.closest_units.clear()
        self.engaged_power.clear()

        self.rules.init_group_func(self, group, units, enemy_groups, move_type)

    def ready_to_shoot(self, unit: Unit) -> bool:
        return self.rules.ready_to_shoot_func(self, unit)

    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        return self.rules.group_solve_combat_func(self, units, current_command)

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        return self.rules.unit_solve_combat_func(self, unit, current_command)

    def focus_fire(self, unit: Unit, current_command: Action, prio: Optional[Dict[UnitTypeId, int]]) -> Action:
        return self.rules.focus_fire_func(self, unit, current_command, prio)

    def melee_focus_fire(
        self, unit: Unit, current_command: Action, prio: Optional[Dict[UnitTypeId, int]] = None
    ) -> Action:
        return self.rules.melee_focus_fire_func(self, unit, current_command, prio)

    def last_targeted(self, unit: Unit) -> Optional[int]:
        if unit.orders:
            # action: UnitCommand
            # current_action: UnitOrder
            current_action = unit.orders[0]
            # targeting unit
            if isinstance(current_action.target, int):
                # tag found
                return current_action.target
        return None

    def is_locked_on(self, unit: Unit) -> bool:
        if unit.has_buff(BuffId.LOCKON):
            return True
        return False

    def is_target(self, unit: Unit) -> bool:
        return not unit.is_memory and unit.can_be_attacked and not unit.is_hallucination and not unit.is_snapshot

    def min_range(self, unit: Unit) -> float:
        """ If a unit can attack both ground and air return the minimum of the attack ranges. """
        ground_range = self.unit_values.ground_range(unit)
        air_range = self.unit_values.air_range(unit)
        if not self.unit_values.can_shoot_air(unit):
            return ground_range
        if not self.unit_values.can_shoot_ground(unit):
            return air_range
        return min(ground_range, air_range)

    def max_range(self, unit: Unit) -> float:
        """ If a unit can attack both ground and air return the maximum of the attack ranges. """
        ground_range = self.unit_values.ground_range(unit)
        air_range = self.unit_values.air_range(unit)
        if not self.unit_values.can_shoot_air(unit):
            return ground_range
        if not self.unit_values.can_shoot_ground(unit):
            return air_range
        return max(ground_range, air_range)
