from typing import Dict, List, Optional, Set

#from knowledges import Knowledge
from sharpy.managers.manager_base import ManagerBase
from sc2 import UnitTypeId, AbilityId
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

    async def update(self):
        self.available_dict.clear()
        if len(self.knowledge.all_own) < 1:
            return
        try:
            result: List[List[AbilityId]] = await self.ai.get_available_abilities(self.knowledge.all_own)
        except:
            self.print(f"Get available abilities failed.")
            return
        
        for i in range(0, len(self.knowledge.all_own)):
            self.available_dict[self.knowledge.all_own[i].tag] = result[i]

        shades = self.cache.own(UnitTypeId.ADEPTPHASESHIFT)

        if len(shades) == 0:
            self.adept_to_shade.clear()
            self.shade_to_adept.clear()
            self._shade_tags_handled.clear()
        else:
            adepts: Units = self.cache.own(UnitTypeId.ADEPT)
            current_shade_tags = set()

            if adepts.exists:
                for shade in shades: # type: Unit
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

