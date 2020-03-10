from typing import List, Optional

from sharpy.constants import Constants
from sharpy.plans.acts import ActBase
from sc2 import UnitTypeId, Race
from sc2.position import Point2
from sc2.unit import Unit

# These buildings do not need to be powered by pylons.
ignored_building_types = (
    UnitTypeId.PYLON,
    UnitTypeId.NEXUS,
    UnitTypeId.ASSIMILATOR,
    UnitTypeId.ASSIMILATORRICH,
)


PYLON = UnitTypeId.PYLON


class RestorePower(ActBase):
    """Builds a pylon next to unpowered Protoss structures."""
    def __init__(self):
        super().__init__()

    async def execute(self) -> bool:
        if not self.knowledge.my_race == Race.Protoss:
            raise Exception(f"RestorePower is meant for Protoss bots, but this bot's race is: {self.knowledge.my_race}")

        # consider only one building per iteration
        unpowered_buildings = self.unpowered_buildings
        if not any(unpowered_buildings):
            return True

        building = self.unpowered_buildings[0]

        if not self.knowledge.can_afford(PYLON):
            return True

        if self.already_restoring(building):
            return True

        if not self.safe_to_restore_power(building):
            return True

        # todo: figure out which method to use for selecting worker
        worker = self.ai.select_build_worker(building.position)
        if not worker:
            return True

        pylon_placement = self.get_pylon_placement(building)
        if not pylon_placement:
            return True

        self.print(f"Placing pylon at {pylon_placement} to restore power to {building.type_id} at {building.position}")
        self.do(worker.build(PYLON, pylon_placement))

        return True

    @property
    def unpowered_buildings(self):
        """Returns all of our unpowered buildings on the map."""
        structures = self.ai.structures
        unpowered = filter(lambda s: not s.is_powered and s.build_progress == 1
                                     and s.type_id not in ignored_building_types, structures)
        return list(unpowered)

    def already_restoring(self, building: Unit) -> bool:
        """Returns true if a pylon has already been ordered or is being built to power the building."""
        pending_pylons: List[Point2] = self.pending_building_positions(PYLON)
        if not any(pending_pylons):
            return False

        return building.position.distance_to_closest(pending_pylons) < Constants.PYLON_POWERED_DISTANCE

    def safe_to_restore_power(self, building: Unit):
        """Returns true if it is safe to restore power to the building."""
        enemy_range = 15
        enemies_near = self.knowledge.unit_cache.enemy_in_range(building.position, enemy_range, False)
        return not any(enemies_near)

    def get_pylon_placement(self, building: Unit) -> Optional[Point2]:
        pylon_positions: List[Point2] = self.knowledge.building_solver.pylon_position

        closest_pylon_pos: Point2 = building.position.closest(pylon_positions)

        if closest_pylon_pos.distance_to(building.position) < Constants.PYLON_POWERED_DISTANCE:
            return closest_pylon_pos

        return None
