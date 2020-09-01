import numpy as np
from typing import Dict, Union, Optional, List, Iterable

from scipy.spatial.ckdtree import cKDTree

from sharpy.managers.unit_value import race_townhalls
from sc2.constants import FakeEffectID
from sc2.game_state import EffectData
from sc2.position import Point2
from sc2.units import Units

from sharpy.managers.manager_base import ManagerBase
from sc2 import UnitTypeId
from sc2.unit import Unit
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sharpy.knowledges import Knowledge


class UnitCacheManager(ManagerBase):
    """Provides performance optimized methods for filtering both own and enemy units based on unit type and position."""

    all_own: Units
    empty_units: Units
    mineral_wall: Units

    def __init__(self):
        super().__init__()
        self.tag_cache: Dict[int, Unit] = {}
        self.own_unit_cache: Dict[UnitTypeId, Units] = {}
        self.enemy_unit_cache: Dict[UnitTypeId, Units] = {}
        self.own_tree: Optional[cKDTree] = None
        self.enemy_tree: Optional[cKDTree] = None
        self.force_fields: List[EffectData] = []

        self.own_numpy_vectors: List[np.ndarray] = []
        self.enemy_numpy_vectors: List[np.ndarray] = []
        self.mineral_fields: Dict[Point2, Unit] = {}
        self.mineral_wall: Units = {}

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.all_own: Units = Units([], self.ai)
        self.empty_units: Units = Units([], self.ai)
        self.mineral_wall: Units = Units([], self.ai)

    def by_tag(self, tag: int) -> Optional[Unit]:
        return self.tag_cache.get(tag, None)

    def by_tags(self, tags: List[int]) -> Units:
        units = Units([], self.ai)
        for tag in tags:
            unit = self.tag_cache.get(tag, None)
            if unit:
                units.append(unit)
        return units

    def own(self, type_id: Union[UnitTypeId, Iterable[UnitTypeId]]) -> Units:
        """Returns all own units of the specified type(s)."""
        if isinstance(type_id, UnitTypeId):
            return self.own_unit_cache.get(type_id, self.empty_units)

        units = Units([], self.ai)
        for single_type in type_id:  # type: UnitTypeId
            units.extend(self.own_unit_cache.get(single_type, self.empty_units))
        return units

    @property
    def own_townhalls(self) -> Units:
        """Returns all of our own townhalls."""
        # Provided for completeness, even though we could just call ai.townhalls property directly.
        return self.ai.townhalls

    def enemy(self, type_id: Union[UnitTypeId, Iterable[UnitTypeId]]) -> Units:
        """Returns all enemy units of the specified type(s)."""
        if isinstance(type_id, UnitTypeId):
            return self.enemy_unit_cache.get(type_id, self.empty_units)

        units = Units([], self.ai)
        for single_type in type_id:  # type: UnitTypeId
            units.extend(self.enemy_unit_cache.get(single_type, self.empty_units))
        return units

    @property
    def enemy_townhalls(self) -> Units:
        """Returns all known enemy townhalls."""
        enemy_townhall_types = race_townhalls[self.knowledge.enemy_race]
        return self.enemy(enemy_townhall_types)

    def own_in_range(self, position: Point2, range: Union[int, float]) -> Units:
        units = Units([], self.ai)
        if self.own_tree is None:
            return units

        for index in self.own_tree.query_ball_point(np.array([position.x, position.y]), range):
            units.append(self.all_own[index])

        return units

    def enemy_in_range(self, position: Point2, range: Union[int, float], only_targetable=True) -> Units:
        units = Units([], self.ai)
        if self.enemy_tree is None:
            return units

        for index in self.enemy_tree.query_ball_point(np.array([position.x, position.y]), range):
            units.append(self.knowledge.known_enemy_units[index])

        if only_targetable:
            return units.filter(lambda x: x.can_be_attacked or x.is_snapshot)
        return units

    async def update(self):
        self.update_minerals()

        self.tag_cache.clear()
        self.own_unit_cache.clear()
        self.enemy_unit_cache.clear()
        self.force_fields.clear()

        self.own_numpy_vectors = []
        self.enemy_numpy_vectors = []
        self.all_own = self.knowledge.all_own

        for unit in self.all_own:
            units = self.own_unit_cache.get(unit.type_id, Units([], self.ai))
            if units.amount == 0:
                self.own_unit_cache[unit.type_id] = units
            units.append(unit)
            self.own_numpy_vectors.append(np.array([unit.position.x, unit.position.y]))

        for unit in self.knowledge.known_enemy_units:
            if unit.is_memory:
                self.tag_cache[unit.tag] = unit

            units = self.enemy_unit_cache.get(unit.type_id, Units([], self.ai))
            if units.amount == 0:
                self.enemy_unit_cache[unit.type_id] = units
            units.append(unit)
            self.enemy_numpy_vectors.append(np.array([unit.position.x, unit.position.y]))

        for unit in self.ai.all_units:
            # Add all non-memory units to unit tag cache
            self.tag_cache[unit.tag] = unit

        if len(self.own_numpy_vectors) > 0:
            self.own_tree = cKDTree(self.own_numpy_vectors)
        else:
            self.own_tree = None

        if len(self.enemy_numpy_vectors) > 0:
            self.enemy_tree = cKDTree(self.enemy_numpy_vectors)
        else:
            self.enemy_tree = None

        for effect in self.ai.state.effects:
            if effect.id == FakeEffectID.get(UnitTypeId.FORCEFIELD.value):
                self.force_fields.append(effect)

    async def post_update(self):
        if self.debug:
            for mf in self.mineral_wall:
                self.debug_text_on_unit(mf, "WALL")

    def update_minerals(self):
        self.mineral_fields.clear()
        self.mineral_wall.clear()

        for mf in self.ai.mineral_field:  # type: Unit
            self.mineral_fields[mf.position] = mf
            if mf.position not in self.ai._resource_location_to_expansion_position_dict:
                self.mineral_wall.append(mf)
