from sc2 import UnitTypeId, BotAI, AbilityId
from sc2.unit import Unit
from sc2.units import UnitSelection


class UseNeuralParasiteDummy(BotAI):
    """Dummy that creates an infestor and then uses neural parasite on a random enemy unit."""

    async def on_step(self, iteration: int):
        if iteration == 0:
            await self.my_init()

        infestors: UnitSelection = self.units(UnitTypeId.INFESTOR)
        if not infestors.exists:
            return

        infestor: Unit = infestors.random
        if not infestor.energy > 100:
            return

        if not self.enemy_units.exists:
            return

        enemy_unit = self.enemy_units.random

        self.do(infestor(AbilityId.NEURALPARASITE_NEURALPARASITE, enemy_unit))

    async def my_init(self):
        # Enemy main
        pos = self.enemy_start_locations[0]

        player_id = self.player_id

        await self._client.debug_create_unit([[UnitTypeId.INFESTOR, 1, pos, player_id]])

        # Enables neural parasite ability, among other things.
        await self._client.debug_tech_tree()
