import string
from typing import Union

from sc2 import UnitTypeId


class UnitCount:
    def __init__(self, enemy_type: UnitTypeId, count: Union[int, float]):
        assert isinstance(enemy_type, UnitTypeId)
        assert isinstance(count, int) or isinstance(count, float)

        self.count = count
        self.enemy_type: UnitTypeId = enemy_type

    def __str__(self):
        name = self.enemy_type.name
        return name + ": " + str("{0:.1f}".format(self.count))

    def to_short_string(self) -> string:
        name = self.enemy_type.name[:3].lower()
        return name + " " + str("{0:.1f}".format(self.count))
