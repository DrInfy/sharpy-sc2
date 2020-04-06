from sharpy import sc2math
from sharpy.managers.combat2.micro_step import MicroStep
from sharpy.managers.combat2 import Action
from sc2 import AbilityId, Race, UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units


class MicroWorkers(MicroStep):
    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        if self.engage_ratio > 0.5 and self.closest_group:
            if self.ready_to_attack_ratio > 0.8 or self.closest_group_distance < 2:
                return Action(self.closest_group.center, True)
            if self.ready_to_attack_ratio < 0.25:
                return Action(self.closest_group.center, True)
            return Action(self.closest_group.center.towards(self.center, -3), False)
        #if self.engage_percentage == 0
        return current_command

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        if self.closest_group and self.engaged_power.melee_percentage > 0.9:
            backstep: Point2 = unit.position.towards(self.closest_group.center, -3)
            if ((unit.health + unit.shield <= 5 and not self.ready_to_shoot(unit))
                    or (unit.shield_health_percentage < 0.5 and unit.weapon_cooldown > 9)):
                backstep = self.pather.find_weak_influence_ground(backstep, 4)
                if self.cache.own_in_range(unit.position, 1) or self.cache.enemy_in_range(unit.position, 1):
                    # Mineral walk
                    angle = sc2math.line_angle(unit.position, backstep)
                    best_angle = sc2math.pi / 6
                    best_mf = None

                    for mf in self.ai.mineral_field:  # type: Unit
                        new_angle = sc2math.line_angle(unit.position, mf.position)
                        angle_distance = sc2math.angle_distance(angle, new_angle)
                        if angle_distance < best_angle:
                            best_mf = mf
                            best_angle = angle_distance

                    if best_mf:
                        # Use backstep with gather command to pass through own units
                        return Action(best_mf, False, ability=AbilityId.HARVEST_GATHER)
                return Action(backstep, False)

        if self.ready_to_shoot(unit):
            if self.closest_group:
                current = Action(self.closest_group.center, True)
            else:
                current = Action(current_command.target, True)
            return self.melee_focus_fire(unit, current)
        elif self.knowledge.enemy_race == Race.Terran:
            # Kill scv building
            nearby = self.cache.enemy_in_range(unit.position, 5)
            scvs = nearby(UnitTypeId.SCV)
            if scvs and nearby.structure.not_ready:
                scv = scvs.closest_to(unit)
                current_command = Action(scv, True)
        # if unit.health + unit.shield <= 5:
        #     backstep = self.pather.find_weak_influence_ground(backstep, 4)
        #     return Action(backstep, False)

        # if self.knowledge.enemy_race == Race.Protoss:
        #     if self.engage_percentage < 0.25:
        #         buildings = self.enemies_near_by.sorted_by_distance_to(unit)
        #         if buildings:
        #             if buildings.first.health + buildings.first.shield < 200:
        #                 return Action(buildings.first, True)
        #             pylons = buildings(UnitTypeId.PYLON)
        #             if pylons:
        #                 return Action(buildings.first, True)
        return current_command
