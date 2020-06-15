from typing import List, Dict, Optional, Union

from sharpy.managers.combat2 import *
from sharpy.general.extended_power import ExtendedPower
from sharpy.managers import UnitCacheManager, PathingManager, ManagerBase
from sharpy.managers.combat2 import Action
from sc2.units import Units

from sc2 import UnitTypeId
from sc2.position import Point2, Point3
from sc2.unit import Unit
import numpy as np
from sklearn.cluster import DBSCAN

# IMPORTANT, do NOT remove these. Used for pyinstaller to include all files.
import sklearn.utils._cython_blas
import sklearn.neighbors.typedefs
import sklearn.neighbors.quad_tree
import sklearn.tree
import sklearn.tree._utils

ignored = {UnitTypeId.MULE, UnitTypeId.LARVA, UnitTypeId.EGG}


class GroupCombatManager(ManagerBase):
    rules: MicroRules

    def __init__(self):
        super().__init__()
        self.default_rules = MicroRules()
        self.default_rules.load_default_methods()
        self.default_rules.load_default_micro()
        self.enemy_group_distance = 7

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.cache: UnitCacheManager = self.knowledge.unit_cache
        self.pather: PathingManager = self.knowledge.pathing_manager
        self.tags: List[int] = []
        self.all_enemy_power = ExtendedPower(self.unit_values)

        await self.default_rules.start(knowledge)

    @property
    def regroup_threshold(self) -> float:
        """ Percentage 0 - 1 on how many of the attacking units should actually be together when attacking"""
        return self.rules.regroup_percentage

    @property
    def own_group_threshold(self) -> float:
        """
        How much distance must be between units to consider them to be in different groups
        """
        return self.rules.own_group_distance

    @property
    def unit_micros(self) -> Dict[UnitTypeId, MicroStep]:
        return self.rules.unit_micros

    @property
    def generic_micro(self) -> MicroStep:
        return self.rules.generic_micro

    async def update(self):
        self.enemy_groups: List[CombatUnits] = self.group_enemy_units()
        self.all_enemy_power.clear()

        for group in self.enemy_groups:  # type: CombatUnits
            self.all_enemy_power.add_units(group.units)

    async def post_update(self):
        pass

    @property
    def debug(self):
        return self._debug and self.knowledge.debug

    def add_unit(self, unit: Unit):
        if unit.type_id in ignored:  # Just no
            return

        self.tags.append(unit.tag)

    def add_units(self, units: Units):
        for unit in units:
            self.add_unit(unit)

    def get_all_units(self) -> Units:
        units = Units([], self.ai)
        for tag in self.tags:
            unit = self.cache.by_tag(tag)
            if unit:
                units.append(unit)
        return units

    def execute(self, target: Point2, move_type=MoveType.Assault, rules: Optional[MicroRules] = None):
        our_units = self.get_all_units()
        if len(our_units) < 1:
            return

        self.rules = rules if rules else self.default_rules

        self.own_groups: List[CombatUnits] = self.group_own_units(our_units)

        if self.debug:
            fn = lambda group: group.center.distance_to(self.ai.start_location)
            sorted_list = sorted(self.own_groups, key=fn)
            for i in range(0, len(sorted_list)):
                sorted_list[i].debug_index = i

        self.rules.handle_groups_func(self, target, move_type)

        self.tags.clear()

    def faster_group_should_regroup(self, group1: CombatUnits, group2: Optional[CombatUnits]) -> bool:
        if not group2:
            return False
        if group1.average_speed < group2.average_speed + 0.1:
            return False
        # Our group is faster, it's a good idea to regroup
        return True

    def regroup(self, group: CombatUnits, target: Union[Unit, Point2]):
        if isinstance(target, Unit):
            target = self.pather.find_path(group.center, target.position, 1)
        else:
            target = self.pather.find_path(group.center, target, 3)
        self.move_to(group, target, MoveType.Push)

    def move_to(self, group: CombatUnits, target, move_type: MoveType):
        self.action_to(group, target, move_type, False)

    def attack_to(self, group: CombatUnits, target, move_type: MoveType):
        self.action_to(group, target, move_type, True)

    def action_to(self, group: CombatUnits, target, move_type: MoveType, is_attack: bool):
        if isinstance(target, Point2) and group.ground_units:
            if move_type in {MoveType.DefensiveRetreat, MoveType.PanicRetreat}:
                target = self.pather.find_influence_ground_path(group.center, target, 14)
            else:
                target = self.pather.find_path(group.center, target, 14)

        own_unit_cache: Dict[UnitTypeId, Units] = {}

        for unit in group.units:
            real_type = self.unit_values.real_type(unit.type_id)
            units = own_unit_cache.get(real_type, Units([], self.ai))
            if units.amount == 0:
                own_unit_cache[real_type] = units

            units.append(unit)

        for type_id, type_units in own_unit_cache.items():
            micro: MicroStep = self.unit_micros.get(type_id, self.generic_micro)
            micro.init_group(self.rules, group, type_units, self.enemy_groups, move_type)
            group_action = micro.group_solve_combat(type_units, Action(target, is_attack))

            for unit in type_units:
                final_action = micro.unit_solve_combat(unit, group_action)
                order = final_action.to_commmand(unit)
                if order:
                    self.ai.do(order)

                if self.debug:
                    if final_action.debug_comment:
                        status = final_action.debug_comment
                    elif final_action.ability:
                        status = final_action.ability.name
                    elif final_action.is_attack:
                        status = "Attack"
                    else:
                        status = "Move"
                    if final_action.target is not None:
                        if isinstance(final_action.target, Unit):
                            status += f": {final_action.target.type_id.name}"
                        else:
                            status += f": {final_action.target}"

                    status += f" G: {group.debug_index}"
                    status += f"\n{move_type.name}"

                    pos3d: Point3 = unit.position3d
                    pos3d = Point3((pos3d.x, pos3d.y, pos3d.z + 2))
                    self.ai._client.debug_text_world(status, pos3d, size=10)

    def closest_group(self, start: Point2, combat_groups: List[CombatUnits]) -> Optional[CombatUnits]:
        group = None
        best_distance = 50  # doesn't find enemy groups closer than this

        for combat_group in combat_groups:
            center = combat_group.center

            if center == start:
                continue  # it's the same group!

            distance = start.distance_to(center)
            if distance < best_distance:
                best_distance = distance
                group = combat_group

        return group

    def group_own_units(self, units: Units) -> List[CombatUnits]:
        groups: List[Units] = []

        # import time
        # ns_pf = time.perf_counter_ns()

        numpy_vectors: List[np.ndarray] = []
        for unit in units:
            numpy_vectors.append(np.array([unit.position.x, unit.position.y]))

        if numpy_vectors:
            clustering = DBSCAN(eps=self.enemy_group_distance, min_samples=1).fit(numpy_vectors)
            # print(clustering.labels_)

            for index in range(0, len(clustering.labels_)):
                unit = units[index]
                if unit.type_id in self.unit_values.combat_ignore:
                    continue

                label = clustering.labels_[index]

                if label >= len(groups):
                    groups.append(Units([unit], self.ai))
                else:
                    groups[label].append(unit)
            # for label in clustering.labels_:

        # ns_pf = time.perf_counter_ns() - ns_pf
        # print(f"Own unit grouping (v2) took {ns_pf / 1000 / 1000} ms. groups: {len(groups)} units: {len(units)}")

        return [CombatUnits(u, self.knowledge) for u in groups]

    def group_enemy_units(self) -> List[CombatUnits]:
        groups: List[Units] = []

        import time

        ns_pf = time.perf_counter_ns()

        if self.cache.enemy_numpy_vectors:
            clustering = DBSCAN(eps=self.enemy_group_distance, min_samples=1).fit(self.cache.enemy_numpy_vectors)
            # print(clustering.labels_)
            units = self.knowledge.known_enemy_units
            for index in range(0, len(clustering.labels_)):
                unit = units[index]
                if unit.type_id in self.unit_values.combat_ignore or not unit.can_be_attacked:
                    continue

                label = clustering.labels_[index]

                if label >= len(groups):
                    groups.append(Units([unit], self.ai))
                else:
                    groups[label].append(unit)
            # for label in clustering.labels_:
        ns_pf = time.perf_counter_ns() - ns_pf
        # print(f"Enemy unit grouping (v2) took {ns_pf / 1000 / 1000} ms. groups: {len(groups)}")
        return [CombatUnits(u, self.knowledge) for u in groups]
