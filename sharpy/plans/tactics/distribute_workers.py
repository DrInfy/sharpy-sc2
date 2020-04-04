from typing import Optional, List

from sharpy.managers import UnitRoleManager
from sharpy.plans.acts import ActBase
from sc2.ids.buff_id import BuffId
from sc2.units import Units

from sharpy.managers.roles import UnitTask
from sc2 import UnitTypeId, Race, AbilityId
from sc2.unit import Unit

from sharpy.knowledges import Knowledge
from sharpy.general.zone import Zone

MAX_WORKERS_PER_GAS = 3
ZONE_EVACUATION_POWER_THRESHOLD = -5
BAD_ZONE_POWER_THRESHOLD = -2


class PlanDistributeWorkers(ActBase):
    """Handles idle workers and worker distribution."""

    def __init__(self, min_gas: Optional[int] = None, max_gas: Optional[int] = None):
        super().__init__()
        assert min_gas is None or isinstance(min_gas, int)
        assert max_gas is None or isinstance(max_gas, int)

        self.min_gas = min_gas
        self.max_gas = max_gas

        self.roles: UnitRoleManager = None
        self.force_work = False

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)
        self.roles = knowledge.roles

    @property
    def active_gas_buildings(self) -> Units:
        """All gas buildings that are ready."""
        # todo: filter out gas buildings that do not have a nexus nearby (it has been destroyed)?
        return self.ai.gas_buildings.ready

    @property
    def safe_non_full_gas_buildings(self) -> Units:
        """All gas buildings that are on a safe zone and could use more workers."""
        result = Units([], self.ai)

        for zone in self.knowledge.our_zones:  # type: Zone
            if zone.is_under_attack:
                continue

            filtered = filter(lambda g: g.surplus_harvesters < 0, zone.gas_buildings)
            result.extend(filtered)

        return result

    @property
    def non_full_safe_zones(self) -> List[Zone]:
        """All zones which have a non-full mineral line and are safe from enemies."""
        zones = filter(
            lambda z: z.our_townhall.surplus_harvesters < 0 and z.power_balance > BAD_ZONE_POWER_THRESHOLD
                      and not z.needs_evacuation,
            self.knowledge.our_zones_with_minerals
        )
        return list(zones)

    @property
    def safe_zones(self) -> List[Zone]:
        """All zones which have a non-full mineral line and are safe from enemies."""
        zones = filter(
            lambda z: z.power_balance > BAD_ZONE_POWER_THRESHOLD and not z.needs_evacuation,
            self.knowledge.our_zones_with_minerals
        )
        return list(zones)

    @property
    def active_gas_workers(self) -> int:
        """Number of active workers harvesting gas."""
        count: int = 0

        for building in self.active_gas_buildings:  # type: Unit
            count += building.assigned_harvesters

        return count

    @property
    def gas_workers_target(self) -> int:
        """Target count for workers harvesting gas."""
        worker_count = self.knowledge.roles.free_workers.amount
        max_workers_at_gas = self.active_gas_buildings.amount * MAX_WORKERS_PER_GAS

        estimate = round((worker_count - 8) / 2)
        if self.min_gas is not None:
            estimate = max(estimate, self.min_gas)

        if self.max_gas is not None:
            estimate = min(estimate, self.max_gas)

        return min(max_workers_at_gas, estimate)

    def get_worker_to_reassign(self) -> Optional[Unit]:
        """Returns a worker to reassign or None."""
        workers = self.ai.workers.filter(lambda w: not w.has_buff(BuffId.ORACLESTASISTRAPTARGET))

        # Idle worker
        if workers.idle.exists:
            return workers.idle.first  # use random?

        for zone in self.knowledge.expansion_zones:
            if zone.is_ours and zone.needs_evacuation:
                mineral_workers = workers \
                    .filter(lambda w: w.order_target in zone.mineral_fields.tags and not w.is_carrying_minerals)
                if mineral_workers.exists:
                    self.force_work = True
                    return mineral_workers.first

        # Surplus mineral worker
        for our_zone in self.knowledge.our_zones_with_minerals:
            townhall: Unit = our_zone.our_townhall

            if townhall.surplus_harvesters > 0:
                mineral_workers = workers \
                    .filter(lambda w: w.order_target in our_zone.mineral_fields.tags and not w.is_carrying_minerals)
                if mineral_workers.exists:
                    return mineral_workers.first

        # Surplus gas worker
        for gas in self.active_gas_buildings:  # type: Unit
            if gas.surplus_harvesters > 0:
                excess_gas_workers = workers \
                    .filter(lambda w: w.order_target == gas.tag and not w.is_carrying_vespene)
                if excess_gas_workers.exists:
                    return excess_gas_workers.first

        return None

    def get_gas_worker(self) -> Optional[Unit]:
        for gas in self.active_gas_buildings:  # type: Unit

            excess_gas_workers = self.ai.workers \
                .filter(lambda w: w.order_target == gas.tag and not w.is_carrying_vespene)
            if excess_gas_workers.exists:
                return excess_gas_workers.first

    def get_mineral_worker(self) -> Optional[Unit]:
        for our_zone in self.knowledge.our_zones_with_minerals:
            townhall: Unit = our_zone.our_townhall
            mineral_workers = self.ai.workers \
                .filter(lambda w: w.order_target in our_zone.mineral_fields.tags and not w.is_carrying_minerals)
            if mineral_workers.exists:
                return mineral_workers.closest_to(townhall)
        return None

    def get_new_work(self, worker: Unit) -> Optional[Unit]:
        """Returns new work for a worker, or None if there is nothing better to do."""
        if self.active_gas_workers < self.gas_workers_target:
            # assign to nearest non-full gas building
            if self.safe_non_full_gas_buildings.exists:
                return self.safe_non_full_gas_buildings.closest_to(worker)

        if len(self.non_full_safe_zones) > 0:
            # assign to nearest non-full townhall / mineral field
            def distance_to_zone(zone: Zone):
                return worker.distance_to(zone.center_location)

            sorted_zones = sorted(self.non_full_safe_zones, key=distance_to_zone)

            return sorted_zones[0].mineral_fields[0]

        if not worker.is_gathering or self.force_work:
            # Assign to mineral line with lowest saturation
            def mineral_saturation(zone: Zone):
                if zone.our_townhall.ideal_harvesters > 0:
                    return zone.our_townhall.assigned_harvesters / zone.our_townhall.ideal_harvesters
                else:
                    return 9000

            sorted_zones = sorted(self.safe_zones, key=mineral_saturation)

            if len(sorted_zones) > 0:
                return sorted_zones[0].mineral_fields[0]

        if self.safe_non_full_gas_buildings.exists:
            # Just go mine gas then.
            return self.safe_non_full_gas_buildings.closest_to(worker)

        # Could not find anything better to do
        return None

    def assign_to_work(self, worker: Unit, work: Unit):
        if worker.has_buff(BuffId.ORACLESTASISTRAPTARGET):
            return  # Worker is in stasis and cannot move

        self.roles.set_task(UnitTask.Gathering, worker)
        townhalls = self.ai.townhalls.ready

        if worker.is_carrying_resource and townhalls:
            closest = townhalls.closest_to(worker)
            self.do(worker(AbilityId.SMART, closest))
            self.do(worker.gather(work, queue=True))
        else:
            self.do(worker.gather(work))

    async def execute(self) -> bool:
        self.force_work = False

        for worker in self.roles.all_from_task(UnitTask.Idle).of_type(self.unit_values.worker_types):  # type: Unit
            await self.set_work(worker)

        worker = self.get_worker_to_reassign()
        if worker is None:
            gas_workers = self.active_gas_workers
            if self.max_gas is not None and gas_workers > self.max_gas:
                worker = self.get_gas_worker()
            elif self.gas_workers_target > self.active_gas_workers and self.active_gas_buildings.amount * 3 > gas_workers:
                worker = self.get_mineral_worker()

            if worker is None:
                self.print("No worker to assign.")
                return True

        await self.set_work(worker)
        return True

    async def set_work(self, worker):
        self.print(f"Worker {worker.tag} needs new work!")
        new_work = self.get_new_work(worker)
        if new_work is None:
            self.print(f"No work to assign worker {worker.tag} to.")
            return True
        self.print(f"New work found, gathering {new_work.type_id} {new_work.tag}!")
        self.assign_to_work(worker, new_work)
        return True  # Always non-blocking
