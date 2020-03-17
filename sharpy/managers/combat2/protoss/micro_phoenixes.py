from typing import Dict, Optional

from sharpy.managers.combat2 import MicroStep, Action, MoveType
from sc2 import UnitTypeId, AbilityId
from sc2.ids.buff_id import BuffId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

GRAVITON_BEAM_ENERGY = 50

class MicroPhoenixes(MicroStep):
    def __init__(self, knowledge):
        self.allow_lift = False
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
            UnitTypeId.WIDOWMINEBURROWED: 10,
            UnitTypeId.WIDOWMINE: 8,
            UnitTypeId.GHOST: 10,
            UnitTypeId.REAPER: 4,
            UnitTypeId.MARAUDER: 4,
            UnitTypeId.MARINE: 3,
            UnitTypeId.CYCLONE: 6,
            UnitTypeId.HELLION: 2,
            UnitTypeId.HELLIONTANK: 1,
            UnitTypeId.THOR: -1,

            # Zerg
            UnitTypeId.QUEEN: 3,
            UnitTypeId.DRONE: 4,
            UnitTypeId.HYDRALISK: 7,
            UnitTypeId.BANELING: 6,
            UnitTypeId.LURKERMP: 9,
            UnitTypeId.LURKERMPBURROWED: 9,
            UnitTypeId.INFESTOR: 10,
            UnitTypeId.INFESTEDTERRAN: 1,
            UnitTypeId.ROACH: 0,

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
        super().__init__(knowledge)

    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        beaming_phoenixes = units.filter(lambda p: p.orders and p.orders[0].ability.id == AbilityId.GRAVITONBEAM_GRAVITONBEAM)
        if beaming_phoenixes and len(beaming_phoenixes) > len(units) * 0.5:
            self.allow_lift = False
        else:
            self.allow_lift = True
        return current_command

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:

        if self.move_type == MoveType.DefensiveRetreat or self.move_type == MoveType.PanicRetreat:
            if self.ready_to_shoot(unit):
                closest = self.closest_units.get(unit.tag, None)
                if closest:
                    real_range = self.unit_values.real_range(unit, closest)
                    if 0 < real_range < unit.distance_to(closest):
                        return Action(closest.position, True)

            return current_command

        # Phoenixes are generally faster than the rest of the army

        # if self.engage_ratio < 0.25 and self.can_engage_ratio < 0.25:
        #     if self.group.ground_units:
        #         # Regroup with the ground army
        #         return Action(self.group.center, False)

        has_energy = unit.energy > GRAVITON_BEAM_ENERGY

        if has_energy and self.allow_lift:
            best_target: Optional[Unit] = None
            best_score: float = 0
            close_enemies = self.cache.enemy_in_range(unit.position, 14)

            for enemy in close_enemies:  # type: Unit
                if enemy.is_flying or enemy.is_structure or enemy.has_buff(BuffId.GRAVITONBEAM):
                    continue

                if self.move_type != MoveType.Harass and enemy.type_id in self.unit_values.worker_types:
                    # If we are not doing any harass, don't lift low priority workers up.
                    # We need to prioritize energy to actual combat units
                    continue

                pos: Point2 = enemy.position
                score = self.lift_priority.get(enemy.type_id, -1) + (1 - pos.distance_to(unit) / 10)
                if score > best_score:
                    best_target = enemy
                    best_score = score

            if best_target:
                if best_score > 5 or not close_enemies.flying.exists:
                    self.print(f"Phoenix at {unit.position} lifting {best_target.type_id} at {best_target.position}")

                    if unit.distance_to(best_target) > 8:
                        destination = self.knowledge.pathing_manager.find_influence_air_path(unit.position, best_target.position)
                        return Action(destination, False)
                    return Action(best_target, False, AbilityId.GRAVITONBEAM_GRAVITONBEAM)

        if self.engage_ratio < 0.25 and self.can_engage_ratio < 0.25:
            # Not in combat
            return current_command

        targets = self.enemies_near_by.flying

        if targets:
            closest = targets.closest_to(unit)
            # d = unit.distance_to(closest)
            real_range = self.unit_values.real_range(unit, closest) - 1
            best_position = self.pather.find_low_inside_air(unit.position, closest.position, real_range)

            return Action(best_position, False)

        return current_command


    def print(self, msg):
        self.knowledge.print(f"[MicroPhoenixes] {msg}")
