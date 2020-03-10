from sharpy.plans.acts import ActBase
from sharpy.managers.roles import UnitTask
from sc2 import UnitTypeId, AbilityId


class ManTheBunkers(ActBase):
    def __init__(self):
        super().__init__()

    async def execute(self) -> bool:
        roles: 'UnitRoleManager' = self.knowledge.roles
        bunkers = self.cache.own(UnitTypeId.BUNKER).ready
        marines = self.cache.own(UnitTypeId.MARINE)

        for bunker in bunkers: # type: Unit
            if len(bunker.passengers) >= 4:
                continue
            if marines:
                marine = marines.closest_to(bunker) #.prefer_idle()
                self.do(marine(AbilityId.SMART, bunker))
                roles.set_task(UnitTask.Reserved, marine)
        return True
