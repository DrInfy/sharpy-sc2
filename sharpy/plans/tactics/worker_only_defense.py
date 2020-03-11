from typing import List, Tuple, Optional

from sharpy.managers import UnitValue
from sharpy.managers.combat2 import MoveType
from sharpy.plans.acts import ActBase
from sharpy.managers.roles import UnitTask
from sharpy.general.zone import Zone

from sc2 import UnitTypeId
from sc2.unit import Unit
from sc2.units import Units


class PlanWorkerOnlyDefense(ActBase):
    def __init__(self):
        super().__init__()
        self.defender_tags: List[int] = []

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        self.was_active = False
        self.gather_mf = self.solve_optimal_mineral_field()

    def solve_optimal_mineral_field(self) -> Unit:
        main: Zone = self.knowledge.own_main_zone
        for mf in main.mineral_fields: #type: Unit
            if len(main.mineral_fields.closer_than(2, mf.position)) > 2:
                return mf
        return main.mineral_fields.first

    async def execute(self) -> bool:
        self.defender_tags.clear()

        if self.ai.supply_army > 3:
            # Safe
            if self.was_active:
                self.free_others()
                self.was_active = False
            return True

        combined_enemies: Units = Units([], self.ai)

        for zone in self.knowledge.expansion_zones: # type: Zone
            if not zone.is_ours:
                continue

            combined_enemies |= zone.known_enemy_units

        already_defending: Units = self.knowledge.roles.units(UnitTask.Defending)

        if not combined_enemies:
            if self.was_active:
                self.free_others()
                self.was_active = False
            # Safe
            return True

        # for unit in already_defending:
        #     # return workers back to base that have wandered too far away
        #     if unit.type_id in self.unit_values.worker_types and unit.distance_to(self.ai.start_location) > 30:
        #         self.knowledge.roles.clear_task(unit)
        #         unit.gather(self.gather_mf)

        worker_only = combined_enemies.amount == combined_enemies.of_type(self.unit_values.worker_types).amount

        if combined_enemies.amount == 1 and worker_only:
            # Single scout worker
            u: Unit

            if self.ai.workers.filter(lambda u: u.shield_health_percentage < 0.75 and u.distance_to(self.ai.start_location) < 30).amount == 0:
                # Safe, let the scout do whatever it wants
                # TODO: Check expansion / building blocking
                self.free_others()
                return False  # Blocks normal zone defense, TODO: Remove this?

            self.attack_target(combined_enemies[0], 2, already_defending)
            self.free_others()
            return False  # Block other defense methods

        if worker_only:
            distance, closest_enemy = self.closest_distance_between_our_theirs(combined_enemies)
            if closest_enemy is None:
                closest_enemy = combined_enemies.closest_to(self.ai.start_location)

            buildings_needs_defending = self.ai.structures.filter(lambda u: self.building_needs_defending(u, 0.6))
            if (not buildings_needs_defending.exists
                    and (distance > 4
                    or (len(already_defending) < 5 and combined_enemies.closest_distance_to(self.ai.start_location) > 9))):
                self.free_others()
                return False  # no real danger, go back to mining

            require_workers = combined_enemies.amount + 2
            worker_count = self.ai.supply_workers

            if require_workers > 5 and worker_count > 5:
                require_workers = min(worker_count - 2, require_workers)

            army = self.get_army(closest_enemy, require_workers, already_defending)

            if not army:
                return False  # No army to fight with, waiting for one.

            self.knowledge.roles.set_tasks(UnitTask.Defending, army)
            #my_closest = army.closest_to(closest_enemy.position)
            # center = army.center

            buildings_needs_defending = self.ai.structures.filter(lambda u: self.building_needs_defending(u, 0.5))
            # own_closest = army.closest_to(closest_enemy)

            if (buildings_needs_defending.exists or distance < 3):
                for unit in army:
                    # if unit.type_id == UnitTypeId.PROBE and unit.shield <= 5:
                    #     await self.regroup_defend(actions, army, combined_enemies, unit)
                    # else:
                    self.knowledge.combat_manager.add_unit(unit)
            else:
                for unit in army:
                    await self.regroup_defend(army, combined_enemies, unit)

            self.knowledge.combat_manager.execute(closest_enemy.position, MoveType.Assault)
            self.free_others()
        else:
            return True  # Don't know how to defend against

        self.was_active = True
        return False  # In Combat

    async def regroup_defend(self, army, combined_enemies, unit):
        if unit.weapon_cooldown == 0:
            closest_to_this = combined_enemies.closest_to(unit)

            if closest_to_this.distance_to(unit) < self.unit_values.real_range(unit, closest_to_this):
                self.do(unit.attack(closest_to_this))
            else:
                await self.regroup(army, unit)
        else:
            await self.regroup(army, unit)

    async def regroup(self, army, unit):
        if self.unit_values.is_worker(unit):
            self.do(unit.gather(self.gather_mf))
        else:
            self.knowledge.combat_manager.add_unit(unit)

    def closest_distance_between_our_theirs(self, combined_enemies: Units) -> Tuple[float, Optional[Unit]]:
        own = self.ai.units.filter(lambda unit: not unit.is_structure and unit.type_id not in self.unit_values.combat_ignore)
        closest: Optional[Unit] = None
        d = 0
        for own_unit in own:  # type: Unit
            closest_temp = combined_enemies.closest_to(own_unit)
            temp_distance = closest_temp.distance_to(own_unit)
            if closest is None or temp_distance < d:
                d = temp_distance
                closest = closest_temp

        return (d, closest)

    def building_needs_defending(self, unit: Unit, percentage: float) -> bool:
        return unit.shield_health_percentage < percentage

    def get_army(self, target: Unit, defender_count: int, already_defending: Units):
        army: Units = Units([], self.ai)
        fighters: Units = Units([], self.ai)
        workers: Units = Units([], self.ai)
        count = 0

        for unit in self.ai.units: # type: Unit
            if unit.is_structure or unit.tag in self.defender_tags:
                continue
            if unit.type_id in self.unit_values.worker_types:
                workers.append(unit)
            elif self.knowledge.should_attack(unit):
                fighters.append(unit)

        if fighters:
            for fighter in fighters: # type: Unit
                army.append(fighter)
                self.defender_tags.append(fighter.tag)
                count += self.unit_values.power(fighter)

        if already_defending:
            for unit in already_defending: # type: Unit
                if self.ready_to_defend(unit):
                    count += 1
                    army.append(unit)
                    self.defender_tags.append(unit.tag)
                    if count >= defender_count:
                        return army


        for unit in workers.sorted_by_distance_to(target.position): # type: Unit
            if self.ready_to_defend(unit) and not unit.tag in self.defender_tags:
                count += 1
                army.append(unit)
                self.defender_tags.append(unit.tag)
                if count >= defender_count:
                    return army

        for unit in workers.sorted_by_distance_to(target.position): # type: Unit
            if not unit.tag in self.defender_tags:
                count += 1
                army.append(unit)
                self.defender_tags.append(unit.tag)
                if count >= defender_count:
                    return army
        return army

    def ready_to_defend(self, unit: Unit):
        return (unit.type_id == UnitTypeId.PROBE and unit.shield_percentage > 0) or unit.health > 5

    def attack_target(self, target: Unit, defender_count: int, already_defending: Units):
        fighters: Units = Units([], self.ai)
        workers: Units = Units([], self.ai)

        for unit in self.ai.units: # type: Unit
            if unit.is_structure or unit.tag in self.defender_tags:
                continue
            if unit.type_id in self.unit_values.worker_types:
                workers.append(unit)
            elif self.knowledge.should_attack(unit):
                fighters.append(unit)

        if fighters:
            for fighter in fighters: # type: Unit
                self.knowledge.roles.set_task(UnitTask.Defending, fighter)
                self.do(fighter.attack(target))
                self.defender_tags.append(fighter.tag)
                return

        count = 0
        if already_defending:
            for unit in already_defending: # type: Unit
                if self.ready_to_defend(unit):
                    count += 1
                    self.do(unit.attack(target))
                    self.defender_tags.append(unit.tag)
                    self.knowledge.roles.set_task(UnitTask.Defending, unit)
                    if count >= defender_count:
                        return


        for unit in workers.sorted_by_distance_to(target.position): # type: Unit
            if self.ready_to_defend(unit):
                count += 1
                self.do(unit.attack(target))
                self.defender_tags.append(unit.tag)
                self.knowledge.roles.set_task(UnitTask.Defending, unit)
                if count >= defender_count:
                    return

    def free_others(self):
        already_defending: Units = self.knowledge.roles.units(UnitTask.Defending)
        to_clear = already_defending.tags_not_in(self.defender_tags)
        self.knowledge.roles.clear_tasks(to_clear)

        for unit in to_clear:
            if unit.is_gathering or unit.is_attacking:
                self.do(unit.stop())

    async def debug_actions(self):
        if self.was_active:
            units: Units = self.knowledge.roles.units(UnitTask.Defending)
            for unit in units:
                text = f"Worker Defending"
                self._client.debug_text_world(text, unit.position3d)
