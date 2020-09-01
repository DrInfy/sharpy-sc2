import warnings
from sharpy.plans.require.require_base import RequireBase


class Minerals(RequireBase):
    """Require that a specific number of minerals are "in the bank"."""

    def __init__(self, mineral_requirement: int):
        assert mineral_requirement is not None and isinstance(mineral_requirement, int)
        super().__init__()

        self.mineralRequirement = mineral_requirement

    def check(self) -> bool:
        if self.ai.minerals > self.mineralRequirement:
            return True
        return False


class RequiredMinerals(Minerals):
    def __init__(self, mineral_requirement: int):
        warnings.warn("'RequiredMinerals' is deprecated, use 'Minerals' instead", DeprecationWarning, 2)
        super().__init__(mineral_requirement)
