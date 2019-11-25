from sc2.unit_command import UnitCommand
from .manager_base import ManagerBase
from sc2 import BotAI, List, Set
from sc2.unit import Unit


class ActionIssued():
    """
    Individual action that is assigned to a unit. Used for preventing duplicate build orders.
    """
    def __init__(self, ai: BotAI, unit_tag: int) -> None:
        self.ai = ai
        self.delay = 1
        if ai.realtime:
            self.delay = 10
        self.frame: int = ai.state.game_loop
        self.tag: int = unit_tag

    @property
    def is_old(self):
        if self.frame + self.delay < self.ai.state.game_loop:
            return True
        return False


class ActionHandler(ManagerBase):
    """
    Handles and allows preventing duplicate actions especially when using real time.
    """
    def __init__(self):
        self.actions: List[ActionIssued] = []
        self.blocked: Set[int] = set()
        super().__init__()

    async def update(self):
        self.blocked.clear()

        for i in range(0, len(self.actions) - 1)[::-1]:
            action = self.actions[i]
            if action.is_old:
                self.actions.pop(i)
            elif action.tag not in self.blocked:
                self.blocked.add(action.tag)

    def action_made(self, action: UnitCommand):
        tag = action.unit.tag
        self.actions.append(ActionIssued(self.ai, tag))

        if tag not in self.blocked:
            self.blocked.add(tag)

    def allow_action(self, unit: Unit):
        return unit.tag not in self.blocked

    async def post_update(self):
        pass
