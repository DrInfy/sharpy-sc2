from typing import Dict

from sharpy.managers import ManagerBase
from sc2.unit import Unit


class PreviousUnitsManager(ManagerBase):
    """Keeps track of units from the previous iteration. Useful for checking eg. which unit died."""
    def __init__(self):
        super().__init__()
        self.previous_units: Dict[int, Unit] = dict()

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)

    async def update(self):
        pass

    async def post_update(self):
        """Updates previous units so we know what they are on the next iteration.
        Needs to be run right before the end of an iteration."""
        self.previous_units = dict()

        for unit in self.knowledge.all_own:  # type: Unit
            if unit.tag in self.previous_units:
                self.print(f"Unit {unit} is already present in previous_units!")
            self.previous_units[unit.tag] = unit

        for enemy_unit in self.knowledge.known_enemy_units:  # type: Unit
            if enemy_unit.tag in self.previous_units:
                self.print(f"Enemy unit {enemy_unit} is already present in previous_units!")
            self.previous_units[enemy_unit.tag] = enemy_unit
