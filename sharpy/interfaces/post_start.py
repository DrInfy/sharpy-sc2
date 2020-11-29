from abc import ABC, abstractmethod


class IPostStart(ABC):
    """
    Identifies that the manager needs to be called with a post_start method
    after all the managers have been properly started.
    """

    @abstractmethod
    async def post_start(self):
        pass
