import warnings

import sc2

from sharpy.plans.require.require_base import RequireBase


class Gas(RequireBase):
    """Require that a specific number of minerals are "in the bank"."""

    def __init__(self, vespene_requirement: int):
        assert vespene_requirement is not None and isinstance(vespene_requirement, int)
        super().__init__()

        self.vespene_requirement = vespene_requirement

    def check(self) -> bool:
        if self.ai.vespene > self.vespene_requirement:
            return True
        return False


class RequiredGas(Gas):
    def __init__(self, vespene_requirement: int):
        warnings.warn("'RequiredGas' is deprecated, use 'Gas' instead", DeprecationWarning, 2)
        super().__init__(vespene_requirement)
