from typing import List

from sc2 import BotAI

from sharpy.plans.require import RequireBase

class RequiredAll(RequireBase):
    """Check passes if all of the conditions are true."""
    def __init__(self, conditions: List[RequireBase]):
        super().__init__()
        assert conditions is not None and isinstance(conditions, List)
        self.conditions: List[RequireBase] = conditions


    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)

        for condition in self.conditions:
            await condition.start(knowledge)

    def check(self) -> bool:
        for condition in self.conditions:
            if not condition.check():
                return False

        return True
