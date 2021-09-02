from sc2pathlib import MapType, Sc2Map
from sharpy.managers import ManagerBase
from sharpy.managers.core import PathingManager


class EnemyVisionManager(ManagerBase):
    map: Sc2Map
    pather: PathingManager

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.pather = knowledge.get_required_manager(PathingManager)
        self.map = self.pather.map

    async def update(self):
        self.map.clear_vision()
        for unit in self.ai.all_enemy_units:
            self.map.add_vision_params(unit.is_detector, unit.is_flying, unit.position, unit.sight_range)
        self.map.calculate_vision()

    async def post_update(self):
        if self.debug:
            self.map.plot_vision()
