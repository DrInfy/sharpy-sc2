from abc import abstractmethod, ABC

from sc2.unit import Unit
from sc2.units import Units


class IMemoryManager(ABC):
    @property
    @abstractmethod
    def ghost_units(self) -> Units:
        """Returns latest snapshot for all units that we know of but which are currently not visible."""
        pass

    @abstractmethod
    def get_latest_snapshot(self, unit_tag: int) -> Unit:
        """Returns the latest snapshot of a unit. Throws KeyError if unit_tag is not found."""
        pass

    @abstractmethod
    def is_unit_visible(self, unit_tag: int) -> bool:
        pass
