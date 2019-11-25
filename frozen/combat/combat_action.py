from typing import Union, Optional

from sc2 import AbilityId
from sc2.position import Point2
from sc2.unit import Unit


class CombatAction:
    target: Union[Point2, Unit]
    unit: Unit
    is_attack: bool

    def __init__(self, unit: Unit, target: Optional[Union[Point2, Unit]], is_attack: bool, ability: Optional[AbilityId] = None):
        self.unit = unit
        self.target = target
        self.is_attack = is_attack
        self.ability = ability
        self.is_final = False
