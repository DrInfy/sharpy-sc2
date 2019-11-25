import sc2


class IntervalFunc:
    def __init__(self, ai: sc2.BotAI, func, timer_seconds: float):
        self.timer_seconds = timer_seconds
        self.ai = ai
        self.func = func
        self.cached_value = None
        self.last_call = None

    def execute(self):
        if self.last_call is None or self.ai.time > self.last_call + self.timer_seconds:
            self.last_call = self.ai.time
            self.cached_value = self.func()
        return self.cached_value

class IntervalFuncAsync:
    def __init__(self, ai: sc2.BotAI, func, timer_seconds: float):
        self.timer_seconds = timer_seconds
        self.ai = ai
        self.func = func
        self.cached_value = None
        self.last_call = None

    async def execute(self):
        if self.last_call is None or self.ai.time > self.last_call + self.timer_seconds:
            self.last_call = self.ai.time
            self.cached_value = await self.func()
        return self.cached_value