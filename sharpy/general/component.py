from typing import TYPE_CHECKING, Optional

from sc2.client import Client
from sc2.position import Point3
from sc2.unit import Unit

if TYPE_CHECKING:
    from sharpy.knowledges import Knowledge, KnowledgeBot
    from sharpy.managers import *


class Component:
    """
    Common component for all sharpy objects that contains shortcuts to managers

    Attributes:
    """

    # Shortcuts to various managers
    knowledge: "Knowledge"
    ai: "KnowledgeBot"
    client: Client
    cache: "UnitCacheManager"
    unit_values: "UnitValue"
    pather: "PathingManager"
    combat: "GroupCombatManager"
    roles: "UnitRoleManager"
    zone_manager: "ZoneManager"
    cd_manager: "CooldownManager"

    def __init__(self) -> None:
        self._debug: bool = False
        self._started: bool = False
        self.parent_key: Optional[str] = None
        self._key: Optional[str] = None
        self.__cache_key: Optional[str] = None

    @property
    def key(self) -> str:
        """
        Key is used to identify this object on possible tree structures
        @return:
        """
        if not self.__cache_key:
            if not self._key:
                self._key = type(self).__name__
            if self.parent_key:
                self.__cache_key = f"{self.parent_key}/{self._key}"
            else:
                self.__cache_key = self._key
        return self.__cache_key

    @property
    def debug(self):
        return self._debug and self.knowledge.debug

    async def start(self, knowledge: "Knowledge"):
        self._started = True
        self.knowledge = knowledge
        self._debug = self.knowledge.get_boolean_setting(f"debug.{type(self).__name__}")
        self.ai = knowledge.ai
        self.cache = knowledge.unit_cache
        self.unit_values = knowledge.unit_values
        self.client = self.ai._client
        self.pather = self.knowledge.pathing_manager
        self.combat = self.knowledge.combat_manager
        self.roles = self.knowledge.roles
        self.zone_manager = self.knowledge.zone_manager
        self.cd_manager = knowledge.cooldown_manager

    def print(self, msg: str, stats: bool = True):
        self.knowledge.print(msg, type(self).__name__, stats)

    async def start_component(self, component: "Component", knowledge: "Knowledge"):
        component.parent_key = self.key
        await component.start(knowledge)

    def debug_text_on_unit(self, unit: Unit, text: str):
        pos3d: Point3 = unit.position3d
        pos3d = Point3((pos3d.x, pos3d.y, pos3d.z + 2))
        self.client.debug_text_world(text, pos3d, size=10)
