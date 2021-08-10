from typing import Optional, Callable

from sharpy.managers.core import ManagerBase


class ChatManager(ManagerBase):
    def __init__(self):
        super().__init__()
        self.taunted = set()
        self.debug_builds: Optional[str] = None
        self.debug_build_selection: Optional[str] = None

    async def chat_taunt_once(self, key: str, message: Callable[[], str], log=True, team_only=False):
        if key in self.taunted:
            return True

        self.taunted.add(key)
        msg = message()
        if log:
            self.print(msg)

        await self.ai.chat_send(msg, team_only)

    async def chat_debug(self, message: str):
        if self.ai.realtime:
            return True
        await self.ai.chat_send(message)

    def store_debug_build_values(self, message: str):
        self.debug_builds = message
        self.print(message, stats=False)

    def store_debug_build_selection(self, message: str):
        self.debug_build_selection = message
        self.print(message, stats=False)

    async def update(self):
        if self.debug_builds and self.ai.time > 7:
            await self.chat_debug(self.debug_builds)
            self.debug_builds = None
        if self.debug_build_selection and self.ai.time > 11:
            await self.chat_debug(self.debug_build_selection)
            self.debug_build_selection = None

    async def post_update(self):
        pass
