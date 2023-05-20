from typing import List, Dict, Optional

from sc2.ids.ability_id import AbilityId
from sharpy.combat.protoss import MicroAdepts
from sharpy.interfaces import IZoneManager, IEnemyUnitsManager
from sharpy.managers.extensions import BuildDetector
from sharpy.plans.acts import ActBase
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from sharpy.general.zone import Zone
from sharpy.combat import MoveType, MicroRules
from sharpy.managers.core.roles import UnitTask


class DoubleAdeptScout(ActBase):
    ZONE_DISTANCE_THRESHOLD_SQUARED = 9 * 9
    micro: MicroRules
    build_detector: BuildDetector
    zone_manager: IZoneManager
    enemy_units_manager: IEnemyUnitsManager

    def __init__(self, adepts_to_start: int = 2):
        super().__init__()
        self.started = False
        self.ended = False
        self.scout_tags: List[int] = []

        self.target_zone: Zone = []
        self.target_position: Point2 = None
        # Zones will be without workers until at least the specified time
        self.empty_zone_until: Dict[Zone, float] = []
        self.is_behind_minerals = False

        self.target_changed = False
        self.adept_target = False
        self.adepts_to_start = adepts_to_start

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.micro = MicroRules()
        self.micro.load_default_methods()
        self.micro.generic_micro = MicroAdepts(False)
        self.build_detector = knowledge.get_manager(BuildDetector)
        self.zone_manager = knowledge.get_required_manager(IZoneManager)
        self.enemy_units_manager = knowledge.get_required_manager(IEnemyUnitsManager)
        await self.micro.start(knowledge)

    async def execute(self) -> bool:
        if self.build_detector and self.build_detector.rush_detected:
            self.roles.clear_tasks(self.scout_tags)
            self.scout_tags.clear()
            return True  # Never block

        if not self.zone_manager.enemy_start_location_found:
            # We don't know where to go just yet
            return True  # Never block

        if self.ended:
            return True  # Never block

        if not self.started:
            await self.check_start()

        if self.started:
            adepts: Units = Units([], self.ai)
            for tag in self.scout_tags:
                adept: Unit = self.cache.by_tag(tag)
                if adept is not None:
                    adepts.append(adept)
            if len(adepts) == 0:
                await self.end_scout()
            else:
                await self.micro_adepts(adepts)

        return True  # Never block

    async def micro_adepts(self, adepts: Units):
        center = adepts.center

        targets: (Point2, Point2) = await self.select_targets(center)

        if targets is None:
            self.ended = True
            return

        self.roles.refresh_tasks(adepts)

        if self.target_position != targets[0]:
            self.print(f"target changed to: {targets[0]}")
        self.target_position = targets[0]

        if self.adept_target != targets[1]:
            self.adept_target = targets[1]
            self.target_changed = True

        local_target = self.pather.find_path(center, self.target_position)
        shade_distance = center.distance_to(self.target_position)  # TODO: Use ground distance

        for adept in adepts:  # type: Unit
            shade_tag = self.cd_manager.adept_to_shade.get(adept.tag, None)
            if shade_tag is not None:
                shade = self.cache.by_tag(shade_tag)
                if self.cd_manager.is_ready(adept.tag, AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT, 6.9):
                    # Determine whether to cancel the shade or not
                    if self.enemy_units_manager.danger_value(
                        adept, adept.position
                    ) < self.enemy_units_manager.danger_value(adept, shade.position):
                        # It's safer to not phase shift
                        adept(AbilityId.CANCEL_ADEPTPHASESHIFT)
                        continue

            if self.cd_manager.is_ready(adept.tag, AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT) and (
                shade_distance < 11 or shade_distance > 30
            ):
                adept(AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT, self.adept_target)
                self.cd_manager.used_ability(adept.tag, AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT)
                self.target_changed = False
                self.print(f"Using phase shift to: {self.adept_target}")
            else:
                self.combat.add_unit(adept)

        self.combat.execute(local_target, MoveType.Harass, rules=self.micro)

    async def select_targets(self, center: Point2) -> (Point2, Point2):
        """ Returns none if no valid target was found. """
        closest_viable_zone: Zone = None
        second_viable_zone: Zone = None
        current_zone_index: Optional[int] = None
        enemy_zones: List[Zone] = self.zone_manager.enemy_expansion_zones

        for i in range(0, len(enemy_zones)):
            zone = enemy_zones[i]
            distance = center.distance_to(zone.center_location)
            # TODO: missing conditions
            if distance < 12:
                current_zone_index = i
            if zone.is_enemys and closest_viable_zone is None:
                closest_viable_zone = zone
            else:
                if closest_viable_zone is None:
                    if zone.could_have_enemy_workers_in < self.ai.time:
                        closest_viable_zone = zone
                else:
                    # we have a viable zone
                    if zone.is_enemys and not closest_viable_zone.is_enemys:
                        closest_viable_zone = zone
                    elif zone.is_enemys:
                        # both are enemy zones
                        if current_zone_index == i:
                            if (
                                zone.could_have_enemy_workers_in < self.ai.time
                                and closest_viable_zone.could_have_enemy_workers_in < self.ai.time
                            ):
                                second_viable_zone = closest_viable_zone
                                closest_viable_zone = zone
                            elif zone.could_have_enemy_workers_in < self.ai.time:
                                closest_viable_zone = zone
                        elif zone.could_have_enemy_workers_in < self.ai.time:
                            if second_viable_zone is None:
                                second_viable_zone = zone

        if closest_viable_zone is None:
            return None

        if second_viable_zone:
            return (
                await self.get_zone_closest(closest_viable_zone, center),
                await self.get_zone_closest(second_viable_zone, center),
            )

        return (
            await self.get_zone_closest(closest_viable_zone, center),
            await self.get_zone_furthest(closest_viable_zone, center),
        )

    async def get_zone_target(self, zone: Zone, center) -> Point2:
        if self.is_behind_minerals:
            target_position = await self.get_zone_furthest(zone, center)
        else:
            target_position = await self.get_zone_closest(zone, center)

        return target_position

    async def get_zone_closest(self, zone: Zone, center) -> Point2:
        target_position = zone.behind_mineral_position_center  # default position
        if zone.mineral_fields.exists and len(zone.behind_mineral_positions) > 0:
            distance = 9999999

            for pos in zone.behind_mineral_positions:
                d2 = center.distance_to(pos)
                if d2 < 10:
                    self.is_behind_minerals = True
                if d2 < distance:
                    # Get closest position
                    target_position = pos
                    distance = d2

        return target_position

    async def get_zone_furthest(self, zone: Zone, center) -> Point2:
        target_position = zone.behind_mineral_position_center  # default position
        if zone.mineral_fields.exists and len(zone.behind_mineral_positions) > 0:
            distance = 0
            for pos in zone.behind_mineral_positions:
                d2 = center.distance_to(pos)
                if d2 > distance:
                    # Get furthest away position
                    target_position = pos
                    distance = d2

        return target_position

    async def end_scout(self):
        self.started = False
        self.ended = True
        self.roles.clear_tasks(self.scout_tags)
        self.scout_tags.clear()
        self.is_behind_minerals = False

    async def check_start(self):
        adepts: Units = self.roles.free_units(UnitTypeId.ADEPT)
        if adepts.amount >= self.adepts_to_start:
            self.started = True

            for adept in adepts:
                self.scout_tags.append(adept.tag)
                self.roles.set_tasks(UnitTask.Scouting, adepts)
                if len(self.scout_tags) >= self.adepts_to_start:
                    return
