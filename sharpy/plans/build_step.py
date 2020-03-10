from typing import Optional, Callable, Union

# Singular step of action
from sharpy.plans.require import RequireCustom
from sharpy.plans.require.require_base import RequireBase
from sharpy.plans.acts.act_base import ActBase

class Step(ActBase):
    def __init__(self,
                 requirement: Optional[Union[RequireBase, Callable[['Knowledge'], bool]]],
                 action: Optional[ActBase],
                 skip: Optional[Union[RequireBase, Callable[['Knowledge'], bool]]] = None,
                 skip_until: Optional[Union[RequireBase, Callable[['Knowledge'], bool]]] = None):
        assert requirement is None or isinstance(requirement, RequireBase) or isinstance(requirement, Callable)
        assert action is None or isinstance(action, ActBase)
        assert skip is None or isinstance(skip, RequireBase) or isinstance(skip, Callable)
        assert skip_until is None or isinstance(skip_until, RequireBase) or isinstance(skip_until, Callable)
        super().__init__()

        self.requirement = requirement
        self.action = action
        self.skip = skip
        self.skip_until = skip_until

        if isinstance(self.requirement, Callable):
            self.requirement = RequireCustom(self.requirement)
        if isinstance(self.skip, Callable):
            self.skip = RequireCustom(self.skip)

        if isinstance(self.skip_until, Callable):
            self.skip_until = RequireCustom(self.skip_until)

    async def debug_draw(self):
        if self.requirement is not None:
            await self.requirement.debug_draw()
        if self.action is not None:
            await self.action.debug_draw()
        if self.skip is not None:
            await self.skip.debug_draw()
        if self.skip_until is not None:
            await self.skip_until.debug_draw()

    async def start(self, knowledge: 'Knowledge'):
        if self.requirement != None:
            await self.requirement.start(knowledge)
        if self.action != None:
            await self.action.start(knowledge)
        if self.skip != None:
            await self.skip.start(knowledge)
        if self.skip_until != None:
            await self.skip_until.start(knowledge)

    async def execute(self) -> bool:
        if self.skip is not None and self.skip.check():
            return True
        if self.skip_until is not None and not self.skip_until.check():
            return True
        if self.requirement is not None and not self.requirement.check():
            return False

        if self.action is None:
            return True

        return await self.action.execute()



