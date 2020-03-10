from typing import List

from sharpy.plans.require.require_base import RequireBase

class RequiredCount(RequireBase):
    # If any of the conditions is filled, we're good to go
    def __init__(self, count: int, conditions: List[RequireBase]):
        assert count is not None and isinstance(count, int)
        super().__init__()

        self.conditions:List[RequireBase] = conditions
        self.count = count

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        for condition in self.conditions:
            await condition.start(knowledge)

    def check(self) -> bool:
        amount = 0
        for condition in self.conditions:
            if condition.check():
                amount += 1

        return amount >= self.count
