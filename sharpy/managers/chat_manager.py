from typing import Optional, Callable

from sharpy.managers import ManagerBase


class ChatManager(ManagerBase):
    def __init__(self):
        super().__init__()
        self.taunted = set()
        self.debug_builds: Optional[str] = None
        self.debug_build_selection: Optional[str] = None

    async def chat_taunt_once(self, key: str, message: Callable[[], str]):
        # self.taunted.add(taunt_type)
        if not self.knowledge.is_chat_allowed or key in self.taunted:
            return True

        self.taunted.add(key)
        await self.ai.chat_send(message())

    async def chat_debug(self, message: str):
        if not self.knowledge.is_chat_allowed or self.ai.realtime:
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

