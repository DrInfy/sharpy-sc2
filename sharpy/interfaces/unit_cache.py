from abc import abstractmethod, ABC
from typing import Optional, List, Union, Iterable, Dict, Tuple

from sc2.ids.effect_id import EffectId

from sc2.game_state import EffectData

from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units


class IUnitCache(ABC):
    @property
    @abstractmethod
    def own_unit_cache(self) -> Dict[UnitTypeId, Units]:
        pass

    @property
    @abstractmethod
    def enemy_unit_cache(self) -> Dict[UnitTypeId, Units]:
        pass

    @property
    @abstractmethod
    def own_townhalls(self) -> Units:
        """Returns all of our own townhalls."""
        pass

    @property
    @abstractmethod
    def enemy_townhalls(self) -> Units:
        """Returns all known enemy townhalls."""
        pass

    @property
    @abstractmethod
    def enemy_workers(self) -> Units:
        pass

    @property
    @abstractmethod
    def mineral_fields(self) -> Dict[Point2, Unit]:
        pass

    @property
    @abstractmethod
    def mineral_wall(self) -> Units:
        """Returns all known mineral wall mineral field units."""
        pass

    @abstractmethod
    def by_tag(self, tag: int) -> Optional[Unit]:
        pass

    @abstractmethod
    def by_tags(self, tags: List[int]) -> Units:
        pass

    @abstractmethod
    def effects(self, id: Union[UnitTypeId, EffectId]) -> List[Tuple[Point2, EffectData]]:
        pass

    @abstractmethod
    def own(self, type_id: Union[UnitTypeId, Iterable[UnitTypeId]]) -> Units:
        """Returns all own units of the specified type(s)."""
        pass

    @abstractmethod
    def enemy(self, type_id: Union[UnitTypeId, Iterable[UnitTypeId]]) -> Units:
        """Returns all enemy units of the specified type(s)."""
        pass

    @abstractmethod
    def own_in_range(self, position: Point2, range: Union[int, float]) -> Units:
        pass

    @abstractmethod
    def enemy_in_range(self, position: Point2, range: Union[int, float], only_targetable=True) -> Units:
        pass
