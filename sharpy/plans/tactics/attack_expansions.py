# Starts all out attack with workers on specified unit supply that is not workers
import random

from sharpy.managers.roles import UnitTask
from sharpy.plans.acts import ActBase
from sc2.unit import Unit


# Plan that blocks any further strategies until an all-out attack has been started and ended
class PlanFinishEnemy(ActBase):
    def __init__(self):
        super().__init__()

    async def execute(self):
        target = await self.find_attack_position(self.ai)
        for unit in self.ai.units.idle: # type: Unit
            if self.knowledge.should_attack(unit):
                self.do(unit.attack(target))
                self.knowledge.roles.set_task(UnitTask.Attacking, unit)

        return True

    async def find_attack_position(self, ai):
        main_pos = self.knowledge.own_main_zone.center_location

        target = random.choice(list(ai.expansion_locations))
        last_distance2 = target.distance_to(main_pos)
        target_known = False
        if ai.enemy_structures.exists:
            for building in ai.enemy_structures:
                if building.health > 0:
                    current_distance2 = target.distance_to(main_pos)
                    if not target_known or current_distance2 < last_distance2:
                        target = building.position
                        last_distance2 = current_distance2
                        target_known = True
        return target






