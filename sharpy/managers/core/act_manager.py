import asyncio

from .manager_base import ManagerBase
from typing import TYPE_CHECKING, Coroutine, Union, Callable

from sharpy.interfaces import IPostStart

if TYPE_CHECKING:
    from sharpy.knowledges import Knowledge
    from sharpy.plans.acts import ActBase


class ActManager(ManagerBase, IPostStart):
    _act: "ActBase"

    def __init__(self, act_or_func: Union[Callable[[], Coroutine], "ActBase"]) -> None:
        super().__init__()
        self._act_or_func: Union[Callable[[], Coroutine], "ActBase"] = act_or_func

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)

    async def post_start(self):
        if asyncio.iscoroutinefunction(self._act_or_func):
            self._act = await self._act_or_func()
        else:
            self._act = self._act_or_func

        await self.start_component(self._act, self.knowledge)

    async def update(self):
        await self._act.execute()

    async def post_update(self):
        if self.knowledge.debug:
            await self._act.debug_draw()
