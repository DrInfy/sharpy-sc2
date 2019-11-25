from abc import abstractmethod
from frozen.plans.acts import ActBase


class RequireBase(ActBase):

    async def execute(self) -> bool:
        return self.check()

    @abstractmethod
    def check(self) -> bool:
        pass
