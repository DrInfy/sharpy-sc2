from typing import Union, Optional

from sc2 import AbilityId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.unit_command import UnitCommand


class Action:
    target: Union[Point2, Unit]
    is_attack: bool

    def __init__(self, target: Optional[Union[Point2, Unit]],
                 is_attack: bool,
                 ability: Optional[AbilityId] = None,
                 debug_comment: Optional[str] = None):

        self.target = target
        self.is_attack = is_attack
        self.ability = ability
        self.is_final = False
        self.debug_comment = debug_comment

    def to_commmand(self, unit: Unit) -> UnitCommand:
        if self.ability is not None:
            action = unit(self.ability, self.target)
        elif self.is_attack:
            action = unit.attack(self.target)
        else:
            action = unit.move(self.target)
        return action

class NoAction(Action):
    def __init__(self):
        super().__init__(None, False)

    def to_commmand(self, unit: Unit) -> UnitCommand:
        return None