from typing import List, Dict

from frozen.combat.state_warpprism import StateWarpPrism
from frozen.sc2math import unit_geometric_median
from frozen.general.unit_value import UnitValue

from .state_step import StateStep
from sc2 import UnitTypeId, AbilityId, common_pb, BotAI
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from .combat_action import CombatAction
from .combat_goal import CombatGoal
from .defensive_kite import DefensiveKite
from .enemy_data import EnemyData
from .enemy_targeting import EnemyTargeting
from .formation import Formation
from .move_type import MoveType
from .offensive_push import OffensivePush
from .state_voidray import StateVoidray
from .state_stalker import StateStalker

from .state_medivac import StateMedivac
from .state_observer import StateObserver
from .state_ravager import StateRavager
from .state_raven import StateRaven
from .state_siegetank import StateSiegetank
from .state_viking import StateViking

from .state_adept import StateAdept
from .state_disruptor import StateDisruptor
from .state_disruptor import StatePurificationNova
from .state_oracle import StateOracle
from .state_phoenix import StatePhoenix
from .state_battle_cruiser import StateBattleCruiser
from .ball_formation import BallFormation
from .state_sentry import StateSentry


class CombatManager:
    focus_fire: bool
    defensive_stutter_step: bool
    offensive_stutter_step: bool
    retreat: bool
    use_unit_micro: bool
    move_formation: Formation
    ENEMY_UNIT_NOTICE_DISTANCE = 15
    ENEMY_UNIT_NOTICE_DISTANCE_PHOENIX = 30

    def __init__(self, knowledge):
        self.knowledge: 'Knowledge' = knowledge
        self.ai: BotAI = knowledge.ai
        self.unit_values: UnitValue = knowledge.unit_values
        self.cache = self.knowledge.unit_cache

        # Public properties / Fields:

        # Units will focus on priority targets
        self.focus_fire = True
        # Units will stutter step when moving towards a target
        self.offensive_stutter_step = True
        # Units will stutter step away when facing enemies with shorter range
        self.defensive_stutter_step = True
        # Units will automatically retreat away from the battlefield when severely wounded.
        self.retreat = True
        # Allows disabling ability usage.
        self.use_unit_micro = True
        # Does the unit attempt to maintain formation with other units.
        self.move_formation = Formation.Ball

        self.unit_goals: List[CombatGoal] = []
        self.tags: List[int] = []

        self._kite = DefensiveKite(self.knowledge)
        self._push = OffensivePush(self.knowledge)
        self._targeting = EnemyTargeting(self.knowledge)
        self.specific_micro_dict: Dict[UnitTypeId, "StateStep"] = dict()
        self.specific_micro_dict[UnitTypeId.SENTRY] = StateSentry(self.knowledge)
        self.specific_micro_dict[UnitTypeId.PHOENIX] = StatePhoenix(self.knowledge, self)
        self.specific_micro_dict[UnitTypeId.DISRUPTOR] = StateDisruptor(self.knowledge)
        self.specific_micro_dict[UnitTypeId.DISRUPTORPHASED] = StatePurificationNova(self.knowledge)
        self.specific_micro_dict[UnitTypeId.ORACLE] = StateOracle(self.knowledge)
        self.specific_micro_dict[UnitTypeId.ADEPT] = StateAdept(self.knowledge)
        self.specific_micro_dict[UnitTypeId.SIEGETANK] = StateSiegetank(self.knowledge)
        self.specific_micro_dict[UnitTypeId.MEDIVAC] = StateMedivac(self.knowledge)
        self.specific_micro_dict[UnitTypeId.OBSERVER] = StateObserver(self.knowledge)
        self.specific_micro_dict[UnitTypeId.VIKINGFIGHTER] = StateViking(self.knowledge)
        self.specific_micro_dict[UnitTypeId.RAVEN] = StateRaven(self.knowledge)
        self.specific_micro_dict[UnitTypeId.RAVAGER] = StateRavager(self.knowledge)
        self.specific_micro_dict[UnitTypeId.VOIDRAY] = StateVoidray(self.knowledge)
        self.specific_micro_dict[UnitTypeId.STALKER] = StateStalker(self.knowledge)
        self.specific_micro_dict[UnitTypeId.BATTLECRUISER] = StateBattleCruiser(self.knowledge)
        self.specific_micro_dict[UnitTypeId.WARPPRISM] = StateWarpPrism(self.knowledge)

        self.ball_formation = BallFormation(self.knowledge)

        # Units will prioritise workers above all. Useful for harassment.
        self.prioritise_workers = False
        self.units_median = Point2((0,0))

    @property
    def prioritise_workers(self) -> bool:
        return self._targeting.focus_workers

    @prioritise_workers.setter
    # Units will prioritise workers above all. Useful for harassment.
    def prioritise_workers(self, value: bool):
        self._targeting.focus_workers = value

    def addUnit(self, unit: Unit, target: Point2, move_type = MoveType.Assault):
        if unit.type_id == UnitTypeId.MULE: # Just no
            return
        self.unit_goals.append(CombatGoal(unit, target, move_type))
        self.tags.append(unit.tag)

    def execute(self):
        # Units need to be ready to be counted as possible targets for combat

        our_units = self.get_all_units()
        self.units_median = unit_geometric_median(our_units)
        dict_units_enemy_data: Dict[int, EnemyData] = self.preload_enemy_data(our_units, self.units_median)

        if self.move_formation == Formation.Ball:
            if any(self.unit_goals):
                self.ball_formation.prepare_solve(our_units, self.unit_goals[0].target, dict_units_enemy_data, self.units_median)


        for goal in self.unit_goals:
            unit: Unit = goal.unit
            move_type: MoveType = goal.move_type
            target = goal.target
            goal.set_shoot_status(self.knowledge)

            enemy_data = dict_units_enemy_data[unit.tag]
            real_type = self.unit_values.real_type(unit.type_id)
            type_micro: StateStep = self.specific_micro_dict.get(real_type, None)

            if move_type in {MoveType.Assault, MoveType.SearchAndDestroy, MoveType.Harass}:
                # Default command is attack move
                command = CombatAction(unit, target, True)
            else:
                # Default command is move
                command = CombatAction(unit, target, False)

            if move_type == MoveType.PanicRetreat:
                # Panic escape using any abilities available
                if type_micro is not None and self.use_unit_micro:
                    command = type_micro.PanicRetreat(goal, command, enemy_data)
            elif enemy_data.enemies_exist:
                # Combat movement and focus fire
                command = self.solve_combat(goal, command, enemy_data)
            elif self.move_formation == Formation.Ball and goal.move_type != MoveType.DefensiveRetreat:
                command = self.ball_formation.solve_combat(goal, command)

            if move_type == MoveType.Harass and command.target is Point2 and command.is_attack:
                # this is to prevent the adept / oracle / harass unit from attacking buildings
                command.is_attack = False

            if type_micro is not None and self.use_unit_micro:
                command = type_micro.FinalSolve(goal, command, enemy_data)

            self.execute_command(unit, command)

        self.unit_goals.clear()
        self.tags.clear()

    def preload_enemy_data(self, our_units: Units, units_median: Point2) -> Dict[int, EnemyData]:
        dict_units_enemy_data: Dict[int, EnemyData] = dict()

        for goal in self.unit_goals:
            unit: Unit = goal.unit
            if unit.type_id == UnitTypeId.PHOENIX:
                close_enemies: Units = self.cache.enemy_in_range(unit.position, CombatManager.ENEMY_UNIT_NOTICE_DISTANCE_PHOENIX)
            else:
                close_enemies: Units = self.cache.enemy_in_range(unit.position, CombatManager.ENEMY_UNIT_NOTICE_DISTANCE)

            # Fix for Chargelot build overlords
            close_enemies = close_enemies.exclude_type(UnitTypeId.OVERLORD)
            enemy_data = EnemyData(self.knowledge, close_enemies, unit, our_units, units_median)

            dict_units_enemy_data[unit.tag] = enemy_data

        return dict_units_enemy_data

    def get_all_units(self) -> Units:
        units = Units([], self.ai)
        for cmd in self.unit_goals:
            units.append(cmd.unit)
        return units

    @property
    def beaming_phoenixes(self) -> Units:
        """Returns all our Phoenixes that are using Graviton Beam."""
        phoenixes = self.cache.own(UnitTypeId.PHOENIX).filter(lambda p: len(p.orders) > 0)
        beaming_phoenixes = phoenixes.filter(lambda p: p.orders[0].ability.id == AbilityId.GRAVITONBEAM_GRAVITONBEAM)
        return beaming_phoenixes

    @property
    def beaming_phoenix_tags(self) -> List[int]:
        return list(map(lambda p: p.tag, self.beaming_phoenixes))

    @property
    def beamed_unit_tags(self) -> List[int]:
        """Returns tags of units being beamed by our Phoenixes."""
        phoenixes = self.cache.own(UnitTypeId.PHOENIX).filter(lambda p: len(p.orders) > 0)
        orders = map(lambda p: p.orders[0], phoenixes)
        graviton_orders = filter(lambda o: o.ability.id == AbilityId.GRAVITONBEAM_GRAVITONBEAM, orders)
        graviton_targets = map(lambda go: go.target, graviton_orders)
        return list(graviton_targets)

    @property
    def get_beamed_units(self) -> Units:
        """Returns units being beamed by our Phoenixes."""
        tags = self.beamed_unit_tags
        return self.knowledge.known_enemy_units.tags_in(tags)

    def solve_combat(self, goal: CombatGoal, command: CombatAction, enemy_data: EnemyData) -> CombatAction:
        unit: Unit = goal.unit
        move_type: MoveType = goal.move_type
        target: Point2 = goal.target

        finalActions: List[CombatAction] = []
        type_micro = self.specific_micro_dict.get(unit.type_id, None)

        if type_micro is not None and self.use_unit_micro:
            finalActions = type_micro.solve_combat(goal, command, enemy_data)

        if len(finalActions) == 0 and self.defensive_stutter_step:
            finalActions = self._kite.solve_combat(goal, command, enemy_data)
        if len(finalActions) == 0 and self.offensive_stutter_step and goal.move_type in {MoveType.Assault, MoveType.Harass}:
            finalActions = self._push.solve_combat(goal, command, enemy_data)

        if len(finalActions) == 0:
            # Set default action as command
            finalActions = [command]

        if finalActions[0].is_attack and self.focus_fire:
            result = self._targeting.solve_combat(goal, finalActions[0], enemy_data)
            if len(result) == 1:
                finalActions[0] = result[0]

        if len(finalActions) == 2:
            if goal.ready_to_shoot:
                return finalActions[0]
            else:
                return finalActions[1]
        elif len(finalActions) == 1:
            return finalActions[0]
        return command

    def execute_command(self, unit: Unit, command: CombatAction):
        if command.ability is not None:
            action = unit(command.ability, command.target)
        elif command.is_attack:
            action = unit.attack(command.target)
        else:
            action = unit.move(command.target)

        if self.prevent_double_actions(action):
            self.ai.do(action)

    def prevent_double_actions(self, action):
        # always add actions if queued
        if action.queue:
            return True
        if action.unit.orders:
            # action: UnitCommand
            # current_action: UnitOrder
            current_action = action.unit.orders[0]
            # different action
            if current_action.ability.id != action.ability:
                return True
            if (
                isinstance(current_action.target, int)
                and isinstance(action.target, Unit)
                and current_action.target == action.target.tag
            ):
                # remove action if same target unit
                return False
            elif (
                isinstance(action.target, Point2)
                and isinstance(current_action.target, common_pb.Point)
                and (action.target.x, action.target.y) == (current_action.target.x, current_action.target.y)
            ):
                # remove action if same target position
                return False
        return True