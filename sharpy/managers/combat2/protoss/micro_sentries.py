from typing import List, Optional, TYPE_CHECKING

from sharpy.general.zone import Zone
from sharpy.managers.combat2 import MoveType, Action, NoAction, GenericMicro, CombatModel
from sc2.position import Point2
if TYPE_CHECKING:
    from sharpy.managers import *

from sc2 import AbilityId, Race
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit, UnitOrder
from sc2.units import Units


GUARDIAN_SHIELD_RANGE = 4.5
GUARDIAN_SHIELD_TRIGGER_RANGE = 8

FORCE_FIELD_ENERGY_COST = 50
SHIELD_ENERGY_COST = 75
HALLUCINATION_ENERGY_COST = 75

class MicroSentries(GenericMicro):
    def __init__(self, knowledge):
        super().__init__(knowledge)
        self.shield_up = False
        self.last_shield_up = 0  # Allows delay until another shield is used
        self.should_shield_up = False
        self.range_power = 0
        self.melee_power = 0
        self.upcoming_fields: List[Point2] = []

        ramp_ff_movement = 2

        self.main_ramp_position: Point2 = self.knowledge.base_ramp.bottom_center.towards(
            self.knowledge.base_ramp.top_center, ramp_ff_movement)
        # self.main_ramp_position = self.main_ramp_position.offset((0.5, -0.5))


    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        self.upcoming_fields.clear()

        self.shield_up = False
        for unit in units:
            if unit.has_buff(BuffId.GUARDIANSHIELD):
                self.shield_up = True
            elif unit.orders and unit.orders[0].ability.id == AbilityId.FORCEFIELD_FORCEFIELD:
                self.shield_up = True

        self.range_power = 0
        self.melee_power = 0

        for group in self.enemy_groups:
            if group.center.distance_to(self.center) < 10:
                self.range_power += group.power.ground_power - group.power.melee_power
                self.melee_power += group.power.melee_power

        self.should_shield_up = self.range_power > 10
        return super().group_solve_combat(units, current_command)

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        if self.force_fielding(unit):
            # Don't do anything if force field is ordered
            return NoAction()

        if not self.shield_up and self.should_shield_up and unit.energy >= SHIELD_ENERGY_COST \
                and self.last_shield_up + 0.5 < self.ai.time:
            self.shield_up = True
            self.last_shield_up = self.ai.time
            return Action(None, False, AbilityId.GUARDIANSHIELD_GUARDIANSHIELD)

        if unit.shield_percentage < 0.1:
            if self.range_power > 5 and unit.energy >= HALLUCINATION_ENERGY_COST:
                return Action(None, False, AbilityId.HALLUCINATION_ARCHON)
            if self.melee_power > 5 and unit.energy >= FORCE_FIELD_ENERGY_COST:
                melee = self.knowledge.unit_cache.enemy(self.unit_values.melee)
                if melee:
                    closest = melee.closest_to(unit)
                    pos = unit.position.towards(closest, 0.6)
                    return Action(pos, False, AbilityId.FORCEFIELD_FORCEFIELD)

        if self.move_type == MoveType.SearchAndDestroy and unit.energy >= FORCE_FIELD_ENERGY_COST:
            # Look for defensive force field on ramp or other choke
            natural: Zone = self.knowledge.expansion_zones[1]
            main: Zone = self.knowledge.expansion_zones[0]
            d_natural = unit.distance_to(natural.center_location)
            d_main = unit.distance_to(main.center_location)

            if d_natural < 15 and d_natural < d_main and self.closest_group_distance < 10:
                # Sentry is at the natural
                zealot_pos: Point2 = self.knowledge.building_solver.zealot_position
                if self.knowledge.enemy_race == Race.Zerg and natural.our_wall() and zealot_pos:
                    # Protect gate keeper
                    our_keepers = self.cache.own_in_range(zealot_pos, 2).not_structure
                    combined_health = 0
                    for keeper in our_keepers:  # type: Unit
                        combined_health += keeper.health + keeper.shield

                    if combined_health < 70:
                        action = self.should_force_field(zealot_pos.towards(self.closest_group.center, 0.6))
                        if action:
                            return action

                if self.model == CombatModel.StalkerToSpeedlings:
                    # Protect buildings
                    buildings = self.cache.own_in_range(unit.position, 8).structure
                    for building in buildings:   # type: Unit
                        if building.health + building.shield < 300:
                            action = self.should_force_field(building.position.towards(self.closest_group.center, 1.2))
                            if action:
                                return action

            elif not natural.is_ours or natural.power_balance < 0 and d_main < main.radius:
                # Protect main base ramp
                not_flying = self.cache.enemy_in_range(self.main_ramp_position, 3).filter(lambda u: not u.is_flying and not u.is_structure)
                if not_flying:
                    action = self.should_force_field(self.main_ramp_position)
                    if action:
                        return action

            #  and self.model == CombatModel.StalkerToSpeedlings
        return super().unit_solve_combat(unit, current_command)

    def should_force_field(self, position: Point2) -> Optional[Action]:
        for ff in self.cache.force_fields:  # type: EffectData
            for position in ff.positions:
                if position.distance_to(position) < 1.5:
                    return None

        for ff_pos in self.upcoming_fields:   # type: Point2
            if ff_pos.distance_to_point2(position) < 1.5:
                return None

        self.upcoming_fields.append(position)
        return Action(position, False, AbilityId.FORCEFIELD_FORCEFIELD)

    def force_fielding(self, unit) -> Optional[Point2]:
        if unit.orders:
            # action: UnitCommand
            # current_action: UnitOrder
            current_action: UnitOrder = unit.orders[0]
            if current_action.ability.id == AbilityId.FORCEFIELD_FORCEFIELD:
                return current_action.target
        return None
