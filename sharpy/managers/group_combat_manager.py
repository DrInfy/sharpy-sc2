from typing import List, Dict, Optional, Union

from sharpy.managers.combat2 import *
from sharpy.general.extended_power import ExtendedPower
from sharpy.managers import UnitCacheManager, PathingManager, ManagerBase
from sharpy.managers.combat2 import Action
from sharpy.managers.combat2.protoss import *
from sharpy.managers.combat2.terran import *
from sharpy.managers.combat2.zerg import *
from sc2.units import Units

from sc2 import UnitTypeId
from sc2.position import Point2, Point3
from sc2.unit import Unit

ignored = {UnitTypeId.MULE, UnitTypeId.LARVA, UnitTypeId.EGG}


class GroupCombatManager(ManagerBase):
    def __init__(self):
        # How much distance must be between units to consider them to be in different groups
        self.own_group_threshold = 7
        super().__init__()

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        self.cache: UnitCacheManager = self.knowledge.unit_cache
        self.pather: PathingManager = self.knowledge.pathing_manager
        self.tags: List[int] = []

        self.unit_micros: Dict[UnitTypeId, MicroStep] = dict()
        self.all_enemy_power = ExtendedPower(self.unit_values)

        # Micro controllers / handlers
        self.unit_micros[UnitTypeId.DRONE] = MicroWorkers(knowledge)
        self.unit_micros[UnitTypeId.PROBE] = MicroWorkers(knowledge)
        self.unit_micros[UnitTypeId.SCV] = MicroWorkers(knowledge)

        # Protoss
        self.unit_micros[UnitTypeId.ARCHON] = NoMicro(knowledge)
        self.unit_micros[UnitTypeId.ADEPT] = MicroAdepts(knowledge)
        self.unit_micros[UnitTypeId.CARRIER] = MicroCarriers(knowledge)
        self.unit_micros[UnitTypeId.COLOSSUS] = MicroColossi(knowledge)
        self.unit_micros[UnitTypeId.DARKTEMPLAR] = MicroZerglings(knowledge)
        self.unit_micros[UnitTypeId.DISRUPTOR] = MicroDisruptor(knowledge)
        self.unit_micros[UnitTypeId.DISRUPTORPHASED] = MicroPurificationNova(knowledge)
        self.unit_micros[UnitTypeId.HIGHTEMPLAR] = MicroHighTemplars(knowledge)
        self.unit_micros[UnitTypeId.OBSERVER] = MicroObservers(knowledge)
        self.unit_micros[UnitTypeId.ORACLE] = MicroOracles(knowledge)
        self.unit_micros[UnitTypeId.PHOENIX] = MicroPhoenixes(knowledge)
        self.unit_micros[UnitTypeId.SENTRY] = MicroSentries(knowledge)
        self.unit_micros[UnitTypeId.STALKER] = MicroStalkers(knowledge)
        self.unit_micros[UnitTypeId.WARPPRISM] = MicroWarpPrism(knowledge)
        self.unit_micros[UnitTypeId.VOIDRAY] = MicroVoidrays(knowledge)
        self.unit_micros[UnitTypeId.ZEALOT] = MicroZealots(knowledge)

        # Zerg
        self.unit_micros[UnitTypeId.ZERGLING] = MicroZerglings(knowledge)
        self.unit_micros[UnitTypeId.ULTRALISK] = NoMicro(knowledge)
        self.unit_micros[UnitTypeId.OVERSEER] = MicroOverseers(knowledge)
        self.unit_micros[UnitTypeId.QUEEN] = MicroQueens(knowledge)
        self.unit_micros[UnitTypeId.RAVAGER] = MicroRavagers(knowledge)

        self.unit_micros[UnitTypeId.LURKERMP] = MicroLurkers(knowledge)
        self.unit_micros[UnitTypeId.INFESTOR] = MicroInfestors(knowledge)
        self.unit_micros[UnitTypeId.SWARMHOSTMP] = MicroSwarmHosts(knowledge)
        self.unit_micros[UnitTypeId.LOCUSTMP] = NoMicro(knowledge)
        self.unit_micros[UnitTypeId.LOCUSTMPFLYING] = NoMicro(knowledge)
        self.unit_micros[UnitTypeId.VIPER] = MicroVipers(knowledge)

        # Terran
        self.unit_micros[UnitTypeId.HELLIONTANK] = NoMicro(knowledge)
        self.unit_micros[UnitTypeId.SIEGETANK] = MicroTanks(knowledge)
        self.unit_micros[UnitTypeId.VIKINGFIGHTER] = MicroVikings(knowledge)
        self.unit_micros[UnitTypeId.MARINE] = MicroBio(knowledge)
        self.unit_micros[UnitTypeId.MARAUDER] = MicroBio(knowledge)
        self.unit_micros[UnitTypeId.BATTLECRUISER] = MicroBattleCruisers(knowledge)
        self.unit_micros[UnitTypeId.RAVEN] = MicroRavens(knowledge)
        self.unit_micros[UnitTypeId.MEDIVAC] = MicroMedivacs(knowledge)

        self.generic_micro = GenericMicro(knowledge)
        self.regroup_threshold = 0.75

    async def update(self):
        self.enemy_groups: List[CombatUnits] = self.group_enemy_units()
        self.all_enemy_power.clear()

        for group in self.enemy_groups: # type: CombatUnits
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

    def execute(self, target: Point2, move_type=MoveType.Assault):
        our_units = self.get_all_units()
        if len(our_units) < 1:
            return

        self.own_groups: List[CombatUnits] = self.group_own_units(our_units)

        total_power = ExtendedPower(self.unit_values)

        for group in self.own_groups:
            total_power.add_power(group.power)

        if self.debug:
            fn = lambda group: group.center.distance_to(self.ai.start_location)
            sorted_list = sorted(self.own_groups, key=fn)
            for i in range(0, len(sorted_list)):
                sorted_list[i].debug_index = i

        for group in self.own_groups:
            center = group.center
            closest_enemies = group.closest_target_group(self.enemy_groups)
            own_closest_group = self.closest_group(center, self.own_groups)

            if closest_enemies is None:
                if move_type == MoveType.PanicRetreat:
                    self.move_to(group, target, move_type)
                else:
                    self.attack_to(group, target, move_type)
            else:
                power = group.power
                enemy_power = ExtendedPower(closest_enemies)
                enemy_center = closest_enemies.center

                is_in_combat = group.is_in_combat(closest_enemies)
                # pseudocode for attack

                if move_type == MoveType.DefensiveRetreat or move_type == MoveType.PanicRetreat:
                    self.move_to(group, target, move_type)
                    break

                if power.power > self.regroup_threshold * total_power.power:
                    # Most of the army is here
                    if (
                            group.is_too_spread_out()
                            and not is_in_combat
                    ):
                        self.regroup(group, group.center)
                    else:
                        self.attack_to(group, target, move_type)

                elif is_in_combat:
                    if not power.is_enough_for(enemy_power, 0.75):
                        # Regroup if possible

                        if own_closest_group:
                            self.move_to(group, own_closest_group.center, MoveType.ReGroup)
                        else:
                            # fight to bitter end
                            self.attack_to(group, closest_enemies.center, move_type)
                    else:
                        self.attack_to(group, closest_enemies.center, move_type)
                else:
                    # if self.faster_group_should_regroup(group, own_closest_group):
                    #     self.move_to(group, own_closest_group.center, MoveType.ReGroup)

                    if group.power.is_enough_for(self.all_enemy_power, 0.85):
                        # We have enough units here to crush everything the enemy has
                        self.attack_to(group, closest_enemies.center, move_type)
                    else:
                        # Regroup if possible
                        if move_type == MoveType.Assault:
                            # Group towards attack target
                            own_closest_group = self.closest_group(target, self.own_groups)
                        else:
                            # Group up with closest group
                            own_closest_group = self.closest_group(center, self.own_groups)

                        if own_closest_group:
                            self.move_to(group, own_closest_group.center, MoveType.ReGroup)
                        else:
                            # fight to bitter end
                            self.attack_to(group, closest_enemies.center, move_type)

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
            if move_type in { MoveType.DefensiveRetreat, MoveType.PanicRetreat}:
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
            micro.init_group(group, type_units, self.enemy_groups, move_type)
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

    def group_own_units(self, our_units: Units) -> List[CombatUnits]:
        lookup_distance = self.own_group_threshold
        groups: List[Units] = []
        assigned: Dict[int, int] = dict()

        for unit in our_units:
            if unit.tag in assigned:
                continue

            units = Units([unit], self.ai)
            index = len(groups)

            assigned[unit.tag] = index

            groups.append(units)
            self.include_own_units(unit, units, lookup_distance, index, assigned)

        return [CombatUnits(u, self.knowledge) for u in groups]

    def include_own_units(self, unit: Unit, units: Units, lookup_distance: float, index: int, assigned: Dict[int, int]):
        units_close_by = self.cache.own_in_range(unit.position, lookup_distance)

        for unit_close in units_close_by:
            if unit_close.tag in assigned or unit_close.tag not in self.tags:
                continue

            assigned[unit_close.tag] = index
            units.append(unit_close)
            self.include_own_units(unit_close, units, lookup_distance, index, assigned)

    def group_enemy_units(self) -> List[CombatUnits]:
        groups: List[Units] = []
        assigned: Dict[int, int] = dict()
        lookup_distance = 7

        for unit in self.knowledge.known_enemy_units_mobile:
            if unit.tag in assigned or unit.type_id in self.unit_values.combat_ignore or not unit.can_be_attacked:
                continue

            units = Units([unit], self.ai)
            index = len(groups)

            assigned[unit.tag] = index

            groups.append(units)
            self.include_enemy_units(unit, units, lookup_distance, index, assigned)

        return [CombatUnits(u, self.knowledge) for u in groups]

    def include_enemy_units(self, unit: Unit, units: Units, lookup_distance: float, index: int, assigned: Dict[int, int]):
        units_close_by = self.cache.enemy_in_range(unit.position, lookup_distance)

        for unit_close in units_close_by:
            if unit_close.tag in assigned or unit_close.tag not in self.tags or not unit.can_be_attacked:
                continue

            assigned[unit_close.tag] = index
            units.append(unit_close)
            self.include_enemy_units(unit_close, units, lookup_distance, index, assigned)
