from typing import Optional

from sc2 import UnitTypeId, BotAI, AbilityId
from sc2.game_data import AbilityData
from sc2.unit import Unit, UnitOrder
from .act_base import ActBase


class CancelBuilding(ActBase):
    """
    Act of canceling a building to change strategy. Defaults to a single use of cancel in order to prevent endless
    build -> cancel -> build loops.
    """

    def __init__(self, unit_type: UnitTypeId, to_count: int, allowed_cancel_count: int = 1):
        assert unit_type is not None and isinstance(unit_type, UnitTypeId)
        assert to_count is not None and isinstance(to_count, int)

        self.unit_type = unit_type
        self.to_count = to_count
        self.allowed_cancel_count = allowed_cancel_count
        self.cancelled_count = 0
        super().__init__()

    async def execute(self):
        if 0 < self.allowed_cancel_count <= self.cancelled_count:
            return True  # Step is done, no more cancels left

        count = self.get_count(self.unit_type)

        if count <= self.to_count:
            return True  # Step is done

        creation_ability: AbilityData = self.ai._game_data.units[self.unit_type.value].creation_ability
        worker: Unit

        for worker in self.ai.workers:  # type: Unit
            for order in worker.orders:  # type: UnitOrder
                if (order.ability.id == creation_ability.id):
                    self.cancelled_count += 1
                    count -= 1
                    self.do(worker.stop())  # cancel the order
                    self.print(f'Stopping {self.unit_type.name}')

        building: Unit
        for building in self.cache.own(self.unit_type).not_ready:
            if count <= self.to_count:
                return True  # Step is done
            self.cancelled_count += 1
            count -= 1
            self.do(building(AbilityId.CANCEL_BUILDINPROGRESS))
            self.print(f'Canceling {self.unit_type.name}')

        return True  # Step is done
