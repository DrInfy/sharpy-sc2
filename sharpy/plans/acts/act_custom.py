from typing import Callable
from sharpy.plans.acts import ActBase


class ActCustom(ActBase):
    def __init__(self, func: Callable[[], bool]):
        # function
        super().__init__()
        self.func = func

    async def execute(self) -> bool:
        return self.func()
