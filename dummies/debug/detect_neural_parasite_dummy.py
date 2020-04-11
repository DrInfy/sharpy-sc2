from sc2 import BotAI
from sc2.ids.buff_id import BuffId


class DetectNeuralParasiteDummy(BotAI):
    """A debug dummy bot that exists only to detect units that are being controlled by an infestor's neural parasite ability."""

    async def on_step(self, iteration: int):
        neuraled_units = self.enemy_units.filter(lambda u: BuffId.NEURALPARASITE in u.buffs)
        if neuraled_units.exists:
            for unit in neuraled_units:
                print(f"Iteration {iteration} - Unit {unit.type_id} {unit.tag} is being controlled by neural parasite")
