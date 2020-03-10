import sc2
from sc2.ids.upgrade_id import UpgradeId

from sharpy.plans.require.require_base import RequireBase


class RequiredTechReady(RequireBase):
    # Check at tech research progress
    """Require that a specific upgrade/technology already exists or is at
     least at the required percentage."""
    def __init__(self, upgrade: UpgradeId, percentage: float = 1):
        assert upgrade is not None and isinstance(upgrade, UpgradeId)
        assert percentage is not None and (isinstance(percentage, int) or isinstance(percentage, float))
        super().__init__()

        self.name = upgrade
        self.percentage = percentage

    def check(self) -> bool:
        if self.ai.already_pending_upgrade(self.name) >= self.percentage:
            return True
        return False
