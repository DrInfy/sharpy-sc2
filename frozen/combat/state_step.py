from abc import abstractmethod, ABC
from typing import List

import sc2
from frozen.general.unit_value import UnitValue
from frozen.knowledges import Knowledge
from frozen.managers import CooldownManager
from .combat_action import CombatAction
from .combat_goal import CombatGoal
from .enemy_data import EnemyData


class StateStep(ABC):

    def __init__(self, knowledge):
        self.knowledge: Knowledge = knowledge
        self.ai: sc2.BotAI = knowledge.ai
        self.unit_values: UnitValue = knowledge.unit_values
        self.cd_manager: CooldownManager = knowledge.cooldown_manager

    @abstractmethod
    def solve_combat(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData)\
            -> List[CombatAction]:
        pass

    def PanicRetreat(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> CombatAction:
        return command

    """Called at the end of combat manager cycle regardless of combat status, enemies data might not have any enemies !"""
    def FinalSolve(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> CombatAction:
        return command