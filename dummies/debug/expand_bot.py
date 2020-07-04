from sharpy.plans.tactics import DistributeWorkers
from sc2 import UnitTypeId

from sharpy.knowledges import KnowledgeBot
from sharpy.plans import BuildOrder
from sharpy.plans.acts import Expand


class ExpandDummy(KnowledgeBot):
    """Dummy bot for testing RestorePower act."""

    def __init__(self):
        super().__init__("ExpandDummy")

    async def create_plan(self) -> BuildOrder:
        return BuildOrder(Expand(2, priority=True, consider_worker_production=False), DistributeWorkers())
