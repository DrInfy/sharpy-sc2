from typing import Optional

from sc2.ids.ability_id import AbilityId
from sharpy.interfaces import IZoneManager
from sharpy.managers.extensions import BuildDetector
from sharpy.plans.acts import ActBase
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from sharpy.managers.core.roles import UnitTask

HALLUCINATION_ENERGY_COST = 75


class HallucinatedPhoenixScout(ActBase):
    """
    Creates hallucinated phoenixes with sentries and uses them as scouts.

    time_interval is seconds.
    """

    build_detector: BuildDetector
    zone_manager: IZoneManager

    def __init__(self, time_interval: int = 60):
        super().__init__()
        self.time_interval: int = time_interval
        # When we last created a hallucinated phoenix scout
        self.last_created: int = -1
        self.last_target: Optional[Point2] = None
        self.current_phoenix_tag: Optional[int] = None

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.build_detector = knowledge.get_manager(BuildDetector)
        self.zone_manager = knowledge.get_required_manager(IZoneManager)

    async def execute(self) -> bool:
        phoenix = await self.get_hallucinated_phoenix()
        if phoenix:
            self.roles.set_task(UnitTask.Scouting, phoenix)
            self.move_phoenix(phoenix)
        if not phoenix and self.should_send_scout:
            # We should have a Phoenix on the next iteration
            self.create_hallucinated_phoenix()

        return True  # Non blocking

    async def get_hallucinated_phoenix(self) -> Optional[Unit]:
        if self.current_phoenix_tag is not None:
            phoenix = self.roles.units(UnitTask.Scouting).find_by_tag(self.current_phoenix_tag)
            if phoenix is not None:
                return phoenix
            # Phoenix does not exist anymore
            self.current_phoenix_tag = None

        phoenixes = self.roles.get_types_from({UnitTypeId.PHOENIX}, UnitTask.Hallucination)

        if phoenixes.exists:
            phoenix = phoenixes[0]
            self.current_phoenix_tag = phoenix.tag
            return phoenix
        return None

    def create_hallucinated_phoenix(self):
        sentries: Units = self.cache.own(UnitTypeId.SENTRY)

        if not sentries.exists:
            return

        another_sentry_with_energy_exists = False

        for sentry in sentries:
            # we don't want to actually spend all energy to make hallucination
            if sentry.energy > HALLUCINATION_ENERGY_COST + 50 or (
                another_sentry_with_energy_exists and sentry.energy > HALLUCINATION_ENERGY_COST
            ):
                if self.ai.enemy_units.closer_than(15, sentry):
                    # Don't make combat hallucinated phoenixes1
                    continue

                # todo: should reserve a sentry for this purpose or at least reserve most of it's energy for this.
                # self.knowledge.add_reserved_unit(sentry.tag)
                sentry(AbilityId.HALLUCINATION_PHOENIX)

                self.last_created = self.knowledge.ai.time
                return

            elif sentry.energy > 50:  # force field
                another_sentry_with_energy_exists = True

    @property
    def should_send_scout(self) -> bool:
        if self.build_detector and self.build_detector.rush_detected and self.ai.time < 5 * 60:
            return False  # no scout in first 5 min if rush incoming
        return self.last_created + self.time_interval < self.knowledge.ai.time

    def move_phoenix(self, phoenix: Unit):
        target = self.select_target()
        phoenix.move(target)

        if target != self.last_target:
            self.last_target = target
            self.print(f"scouting {target}, interval {self.time_interval}")

    def select_target(self) -> Point2:
        # todo: there just might be a linear function here...
        if self.ai.time < 6 * 60:
            targets = self.zone_manager.enemy_expansion_zones[0:3]
        elif self.ai.time < 8 * 60:
            targets = self.zone_manager.enemy_expansion_zones[0:4]
        elif self.ai.time < 10 * 60:
            targets = self.zone_manager.enemy_expansion_zones[0:5]
        else:
            # This includes our bases as well (sorted to the end), but the hallucination
            # won't live long enough to scout all bases.
            targets = self.zone_manager.enemy_expansion_zones

        targets.sort(key=lambda z: z.last_scouted_mineral_line)
        if len(targets) > 0:
            return targets[0].mineral_line_center

        return self.zone_manager.enemy_main_zone.mineral_line_center
