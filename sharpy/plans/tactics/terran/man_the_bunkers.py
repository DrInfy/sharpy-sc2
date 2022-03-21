from sc2.ids.ability_id import AbilityId
from sharpy.plans.acts import ActBase
from sharpy.managers.core.roles import UnitTask
from sc2.ids.unit_typeid import UnitTypeId


class ManTheBunkers(ActBase):
    def __init__(self):
        super().__init__()

    async def execute(self) -> bool:
        roles: "UnitRoleManager" = self.roles
        bunkers = self.cache.own(UnitTypeId.BUNKER).ready
        marines = self.cache.own(UnitTypeId.MARINE)

        for bunker in bunkers:  # type: Unit
            if len(bunker.passengers) >= 4:
                continue
            if marines:
                marine = marines.closest_to(bunker)  # .prefer_idle()
                marine(AbilityId.SMART, bunker)
                roles.set_task(UnitTask.Reserved, marine)
        return True
