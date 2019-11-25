from typing import Optional

from sc2.unit import Unit


class UnitDestroyedEvent:
    """An event indicating which unit just died."""

    def __init__(self, unit_tag: int, unit: Optional[Unit]):
        assert isinstance(unit_tag, int)
        assert isinstance(unit, Unit) or unit is None

        self.unit_tag: int = unit_tag
        self.unit: Optional[Unit] = unit
