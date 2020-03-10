from sharpy.plans.require.require_base import RequireBase

class RequiredTime(RequireBase):
    # Condition for how many units must be ready.
    # Used mostly for buildings
    def __init__(self, time_in_seconds: float):
        assert time_in_seconds is not None and (isinstance(time_in_seconds, int) or isinstance(time_in_seconds, float))
        super().__init__()

        self.time_in_seconds = time_in_seconds

    def check(self) -> bool:
        if self.ai.time > self.time_in_seconds:
            return True
        return False
