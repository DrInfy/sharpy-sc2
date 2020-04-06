from typing import Optional, List

from sc2.position import Point2
from sharpy import sc2math
from sharpy.general.extended_power import ExtendedPower

from sc2.unit import Unit
from sc2.units import Units



class CombatUnits():
    def __init__(self, units: Units, knowledge: 'Knowledge'):
        self.knowledge = knowledge
        self.unit_values = knowledge.unit_values
        self.units = units
        self.center: Point2 = sc2math.unit_geometric_median(units)
        self.ground_units = self.units.not_flying
        if self.ground_units:
            self.center: Point2 = self.ground_units.closest_to((self.center)).position

        self.power = ExtendedPower(self.unit_values)
        self.power.add_units(self.units)
        self.debug_index = 0
        self._total_distance: Optional[float] = None
        self._area_by_circles: float = 0
        self.average_speed = 0

        for unit in self.units:
            self.average_speed += knowledge.unit_values.real_speed(unit)

        if len(self.units) > 1:
            self.average_speed /= len(self.units)

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
                if d < self.unit_values.real_range(unit, enemy_near):
                    engaged_power += power
                    break

        return engaged_power > total_power * 0.15

    def closest_target_group(self, combat_groups: List['CombatUnits']) -> Optional['CombatUnits']:
        group = None
        start = self.center
        best_distance = 50  # doesn't find enemy groups closer than this

        shoots_air = self.power.air_power > 0
        shoots_ground = self.power.ground_power > 0

        for combat_group in combat_groups:
            if not combat_group.ground_units and not shoots_air:
                continue  # We can't shoot the targets here
            if combat_group.power.air_presence == 0 and combat_group.power.ground_presence > 0 and not shoots_ground:
                continue  # We can't shoot the targets here

            if combat_group.power.air_presence > 0 and combat_group.power.ground_presence == 0 and not shoots_air:
                continue  # We can't shoot the targets here

            center = combat_group.center

            distance = start.distance_to(center)
            if distance < best_distance:
                best_distance = distance
                group = combat_group

        return group
