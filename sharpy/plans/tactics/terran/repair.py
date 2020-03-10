from math import ceil

from sharpy.plans.acts import ActBase
from sharpy.managers.roles import UnitTask
from sharpy.general.zone import Zone
from sc2.constants import UnitTypeId
from sc2.unit import Unit


class Repair(ActBase):
    def __init__(self):
        super().__init__()

    async def execute(self) -> bool:
        roles: 'UnitRoleManager' = self.knowledge.roles
        current_repairers = []
        for zone in self.knowledge.our_zones:
            for unit in zone.our_units:
                if self.should_repair(unit):
                    desired_count = self.solve_scv_count(zone, unit)
                    repairing_this_count = 0
                    for worker in zone.our_workers: # type: Unit
                        if not worker.orders:
                            continue
                        if worker.is_repairing:
                            current_repairers.append(worker.tag)
                            repairing_this_count += 1

                    if repairing_this_count < desired_count:
                        for worker in zone.our_workers:  # type: Unit
                            if not worker.is_repairing and not worker.tag in current_repairers:
                                self.do(worker.repair(unit))
                                current_repairers.append(worker.tag)
                                roles.set_task(UnitTask.Building, worker)
                                break
        return True

    def should_repair(self, unit: Unit) -> bool:
        if not unit.is_ready:
            return False
        if unit.health_percentage < 0.95:
            if unit.type_id == UnitTypeId.BUNKER:
                return True
            elif unit.type_id == UnitTypeId.COMMANDCENTER or unit.type_id == UnitTypeId.ORBITALCOMMAND or unit.type_id == UnitTypeId.PLANETARYFORTRESS:
                return True
        if unit.health_percentage < 0.3 and unit.is_structure:
            return True
        if unit.health_percentage < 0.75 and (unit.type_id == UnitTypeId.BATTLECRUISER or unit.type_id == UnitTypeId.SIEGETANK):
            return True
        return False

    def solve_scv_count(self, zone: Zone, unit: Unit) -> int:
        power_max = max(1, zone.known_enemy_power.power / 3)
        if unit.type_id == UnitTypeId.BUNKER:
            hp_max = 6
        elif unit.type_id == UnitTypeId.COMMANDCENTER or unit.type_id == UnitTypeId.ORBITALCOMMAND or unit.type_id == UnitTypeId.PLANETARYFORTRESS:
            hp_max = 12
        elif unit.is_structure:
            hp_max = 1
        else:
            hp_max = 2
        return ceil(min(power_max, hp_max))

