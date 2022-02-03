from sc2.bot_ai import BotAI


class IdleDummy(BotAI):
    """A debug dummy bot that does literally nothing."""

    async def on_step(self, iteration: int):
        pass
