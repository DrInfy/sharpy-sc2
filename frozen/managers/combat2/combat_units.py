from typing import Optional

from frozen import sc2math
from frozen.general.extended_power import ExtendedPower

from sc2.unit import Unit
from sc2.units import Units



class CombatUnits():
    def __init__(self, units: Units, knowledge: 'Knowledge'):
        self.knowledge = knowledge
        self.unit_values = knowledge.unit_values
        self.units = units
        self.center = sc2math.unit_geometric_median(units)
        self.ground_units = self.units.not_flying
        if self.ground_units:
            self.center = self.ground_units.closest_to((self.center)).position

        self.power = ExtendedPower(self.unit_values)
        self.power.add_units(self.units)
        self.debug_index = 0
        self._total_distance: Optional[float] = None
        self._area_by_circles: float = 0

    def is_too_spread_out(self) -> bool:
        if self._total_distance is None:
            self._total_distance = 0
            self._area_by_circles = 5

            for unit in self.units:
                d = unit.distance_to(self.center)
                self._total_distance += d
                self._area_by_circles += unit.radius ** 2
        # self.knowledge.print(f"spread: {self._total_distance} d to {self._total_radius} r")
        return (self._total_distance / len(self.units)) ** 2 > self._area_by_circles * 2

    def is_in_combat(self, closest_enemies: 'CombatUnits') -> bool:
        if closest_enemies is None:
            return False

        distance = self.center.distance_to_point2(closest_enemies.center)
        if distance > 17:
            return False

        if distance < 10 \
                or self.knowledge.unit_cache.enemy_in_range(self.center, 10).exclude_type(self.unit_values.combat_ignore):
           return True

        engaged_power = 0
        total_power = 0

        for unit in self.units:  # type: Unit
            power = self.unit_values.power(unit)
            total_power += power

            for enemy_near in closest_enemies.units:
                d = enemy_near.distance_to(unit)
                if d < self.unit_values.real_range(unit, enemy_near, self.knowledge):
                    engaged_power += power
                    break

        return engaged_power > total_power * 0.15
