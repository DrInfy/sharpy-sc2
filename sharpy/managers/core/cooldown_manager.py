from typing import Dict, List, Optional, Set, Tuple

from sc2.game_state import EffectData
from sc2.ids.effect_id import EffectId
from sc2.position import Point2
from sharpy.managers.core.manager_base import ManagerBase
from sc2 import UnitTypeId, AbilityId, Race
from sc2.unit import Unit
from sc2.units import Units


class CooldownManager(ManagerBase):
    """
    Global cooldown manager that is shared between all units.
    TODO: Rename to ability manager?
    """

    def __init__(self):
        super().__init__()
        self.used_dict: Dict[int, Dict[AbilityId, float]] = dict()
        self.available_dict: Dict[int, List[AbilityId]] = dict()
        self.adept_to_shade: Dict[int, int] = dict()
        self.shade_to_adept: Dict[int, int] = dict()
        self._shade_tags_handled: Set[int] = set()
        self.own_liberator_zones: List[Tuple[int, Point2]] = []
        self.enemy_lib_zones: List[Tuple[Point2, EffectData]] = []

    @property
    def enemy_liberator_zones(self) -> List[Tuple[Point2, EffectData]]:
        if self.ai.race == Race.Terran:
            return self.enemy_lib_zones

        lib_zones: List[Tuple[Point2, EffectData]] = []
        lib_zones.extend(self.cache.effects(EffectId.LIBERATORTARGETMORPHDELAYPERSISTENT))
        lib_zones.extend(self.cache.effects(EffectId.LIBERATORTARGETMORPHPERSISTENT))
        return lib_zones

    async def update(self):
        self.available_dict.clear()
        if len(self.ai.all_own_units) < 1:
            return
        try:
            result: List[List[AbilityId]] = await self.ai.get_available_abilities(self.ai.all_own_units)
        except Exception as e:
            self.print(f"Get available abilities failed: {e}")
            return

        for i in range(0, len(self.ai.all_own_units)):
            self.available_dict[self.ai.all_own_units[i].tag] = result[i]

        if self.ai.race == Race.Protoss:
            self.manage_shades()
        elif self.ai.race == Race.Terran:
            self.manage_liberation_zones()

    def manage_shades(self):
        shades = self.cache.own(UnitTypeId.ADEPTPHASESHIFT)
        if len(shades) == 0:
            self.adept_to_shade.clear()
            self.shade_to_adept.clear()
            self._shade_tags_handled.clear()
        else:
            adepts: Units = self.cache.own(UnitTypeId.ADEPT)
            current_shade_tags = set()

            if adepts.exists:
                for shade in shades:  # type: Unit
                    current_shade_tags.add(shade.tag)
                    if shade.tag not in self._shade_tags_handled:
                        self._shade_tags_handled.add(shade.tag)
                        closest = adepts.closest_to(shade)
                        self.adept_to_shade[closest.tag] = shade.tag
                        self.shade_to_adept[shade.tag] = closest.tag

                tags = []
                for shade_tag in self.shade_to_adept.keys():
                    tags.append(shade_tag)

                for shade_tag in tags:
                    if shade_tag in current_shade_tags:
                        # Shade is still alive, move along
                        continue

                    # remove adept tag from dictionaries
                    adept_tag = self.shade_to_adept.get(shade_tag, None)
                    if adept_tag is not None and adept_tag in self.adept_to_shade:
                        self.adept_to_shade.pop(adept_tag)
                    self.shade_to_adept.pop(shade_tag)

    async def post_update(self):
        pass

    @property
    def time(self) -> float:
        return self.knowledge.ai.time

    def is_ready(self, unit_tag: int, ability: AbilityId, cooldown: Optional[float] = None) -> bool:
        if cooldown is None:
            return ability in self.available_dict.get(unit_tag, [])

        ability_dict = self.used_dict.get(unit_tag, None)
        if ability_dict is None:
            return True

        last_used = ability_dict.get(ability, -1000)

        return last_used + cooldown < self.time

    def used_ability(self, unit_tag: int, ability: AbilityId) -> None:
        ability_dict = self.used_dict.get(unit_tag, None)

        if ability_dict is None:
            ability_dict = {}
            self.used_dict[unit_tag] = ability_dict

        ability_dict[ability] = self.time

    def get_liberation_zone(self, unit_tag: int) -> Optional[Point2]:
        for tag, position in self.own_liberator_zones:
            if tag == unit_tag:
                return position
        return None

    def set_liberation_zone(self, unit_tag: int, target: Point2):
        for i in range(0, len(self.own_liberator_zones))[::-1]:
            tag, position = self.own_liberator_zones[i]
            if tag == unit_tag:
                self.own_liberator_zones.pop(i)
        self.own_liberator_zones.append((unit_tag, target))

    def manage_liberation_zones(self):
        lib_zones: List[Tuple[Point2, EffectData]] = []
        lib_zones.extend(self.cache.effects(EffectId.LIBERATORTARGETMORPHDELAYPERSISTENT))
        lib_zones.extend(self.cache.effects(EffectId.LIBERATORTARGETMORPHPERSISTENT))

        if not lib_zones:
            self.own_liberator_zones.clear()
            self.enemy_lib_zones = lib_zones
        else:
            for i in range(0, len(self.own_liberator_zones))[::-1]:
                own_lib_zone = self.own_liberator_zones[i]
                unit = self.cache.by_tag(own_lib_zone[0])

                if unit is None or (
                    unit.type_id != UnitTypeId.LIBERATORAG
                    and (
                        len(unit.orders) == 0
                        or (
                            unit.orders[0].ability.id != AbilityId.LIBERATORMORPHTOAG_LIBERATORAGMODE
                            and unit.orders[0].ability.id != AbilityId.MORPH_LIBERATORAGMODE
                        )
                    )
                ):
                    self.own_liberator_zones.pop(i)
                    continue

                used_zone: Optional[Tuple[Point2, EffectData]] = None

                for lib_zone in lib_zones:
                    if own_lib_zone[1] == lib_zone[0]:
                        used_zone = lib_zone
                        break

                if used_zone:
                    lib_zones.remove(used_zone)

            self.enemy_lib_zones = lib_zones
