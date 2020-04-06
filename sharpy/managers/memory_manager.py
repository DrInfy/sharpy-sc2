from collections import deque
from typing import Dict, Set, Deque, List

from sc2.position import Point2
from sharpy.events import UnitDestroyedEvent
from sharpy.managers import ManagerBase
from sc2 import UnitTypeId
from sc2.unit import Unit
from sc2.units import Units

MAX_SNAPSHOTS_PER_UNIT = 10


class MemoryManager(ManagerBase):
    """Manages memories of where enemy units have last been seen.

    Structures are ignored because they have two tags. One for the real building and another
    for the building's snapshot when under fog of war.
    """
    def __init__(self):
        super().__init__()

        # Dictionary of units that we remember the position of. Keyed by unit tag.
        # Deque is used so that new snapshots are added to the left, and old ones are removed from the right.
        self._memory_units_by_tag: Dict[int, Deque[Unit]] = dict()

        # Dictionary of units that we know of, but which are longer present at the location last seen. Keyed by unit tag.
        self._archive_units_by_tag: Dict[int, Deque[Unit]] = dict()

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        knowledge.register_on_unit_destroyed_listener(self.on_unit_destroyed)

    async def update(self):
        # Iterate all currently visible enemy units.
        # self.ai.enemy_units is used here because it does not include memory lane units
        for unit in self.ai.enemy_units:
            # Make sure that we have not added the same unit tag to both dictionaries, as that could
            # create very confusing bugs.
            assert not (unit.tag in self._memory_units_by_tag and unit.tag in self._archive_units_by_tag)

            # Ignore certain types
            if unit.type_id in ignored_unit_types:
                continue

            if unit.tag in self._archive_units_by_tag:
                snaps = self._archive_units_by_tag.pop(unit.tag)
            else:
                snaps = self._memory_units_by_tag.get(unit.tag, deque(maxlen=MAX_SNAPSHOTS_PER_UNIT))

            snaps.appendleft(unit)

            if unit.tag not in self._memory_units_by_tag:
                self._memory_units_by_tag[unit.tag] = snaps

        memory_tags_to_remove = list()

        for unit_tag in self._memory_units_by_tag:
            if self.is_unit_visible(unit_tag):
                continue

            snap = self.get_latest_snapshot(unit_tag)
            points: List[Point2] = []
            points.append(Point2((int(snap.position.x), int(snap.position.y))))
            points.append(Point2((int(snap.position.x + 1), int(snap.position.y))))
            points.append(Point2((int(snap.position.x), int(snap.position.y + 1))))
            points.append(Point2((int(snap.position.x + 1), int(snap.position.y + 1))))

            visible = True

            for point in points:
                if not self.ai.is_visible(point):
                    visible = False

            if visible:
                # We see that the unit is no longer there.
                # todo: what about burrowed units, especially lurkers?
                memory_tags_to_remove.append(unit_tag)
                snaps = self._memory_units_by_tag.get(unit_tag)
                self._archive_units_by_tag[unit_tag] = snaps

        for tag in memory_tags_to_remove:
            self._memory_units_by_tag.pop(tag)

    async def post_update(self):
        if not self.debug:
            return

        for unit in self.ghost_units:  # type: Unit
            self.ai._client.debug_text_world(f"{unit.type_id.name}", unit.position3d, size=10)

    @property
    def ghost_units(self) -> Units:
        """Returns latest snapshot for all units that we know of but which are currently not visible."""
        memory_units = Units([], self.ai)

        for tag in self._memory_units_by_tag:
            if self.is_unit_visible(tag):
                continue

            snap = self.get_latest_snapshot(tag)
            memory_units.append(snap)

        return memory_units
        # return memory_units.visible

    def get_latest_snapshot(self, unit_tag: int) -> Unit:
        """Returns the latest snapshot of a unit. Throws KeyError if unit_tag is not found."""
        unit_deque = self._memory_units_by_tag[unit_tag]
        return unit_deque[0]

    def is_unit_visible(self, unit_tag: int) -> bool:
        """Returns true if the unit is visible on this frame."""
        unit: Unit = self.knowledge.unit_cache.by_tag(unit_tag)
        return unit is not None and not unit.is_memory

    def on_unit_destroyed(self, event: UnitDestroyedEvent):
        """Call this when a unit is destroyed, to make sure that the unit is erased from memory."""
        # Remove the unit from frozenh dictionaries.
        self._memory_units_by_tag.pop(event.unit_tag, None)
        self._archive_units_by_tag.pop(event.unit_tag, None)


# Will this end up being the same set as in enemy_units_manager.py ?
ignored_unit_types = {
    # Protoss
    UnitTypeId.INTERCEPTOR,

    # Terran
    UnitTypeId.MULE,
    UnitTypeId.AUTOTURRET,

    # Zerg
    # Cocoons?
    UnitTypeId.LARVA,
    UnitTypeId.LOCUSTMP,
    UnitTypeId.LOCUSTMPFLYING,
    UnitTypeId.INFESTEDTERRAN,
    UnitTypeId.BROODLING,
}
