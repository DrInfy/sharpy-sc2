from typing import List, Tuple

from sc2.position import Point2
from sharpy.managers import UnitValue
from sharpy.managers.build_detector import EnemyRushBuild
from sharpy.managers.combat2 import MoveType
from sharpy.plans.acts import ActBase
from sharpy.managers.roles import UnitTask
from sharpy.general.zone import Zone

from sc2 import UnitTypeId
from sc2.unit import Unit
from sc2.units import Units


class WorkerCounterAttack(ActBase):
    def __init__(self):
        self.has_failed = False
        self.was_active = False
        self.tags: List[int] = []
        super().__init__()

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.gather_mf = self.solve_optimal_mineral_field()

    def solve_optimal_mineral_field(self) -> Unit:
        main: Zone = self.knowledge.own_main_zone
        for mf in main.mineral_fields:  # type: Unit
            if len(main.mineral_fields.closer_than(2, mf.position)) > 2:
                return mf
        return main.mineral_fields.first

    async def execute(self) -> bool:
        if self.has_failed:
            return True  # only do counter attack once
        if self.was_active:
            return self.handle_counter()
        if self.knowledge.build_detector.rush_build == EnemyRushBuild.WorkerRush:
            self.was_active = True
            return self.start_counter()
        return True

    def start_counter(self) -> bool:
        worker_count = self.ai.supply_workers - 2
        target = self.knowledge.enemy_main_zone.center_location
        army = self.get_army(target, worker_count)
        self.combat.add_units(army)
        self.combat.execute(self.knowledge.enemy_main_zone.center_location)
        self.roles.set_tasks(UnitTask.Attacking, army)
        return False

    def get_army(self, target: Point2, attacker_count: int) -> Units:
        # Clear defenders
        defenders = self.roles.all_from_task(UnitTask.Defending)
        self.roles.clear_tasks(defenders.tags)

        count = 0
        army = Units([], self.ai)
        for unit in self.roles.free_workers.sorted_by_distance_to(target):  # type: Unit

            count += 1
            army.append(unit)
            self.tags.append(unit.tag)
            if count >= attacker_count:
                break

        old_defenders = defenders.tags_not_in(self.tags)
        for unit in old_defenders:
            self.do(unit.stop())
        return army

    def handle_counter(self) -> bool:
        attackers = Units([], self.ai)
        for tag in self.tags:
            unit = self.cache.by_tag(tag)
            if unit:
                attackers.append(unit)

        if not attackers.exists:
            self.has_failed = True
            return True

        self.roles.set_tasks(UnitTask.Attacking, attackers)
        attackers_left = attackers.amount

        for attacker in attackers:  # type: Unit
            if attacker.weapon_cooldown > 10 and attacker.shield_health_percentage < 0.5:
                self.do(attacker.gather(self.gather_mf))
            else:
                own = self.cache.own_in_range(attacker.position, 3).amount
                enemies = self.cache.enemy_in_range(attacker.position, 3)
                enemy_count = enemies.amount

                if own >= attackers_left or enemy_count <= own:
                    self.combat.add_unit(attacker)
                else:
                    # Regroup
                    if attacker.distance_to(self.gather_mf) < 5:
                        # On other option but to fight
                        self.combat.add_units(attackers)
                    else:
                        self.do(attacker.gather(self.gather_mf))

        self.combat.execute(self.knowledge.enemy_main_zone.center_location)
        return False
