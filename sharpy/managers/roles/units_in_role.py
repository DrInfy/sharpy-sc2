from typing import List, Union, Set

from sharpy.managers import UnitCacheManager
from sc2 import BotAI
from sc2.unit import Unit
from sc2.units import Units

from .unit_task import UnitTask


class UnitsInRole:
    def __init__(self, task: Union[int, UnitTask], cache: UnitCacheManager, ai: BotAI):
        self.task = task
        self.units: Units = Units([], ai)
        self.tags: Set[int] = set()
        self.cache = cache

    def clear(self):
        self.units.clear()
        self.tags.clear()

    def register_units(self, units: Units):
        for unit in units:
            self.register_unit(unit)

    def register_unit(self, unit: Unit):
        if unit.tag not in self.tags:
            self.units.append(unit)
            self.tags.add(unit.tag)

    def remove_units(self, units: Units):
        for unit in units:
            self.remove_unit(unit)

    def remove_unit(self, unit: Unit):
        if unit.tag in self.tags:
            self.units.remove(unit)
            self.tags.remove(unit.tag)

    def update(self):
        self.units.clear()
        new_tags: Set[int] = set()

        for tag in self.tags:
            unit = self.cache.by_tag(tag)

            if unit is not None and unit.is_mine:
                # update unit to collection
                self.units.append(unit)
                new_tags.add(tag)

        self.tags = new_tags
