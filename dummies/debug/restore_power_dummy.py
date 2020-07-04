from sharpy.plans.tactics import DistributeWorkers
from sc2 import UnitTypeId

from sharpy.knowledges import KnowledgeBot
from sharpy.plans import BuildOrder
from sharpy.plans.acts.protoss import RestorePower


class RestorePowerDummy(KnowledgeBot):
    """Dummy bot for testing RestorePower act."""

    def __init__(self):
        super().__init__("RestorePowerDummy")

    async def create_plan(self) -> BuildOrder:
        return BuildOrder([RestorePower(), DistributeWorkers()])

    async def on_step(self, iteration):
        # Hack so that BuildingSolver is finally ready to give positions for the debug buildings.
        if iteration == 1:
            await self.create_debug_buildings()

        await super().on_step(iteration)

    async def create_debug_buildings(self):
        grid_positions = self.knowledge.building_solver.building_position

        await self._client.debug_create_unit([[UnitTypeId.GATEWAY, 1, grid_positions[0], 1]])
        await self._client.debug_create_unit([[UnitTypeId.GATEWAY, 1, grid_positions[1], 1]])
        await self._client.debug_create_unit([[UnitTypeId.CYBERNETICSCORE, 1, grid_positions[2], 1]])

        await self._client.debug_create_unit([[UnitTypeId.STARGATE, 1, grid_positions[5], 1]])

        await self._client.debug_create_unit([[UnitTypeId.ROBOTICSFACILITY, 1, grid_positions[10], 1]])
