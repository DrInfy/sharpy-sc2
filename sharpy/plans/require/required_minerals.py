import sc2

from sharpy.plans.require.require_base import RequireBase


class RequiredMinerals(RequireBase):
    """Require that a specific number of minerals are "in the bank"."""
    def __init__(self, mineral_requirement: int):
        assert mineral_requirement is not None and isinstance(mineral_requirement, int)
        super().__init__()

        self.mineralRequirement = mineral_requirement

    def check(self) -> bool:
        if self.ai.minerals > self.mineralRequirement:
            return True
        return False
