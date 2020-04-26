from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Callable, Union, TYPE_CHECKING

import sc2
from sharpy.general.extended_power import ExtendedPower
from sharpy.managers.combat2.move_type import MoveType
from sc2.ids.buff_id import BuffId
from .action import Action
from .combat_units import CombatUnits

from sc2 import AbilityId, UnitTypeId, Race
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from ...general.component import Component

if TYPE_CHECKING:
    from .micro_rules import MicroRules
    from sharpy.managers import *

changelings = {
    UnitTypeId.CHANGELING,
    UnitTypeId.CHANGELINGMARINE,
    UnitTypeId.CHANGELINGMARINESHIELD,
    UnitTypeId.CHANGELINGZEALOT,
    UnitTypeId.CHANGELINGZERGLING,
    UnitTypeId.CHANGELINGZERGLINGWINGS,
}


class MicroStep(ABC, Component):
    engaged_power: ExtendedPower
    our_power: ExtendedPower
    delay_to_shoot: float
    enemies_near_by: Units
    closest_group: CombatUnits

    def __init__(self):
        self.enemy_groups: List[CombatUnits] = []
        self.ready_to_attack_ratio: float = 0.0
        self.center: Point2 = Point2((0, 0))
        self.group: CombatUnits
        self.engage_ratio = 0
        self.can_engage_ratio = 0
        self.closest_group: CombatUnits
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
    ):
        self.rules = rules

        self.focus_fired.clear()
        self.group = group
        self.move_type = move_type

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
