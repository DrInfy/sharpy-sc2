from typing import Callable, Optional, Coroutine

from sharpy.managers import ManagerBase


class CustomFuncManager(ManagerBase):
    def __init__(
        self, update_func: Callable[[], Coroutine], post_update_func: Optional[Callable[[], Coroutine]] = None
    ) -> None:
        super().__init__()
        self._update_func = update_func
        self._post_update_func = post_update_func

    async def update(self):
        await self._update_func()

    async def post_update(self):
        if self._post_update_func is not None:
            self._post_update_func()
