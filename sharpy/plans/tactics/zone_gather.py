from typing import Optional, List

from sc2.bot_ai import BotAI
from sc2.data import Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId

from sharpy.combat import MoveType
from sharpy.interfaces import IGatherPointSolver, IBuildingSolver, IEnemyUnitsManager
from sharpy.plans.acts import ActBase
from sc2.position import Point2
from sc2.unit import Unit

from sharpy.managers.core.roles import UnitTask
from sharpy.knowledges import Knowledge
from sharpy.managers.core import UnitValue


class PlanZoneGather(ActBase):
    gather_point_solver: IGatherPointSolver
    building_solver: IBuildingSolver
    enemy_units_manager: IEnemyUnitsManager

    def __init__(self, set_gather_points: bool = True):
        super().__init__()
        self.gather_move_type = MoveType.Assault
        self.gather_set: List[int] = []
        self.blocker_tag: Optional[int] = None
        self.current_gather_point = Point2((0, 0))
        self.close_gates = True
        self.set_gather_points = set_gather_points

    @property
    def gather_point(self) -> Point2:
        return self.current_gather_point_solver.gather_point

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)
        self.building_solver = knowledge.get_required_manager(IBuildingSolver)
        self.enemy_units_manager = knowledge.get_required_manager(IEnemyUnitsManager)
        self.current_gather_point_solver = self.knowledge.get_manager(IGatherPointSolver)

        self.my_race = self.ai.race
        self.defender_types: list
        self.knowledge = knowledge
        self.unit_values: UnitValue = knowledge.unit_values
        self.base_ramp = self.zone_manager.expansion_zones[0].ramp
        self.close_gates = self.ai.enemy_race == Race.Zerg and self.ai.race != Race.Zerg

    def should_hold_position(self, target_position: Point2) -> bool:
        close_enemies = self.ai.all_enemy_units.filter(lambda u: not u.is_flying and not u.is_structure)
        if close_enemies.exists:
            enemy_near = close_enemies.closest_distance_to(target_position) < 7
            if not enemy_near:
                return False

            attackers = self.roles.attacking_units
            if attackers:
                attacker_near = attackers.closest_distance_to(target_position) < 5
                return not attacker_near

            return True

        # No non-flying enemies around
        return False

    async def execute(self) -> bool:
        unit: Unit
        if self.current_gather_point != self.gather_point:
            self.gather_set.clear()
            self.current_gather_point = self.gather_point

        unit: Unit
        if self.set_gather_points:
            for unit in self.cache.own([UnitTypeId.GATEWAY, UnitTypeId.ROBOTICSFACILITY]).tags_not_in(self.gather_set):
                # Rally point is set to prevent units from spawning on the wrong side of wall in
                pos: Point2 = unit.position
                pos = pos.towards(self.current_gather_point, 3)
                unit(AbilityId.RALLY_BUILDING, pos)
                self.gather_set.append(unit.tag)

        await self.manage_blocker()

        units = []
        units.extend(self.roles.idle)

        for unit in units:
            if self.unit_values.should_attack(unit):
                d2 = unit.position.distance_to(self.current_gather_point)
                if d2 > 6.5:
                    self.combat.add_unit(unit)

        self.combat.execute(self.current_gather_point, self.gather_move_type)
        return True  # Always non blocking

    def update_gates(self):
        if self.close_gates:
            lings = self.enemy_units_manager.unit_count(UnitTypeId.ZERGLING)
            if (
                self.enemy_units_manager.unit_count(UnitTypeId.ROACH) > lings
                or self.enemy_units_manager.unit_count(UnitTypeId.HYDRALISK) > lings
            ):
                self.close_gates = False

    async def manage_blocker(self):
        target_position = self.building_solver.zealot
        if target_position is not None:
            if self.blocker_tag is not None:
                unit = self.cache.by_tag(self.blocker_tag)
                if unit is not None and self.close_gates:
                    self.roles.set_task(UnitTask.Reserved, unit)

                    if unit.type_id in {UnitTypeId.STALKER, UnitTypeId.IMMORTAL} and self.cache.own(UnitTypeId.ZEALOT):
                        # Swap expensive blocker to a zaalot
                        new_blocker = self.get_blocker(self.ai, target_position)
                        if new_blocker is not None:
                            self.roles.clear_task(unit)
                            # Register tag
                            unit = new_blocker
                            self.blocker_tag = unit.tag
                            self.roles.set_task(UnitTask.Reserved, unit)

                    if self.should_hold_position(target_position):
                        if unit.distance_to(target_position) < 0.2:
                            unit.hold_position()
                        elif self.ai.enemy_units.exists and self.ai.enemy_units.closest_distance_to(unit) < 2:
                            unit.attack(target_position)
                        else:
                            unit.move(target_position)
                    else:
                        if self.natural_wall:
                            chill_position = target_position
                        else:
                            top_center = self.base_ramp.top_center
                            chill_position = target_position.towards(top_center, -1)

                        if unit.distance_to(chill_position) > 4:
                            unit.move(chill_position)
                        elif unit.orders and unit.orders[0].ability.id == AbilityId.HOLDPOSITION:
                            unit.stop()
                else:
                    await self.remove_gate_keeper()

            elif self.close_gates:
                # We need someone to block our wall.
                unit = self.get_blocker(self.ai, target_position)
                if unit is not None:
                    # Register tag
                    self.blocker_tag = unit.tag
                    self.roles.set_task(UnitTask.Reserved, unit)
                    unit.attack(target_position)

    @property
    def natural_wall(self) -> bool:
        natural = self.zone_manager.expansion_zones[1]
        return natural.is_ours and natural.our_wall()

    async def remove_gate_keeper(self):
        if self.blocker_tag is not None:
            unit = self.cache.by_tag(self.blocker_tag)
            if unit is not None:
                unit.attack(self.current_gather_point)
            self.roles.clear_task(self.blocker_tag)
            self.blocker_tag = None

        main_zone = self.zone_manager.expansion_zones[0]

        for unit in main_zone.known_enemy_units:  # type: Unit
            if unit.is_flying or self.unit_values.defense_value(unit.type_id) == 0 or self.unit_values.is_worker(unit):
                # Unit doesn't require removing gate keeper
                continue

            # Dangerous enemy near our base!
            if self.knowledge.ai.get_terrain_height(unit) < main_zone.height:
                # It hasn't gone up the ramp yet.
                continue

            if self.base_ramp.top_center.distance_to(unit.position) < 3.16:
                # Enemy is probaly stuck in the ramp entrance
                continue
            # Enemy is inside our base, remove gate keeper!
            return False

        return True

    def get_blocker(self, ai, position: Point2) -> Optional[Unit]:
        unit = self.get_blocker_type(UnitTypeId.ZEALOT, ai, position)
        if unit is None:
            unit = self.get_blocker_type(UnitTypeId.ADEPT, ai, position)
        # if unit is None:
        #     unit = self.get_blocker_type(sc2.UnitTypeId.STALKER, ai, position)
        if unit is None:
            unit = self.get_blocker_type(UnitTypeId.DARKTEMPLAR, ai, position)
        # if unit is None:
        #     unit = self.get_blocker_type(sc2.UnitTypeId.IMMORTAL, ai, position)
        return unit

    def get_blocker_type(self, unit_type: UnitTypeId, ai: BotAI, position: Point2) -> Optional[Unit]:
        units = self.roles.free_units(unit_type).closer_than(15, position)
        if units.exists:
            return units.closest_to(position)
        return None
