import numpy as np
from typing import Dict, Union, Optional, List, Iterable, Tuple, Callable

from sc2.data import race_townhalls
from sc2.ids.effect_id import EffectId
from scipy.spatial.ckdtree import cKDTree

from sharpy.interfaces import IUnitCache
from sc2.constants import FakeEffectID
from sc2.game_state import EffectData
from sc2.position import Point2
from sc2.units import Units

from sharpy.managers.core.manager_base import ManagerBase
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sharpy.knowledges import Knowledge

filter_units = {UnitTypeId.ADEPTPHASESHIFT, UnitTypeId.DISRUPTORPHASED, UnitTypeId.LARVA, UnitTypeId.EGG}


class UnitCacheManager(ManagerBase, IUnitCache):
    """Provides performance optimized methods for filtering both own and enemy units based on unit type and position."""

    all_own: Units
    empty_units: Units
    _mineral_wall: Units
    _enemy_workers: Units

    def __init__(self):
        super().__init__()
        self.tag_cache: Dict[int, Unit] = {}
        self._own_unit_cache: Dict[UnitTypeId, Units] = {}
        self._enemy_unit_cache: Dict[UnitTypeId, Units] = {}
        self.own_tree: Optional[cKDTree] = None
        self.enemy_tree: Optional[cKDTree] = None
        self.force_fields: List[EffectData] = []

        self._effects_cache: Dict[Union[str, EffectId], List[Tuple[Point2, EffectData]]] = {}

        self.own_numpy_vectors: List[np.ndarray] = []
        self.enemy_numpy_vectors: List[np.ndarray] = []
        self._mineral_fields: Dict[Point2, Unit] = {}

        # Set this to false to provide cloaked units to zones and unit micro making use of enemy_in_range method.
        self.only_targetable_enemies_default: bool = True
        self.range_filter: Optional[Callable[[], bool]] = lambda unit: unit.type_id not in filter_units

    @property
    def own_unit_cache(self) -> Dict[UnitTypeId, Units]:
        return self._own_unit_cache

    @property
    def enemy_unit_cache(self) -> Dict[UnitTypeId, Units]:
        return self._enemy_unit_cache

    @property
    def enemy_workers(self) -> Units:
        return self._enemy_workers

    @property
    def mineral_fields(self) -> Dict[Point2, Unit]:
        return self._mineral_fields

    @property
    def mineral_wall(self) -> Units:
        return self._mineral_wall

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.all_own: Units = Units([], self.ai)
        self.empty_units: Units = Units([], self.ai)
        self._mineral_wall: Units = Units([], self.ai)
        self._enemy_workers: Units = Units([], self.ai)

    def by_tag(self, tag: int) -> Optional[Unit]:
        return self.tag_cache.get(tag, None)

    def by_tags(self, tags: List[int]) -> Units:
        units = Units([], self.ai)
        for tag in tags:
            unit = self.tag_cache.get(tag, None)
            if unit:
                units.append(unit)
        return units

    def effects(self, id: Union[UnitTypeId, EffectId]) -> List[Tuple[Point2, EffectData]]:
        if isinstance(id, UnitTypeId):
            return self._effects_cache[FakeEffectID.get(id.value)]
        return self._effects_cache.get(id, [])

    def own(self, type_id: Union[UnitTypeId, Iterable[UnitTypeId]]) -> Units:
        """Returns all own units of the specified type(s)."""
        if isinstance(type_id, UnitTypeId):
            return self._own_unit_cache.get(type_id, self.empty_units)

        units = Units([], self.ai)
        for single_type in type_id:  # type: UnitTypeId
            units.extend(self._own_unit_cache.get(single_type, self.empty_units))
        return units

    @property
    def own_townhalls(self) -> Units:
        """Returns all of our own townhalls."""
        # Provided for completeness, even though we could just call ai.townhalls property directly.
        return self.ai.townhalls

    def enemy(self, type_id: Union[UnitTypeId, Iterable[UnitTypeId]]) -> Units:
        """Returns all enemy units of the specified type(s)."""
        if isinstance(type_id, UnitTypeId):
            return self._enemy_unit_cache.get(type_id, self.empty_units)

        units = Units([], self.ai)
        for single_type in type_id:  # type: UnitTypeId
            units.extend(self._enemy_unit_cache.get(single_type, self.empty_units))
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

    def enemy_in_range(
        self, position: Point2, range: Union[int, float], only_targetable: Optional[bool] = None
    ) -> Units:
        if only_targetable is None:
            only_targetable = self.only_targetable_enemies_default

        units = Units([], self.ai)
        if self.enemy_tree is None:
            return units

        for index in self.enemy_tree.query_ball_point(np.array([position.x, position.y]), range):
            units.append(self.ai.all_enemy_units[index])

        if only_targetable:
            if self.range_filter is not None:
                return units.filter(lambda x: self.range_filter(x) and (x.can_be_attacked or x.is_snapshot))
            return units.filter(lambda x: x.can_be_attacked or x.is_snapshot)

        if self.range_filter is not None:
            return units.filter(self.range_filter)
        return units

    async def update(self):
        self.update_minerals()

        self.tag_cache.clear()
        self._own_unit_cache.clear()
        self._enemy_unit_cache.clear()
        self.force_fields.clear()
        self._effects_cache.clear()

        self.own_numpy_vectors = []
        self.enemy_numpy_vectors = []
        self.all_own = self.ai.all_own_units

        for unit in self.all_own:
            units = self._own_unit_cache.get(unit.type_id, Units([], self.ai))
            if units.amount == 0:
                self._own_unit_cache[unit.type_id] = units
            units.append(unit)
            self.own_numpy_vectors.append(np.array([unit.position.x, unit.position.y]))

        for unit in self.ai.all_enemy_units:
            if unit.is_memory:
                self.tag_cache[unit.tag] = unit

            units = self._enemy_unit_cache.get(unit.type_id, Units([], self.ai))
            if units.amount == 0:
                self._enemy_unit_cache[unit.type_id] = units
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
            effects = self._effects_cache.get(effect.id, [])
            if len(effects) == 0:
                self._effects_cache[effect.id] = effects
            effects.append((Point2.center(effect.positions), effect))

            if effect.id == FakeEffectID.get(UnitTypeId.FORCEFIELD.value):
                self.force_fields.append(effect)

        self._enemy_workers = self.enemy([UnitTypeId.SCV, UnitTypeId.PROBE, UnitTypeId.DRONE])

    async def post_update(self):
        if self.debug:
            for mf in self._mineral_wall:
                self.debug_text_on_unit(mf, "WALL")

    def update_minerals(self):
        self._mineral_fields.clear()
        self._mineral_wall.clear()

        for mf in self.ai.mineral_field:  # type: Unit
            self._mineral_fields[mf.position] = mf
            if mf.position not in self.ai._resource_location_to_expansion_position_dict:
                self._mineral_wall.append(mf)
