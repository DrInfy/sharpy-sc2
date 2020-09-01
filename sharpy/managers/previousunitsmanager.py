from typing import Dict

from sc2.position import Point2
from sharpy.managers import ManagerBase
from sc2.unit import Unit


class PreviousUnitsManager(ManagerBase):
    """Keeps track of units from the previous iteration. Useful for checking eg. which unit died."""

    def __init__(self):
        super().__init__()
        self.previous_units: Dict[int, Unit] = dict()

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)

    async def update(self):
        pass

    def last_position(self, unit: Unit) -> Point2:
        """
        Return unit position in last frame, or current if unit was just created.
        """
        previous_unit = self.previous_units.get(unit.tag, unit)
        return previous_unit.position

    async def post_update(self):
        """Updates previous units so we know what they are on the next iteration.
        Needs to be run right before the end of an iteration."""
        self.previous_units = dict()

        for unit in self.ai.all_units:  # type: Unit
            self.previous_units[unit.tag] = unit
