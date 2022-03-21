from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from sharpy.interfaces import IZoneManager
from sharpy.plans.acts import ActBase
from sharpy.managers.core.roles import UnitTask
from sharpy.knowledges import Knowledge


class PlanMainDefender(ActBase):
    def __init__(self):
        super().__init__()
        self.sentry_tag = None

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)
        self.roles = self.roles
        zone_manager = knowledge.get_required_manager(IZoneManager)
        base_ramp = zone_manager.expansion_zones[0].ramp
        if base_ramp:
            self.gather_point = base_ramp.top_center.towards(base_ramp.bottom_center, -4)
        else:
            self.gather_point = zone_manager.expansion_zones[0].center_location.towards(
                zone_manager.enemy_start_location, 8
            )

    async def execute(self):
        if self.knowledge.enemy_race != Race.Zerg:
            return True  # never block

        if self.sentry_tag is None:
            idle = self.roles.all_from_task(UnitTask.Idle)
            sentries = idle(UnitTypeId.SENTRY)
            if sentries.exists:
                sentry = sentries.first
                self.sentry_tag = sentry.tag
                self.roles.set_task(UnitTask.Reserved, sentry)
                self.combat.add_unit(sentry)
        else:
            sentry = self.cache.by_tag(self.sentry_tag)
            if sentry is None:
                self.sentry_tag = None
            else:
                self.combat.add_unit(sentry)

        self.combat.execute(self.gather_point)

        return True  # never block
