from typing import Optional, Callable, Union, List

# Singular step of action
from sc2.unit import Unit
from sharpy.plans.acts import merge_to_act
from sharpy.plans.require import merge_to_require
from sharpy.plans.require.require_base import RequireBase
from sharpy.plans.acts.act_base import ActBase
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sharpy.knowledges import Knowledge


class IfElse(ActBase):
    def __init__(
        self,
        condition: Union[RequireBase, Callable[["BotAI"], bool]],
        action: Union[ActBase, Callable[["BotAI"], bool]],
        action_else: Optional[Union[ActBase, Callable[["BotAI"], bool]]] = None,
        skip: Optional[Union[RequireBase, Callable[["BotAI"], bool]]] = None,
        skip_until: Optional[Union[RequireBase, Callable[["BotAI"], bool]]] = None,
    ):
        assert isinstance(condition, RequireBase) or isinstance(condition, Callable)
        assert isinstance(action, ActBase) or isinstance(action, Callable)
        assert action_else is None or isinstance(action_else, ActBase) or isinstance(action_else, Callable)
        assert skip is None or isinstance(skip, RequireBase) or isinstance(skip, Callable)
        assert skip_until is None or isinstance(skip_until, RequireBase) or isinstance(skip_until, Callable)
        super().__init__()

        self.condition = merge_to_require(condition)
        self.action = merge_to_act(action)
        self.action_else = merge_to_act(action_else)
        self.skip = merge_to_require(skip)
        self.skip_until = merge_to_require(skip_until)

    async def debug_draw(self):
        await self.condition.debug_draw()
        await self.action.debug_draw()
        if self.action_else is not None:
            await self.action_else.debug_draw()
        if self.skip is not None:
            await self.skip.debug_draw()
        if self.skip_until is not None:
            await self.skip_until.debug_draw()

    async def start(self, knowledge: "Knowledge"):
        await self.start_component(self.condition, knowledge)
        await self.start_component(self.action, knowledge)
        if self.action_else is not None:
            await self.start_component(self.action_else, knowledge)
        if self.skip is not None:
            await self.start_component(self.skip, knowledge)
        if self.skip_until is not None:
            await self.start_component(self.skip_until, knowledge)

    async def execute(self) -> bool:
        if self.skip is not None and self.skip.check():
            return True
        if self.skip_until is not None and not self.skip_until.check():
            return True
        if self.condition.check():
            return await self.action.execute()
        if self.action_else is None:
            return True
        return await self.action_else.execute()

    def set_scouts(self, scouts: List[Unit]):
        if self.action is not None:
            assert hasattr(self.action, "set_scouts")
            # noinspection PyUnresolvedReferences
            self.action.set_scouts(scouts)
