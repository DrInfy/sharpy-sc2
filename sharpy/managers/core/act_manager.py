from .manager_base import ManagerBase
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sharpy.plans.acts import ActBase


class ActManager(ManagerBase):
    def __init__(self, act: "ActBase") -> None:
        super().__init__()
        self._act: "ActBase" = act

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        await self.start_component(self._act, knowledge)

    async def update(self):
        await self._act.execute()

    async def post_update(self):
        if self.knowledge.debug:
            await self._act.debug_draw()
