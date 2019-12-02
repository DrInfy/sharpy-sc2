from sharpy.knowledges import Knowledge
from sharpy.general.extended_power import ExtendedPower
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units


class EnemyData:
    close_enemies: Units
    enemy_center: Point2
    closest: Unit

    def __init__(self, knowledge: Knowledge, close_enemies: Units, unit: Unit, our_units: Units, our_median: Point2):
        self.ai = knowledge.ai
        self.our_units = our_units
        self.our_median = our_median

        self.close_enemies = close_enemies
        self.my_height = self.ai.get_terrain_height(unit)
        self.enemy_power = ExtendedPower(knowledge.unit_values)
        self.our_power = ExtendedPower(knowledge.unit_values)

        for unit in our_units: # type: Unit
            self.our_power.add_unit(unit)

        self.worker_only = False

        if self.close_enemies.exists:
            self.enemy_center = close_enemies.center
            # Can be empty!
            self.powered_enemies = close_enemies.filter(lambda x: knowledge.unit_values.power(x) > 0.1)

            if self.powered_enemies.exists:
                self.closest = unit.position.closest(self.powered_enemies)
                self.worker_only = True
                for enemy in self.powered_enemies: # type: Unit
                    if not knowledge.unit_values.is_worker(enemy):
                        self.worker_only = False
                    self.enemy_power.add_unit(enemy)
            else:
                self.closest = unit.position.closest(self.close_enemies)

            self.enemy_center_height = self.ai.get_terrain_height(self.enemy_center)
            self.closest_height = self.ai.get_terrain_height(self.closest)
        else:
            self.powered_enemies = Units([], self.ai) # empty list

    @property
    def enemies_exist(self) -> bool:
        return self.close_enemies.exists
