from math import floor
from typing import List, Set, Dict, Optional

from sharpy import sc2math
from sc2 import UnitTypeId, AbilityId
from sc2.ids.buff_id import BuffId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from sharpy.combat import CombatGoal, CombatAction, EnemyData
# from sharpy.general.combat.combat_manager import CombatManager
from sc2pathlibp import PathFinder
from .state_step import StateStep

GRAVITON_BEAM_ENERGY = 50


class StatePhoenix(StateStep):
    def __init__(self, knowledge, combat_manager: 'CombatManager'):
        super().__init__(knowledge)
        self.combat_manager = combat_manager
        self.path_finder_air: PathFinder = self.knowledge.pathing_manager.path_finder_air

        # These unit types should be targets for graviton beam
        self.lift_priority: Dict[UnitTypeId, int] = {
            # Threaholds: 10 instant priority pickup
            # 5 or above: Prefer lift to shooting actual enemies
            # 0 - 4: Lift only if nothing to shoot
            # negative number: Never try lifting

            # Terran
            UnitTypeId.SIEGETANK: 4,
            UnitTypeId.SIEGETANKSIEGED: 9,  # sieged tanks are much higher priority than unsieged
            UnitTypeId.MULE: 6,  # Would be nice to check it's remaining duration
            UnitTypeId.SCV: 4,
            UnitTypeId.GHOST: 10,
            UnitTypeId.REAPER: 4,
            UnitTypeId.MARAUDER: 4,
            UnitTypeId.MARINE: 3,
            UnitTypeId.CYCLONE: 5,
            UnitTypeId.HELLION: 2,
            UnitTypeId.HELLIONTANK: 1,
            UnitTypeId.THOR: -1,

            # Zerg
            UnitTypeId.QUEEN: 6,
            UnitTypeId.DRONE: 4,
            UnitTypeId.HYDRALISK: 7,
            UnitTypeId.BANELING: 6,
            UnitTypeId.LURKERMP: 9,
            UnitTypeId.LURKERMPBURROWED: 9,
            UnitTypeId.INFESTOR: 10,
            UnitTypeId.INFESTEDTERRAN: 1,

            UnitTypeId.LARVA: -1,
            UnitTypeId.EGG: -1,
            UnitTypeId.LOCUSTMP: -1,
            UnitTypeId.BROODLING: -1,
            UnitTypeId.ULTRALISK: -1,

            # Protoss
            UnitTypeId.SENTRY: 8,
            UnitTypeId.PROBE: 4,
            UnitTypeId.HIGHTEMPLAR: 10,
            UnitTypeId.DARKTEMPLAR: 9,
            UnitTypeId.ADEPT: 4,
            UnitTypeId.ZEALOT: 4,
            UnitTypeId.STALKER: 2,
            UnitTypeId.IMMORTAL: 3,
            UnitTypeId.ARCHON: -1,
            UnitTypeId.COLOSSUS: -1
        }

    def solve_combat(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> List[CombatAction]:
        actions: List[CombatAction] = []
        phoenix: Unit = goal.unit

        # def is_beam_target_type(unit: Unit) -> bool:
        #     if unit.type_id in self.always_ignore:
        #         return False
        #
        #     if phoenix.energy_percentage > 0.95:
        #         # Anything but ignored types are fine with full energy
        #         return True
        #
        #     return unit.type_id in self.lift_priority

        friends: Units = self.combat_manager.ai.units.closer_than(8, phoenix)
        half_not_beaming = friends.amount / 2 > len(self.combat_manager.beaming_phoenix_tags)

        has_energy = phoenix.energy > GRAVITON_BEAM_ENERGY
        best_target: Optional[Unit] = None
        best_score: float = 0

        for enemy in enemies.close_enemies:  # type: Unit
            if enemy.has_buff(BuffId.GRAVITONBEAM):
                continue

            pos: Point2 = enemy.position
            score = self.lift_priority.get(enemy.type_id, -1) + (1 - pos.distance_to(phoenix) / 10)
            if score > best_score:
                best_target = enemy
                best_score = score


        # Use Graviton Beam
        if has_energy and half_not_beaming and best_target:
            if best_score > 5 or not enemies.close_enemies.flying.exists:
                self.print(f"Phoenix at {phoenix.position} lifting {best_target.type_id} at {best_target.position}")

                if phoenix.distance_to(best_target) > 8:
                    destination = self.knowledge.pathing_manager.find_influence_air_path(phoenix.position, best_target.position)
                    return [CombatAction(phoenix, destination, False)]
                return [CombatAction(phoenix, best_target, False, ability=AbilityId.GRAVITONBEAM_GRAVITONBEAM)]

        if enemies.close_enemies.closer_than(11, phoenix.position).exists and not enemies.close_enemies.flying.exists:
            # There is an enemy close by, but it doesn't fly so let's run away !
            pathing_result = self.path_finder_air.lowest_influence_in_grid(enemies.our_median, 8)
            backstep = Point2(pathing_result[0])
            #backstep: Point2 = phoenix.position.towards(enemies.enemy_center, -3)
            return [CombatAction(phoenix, backstep, False)]

        # Do you normal stuff
        return actions

    def FinalSolve(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> CombatAction:
        phoenix: Unit = goal.unit

        if command.is_attack and isinstance(command.target, Unit):
            range = self.unit_values.real_range(phoenix, command.target)
            check_point = (phoenix.position + command.target.position) * 0.5
            pathing_result = self.knowledge.pathing_manager.find_weak_influence_air(check_point, 4)
            direction = sc2math.point_normalize(pathing_result - command.target.position)
            destination = command.target.position + direction * (range - 0.5)
            return CombatAction(phoenix, destination, False)

        return super().FinalSolve(goal, command, enemies)

    def print(self, msg):
        self.knowledge.print(f"[StatePhoenix] {msg}")
