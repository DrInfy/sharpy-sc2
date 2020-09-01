from sc2.unit_command import UnitCommand
from .manager_base import ManagerBase
from sc2 import BotAI, List, Set, AbilityId
from sc2.unit import Unit


class ActionIssued:
    """
    Individual action that is assigned to a unit. Used for preventing duplicate build orders.
    """

    def __init__(self, ai: BotAI, unit: Unit) -> None:
        self.ai = ai
        self.delay = 1
        if ai.realtime:
            self.delay = 10
        self.frame: int = ai.state.game_loop
        self.tag: int = unit.tag
        self.type_id = unit.type_id

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
        self.type_block = {AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, AbilityId.SCANNERSWEEP_SCAN}
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
                action.delay = 0  # Allow on next frame
                self.blocked.add(action.tag)

    def action_made(self, action: UnitCommand):
        tag = action.unit.tag
        self.actions.append(ActionIssued(self.ai, action.unit))

        if action.ability in self.type_block:
            # Block all units of the same type
            for unit in self.cache.own(action.unit.type_id):
                self.actions.append(ActionIssued(self.ai, unit))
        else:
            self.actions.append(ActionIssued(self.ai, action.unit))

        if tag not in self.blocked:
            self.blocked.add(tag)

    def allow_action(self, unit: Unit):
        return unit.tag not in self.blocked

    async def post_update(self):
        pass
