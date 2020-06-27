import math
from typing import Optional, Set, Dict, List, Callable

from sc2.position import Point2, Point3
from sc2.units import Units
from sharpy.managers import BuildingSolver
from sharpy.plans.acts import ActBase
from sharpy.knowledges import Knowledge
from sc2 import UnitTypeId, AbilityId
from sc2.unit import Unit

"""
Background info:
A structure that is building an addon will have .orders of the addon creation ability, the addon itself will have the proper id, e.g. UnitTypeId.BARRACKSREACTOR if it is a reactor created by barracks, the barracks.add_on_tag will be 0 while in construction

I think while landing a structure, the addon tag will be 0 even when the structure has landed already (not .is_flying)
"""

TECHLABS: Set[UnitTypeId] = {
    UnitTypeId.TECHLAB,
    UnitTypeId.BARRACKSTECHLAB,
    UnitTypeId.FACTORYTECHLAB,
    UnitTypeId.STARPORTTECHLAB,
}
REACTORS: Set[UnitTypeId] = {
    UnitTypeId.REACTOR,
    UnitTypeId.BARRACKSREACTOR,
    UnitTypeId.FACTORYREACTOR,
    UnitTypeId.STARPORTREACTOR,
}
BARRACKS: Set[UnitTypeId] = {UnitTypeId.BARRACKS, UnitTypeId.BARRACKSFLYING}
FACTORIES: Set[UnitTypeId] = {UnitTypeId.FACTORY, UnitTypeId.FACTORYFLYING}
STARPORTS: Set[UnitTypeId] = {UnitTypeId.STARPORT, UnitTypeId.STARPORTFLYING}
PRODUCTION_TYPES: List[UnitTypeId] = [UnitTypeId.STARPORT, UnitTypeId.FACTORY, UnitTypeId.BARRACKS]
ALL_PRODUCTION_TYPES: List[UnitTypeId] = [
    UnitTypeId.STARPORT,
    UnitTypeId.STARPORTFLYING,
    UnitTypeId.FACTORY,
    UnitTypeId.FACTORYFLYING,
    UnitTypeId.BARRACKS,
    UnitTypeId.BARRACKSFLYING,
]
ADDON_TYPES: List[UnitTypeId] = [UnitTypeId.REACTOR, UnitTypeId.TECHLAB]
OTHER_ADDON = {
    UnitTypeId.REACTOR: UnitTypeId.TECHLAB,
    UnitTypeId.TECHLAB: UnitTypeId.REACTOR,
}


class PlanAddonSwap(ActBase):
    """
    Plans the addon swap, reserves landing locations and addons to not be built by the GridBuilding() act.
    """

    def __init__(
        self,
        barracks_techlab_count: int = 0,
        barracks_reactor_count: int = 0,
        factory_techlab_count: int = 0,
        factory_reactor_count: int = 0,
        starport_techlab_count: int = 0,
        starport_reactor_count: int = 0,
        force_move_to_naked: bool = False,
        only_once: bool = True,
    ):
        super().__init__()

        self.completed = False
        # As soon as all structures were satisfied with addons once, do not run this plan ever again
        self.only_once = only_once

        self.desired_amount = {
            UnitTypeId.BARRACKS: {
                UnitTypeId.REACTOR: barracks_reactor_count,
                UnitTypeId.TECHLAB: barracks_techlab_count,
            },
            UnitTypeId.FACTORY: {UnitTypeId.REACTOR: factory_reactor_count, UnitTypeId.TECHLAB: factory_techlab_count},
            UnitTypeId.STARPORT: {
                UnitTypeId.REACTOR: starport_reactor_count,
                UnitTypeId.TECHLAB: starport_techlab_count,
            },
        }
        # Set to true if you want structures to always get rid of their addon (e.g. when building addons for other structures), otherwise they stay with their addon if other structure types are not in need of it
        self.force_move_to_naked = force_move_to_naked

        self.production_with_addon: Dict[UnitTypeId, Dict[Optional[UnitTypeId], Units]] = {
            UnitTypeId.BARRACKS: {UnitTypeId.REACTOR: None, UnitTypeId.TECHLAB: None, None: None},
            UnitTypeId.FACTORY: {UnitTypeId.REACTOR: None, UnitTypeId.TECHLAB: None, None: None},
            UnitTypeId.STARPORT: {UnitTypeId.REACTOR: None, UnitTypeId.TECHLAB: None, None: None},
        }
        self.free_techlab_locations: Set[Point2] = set()
        self.free_reactor_locations: Set[Point2] = set()
        self.free_addon_locations: Dict[UnitTypeId, Set[Point2]] = {
            UnitTypeId.REACTOR: self.free_reactor_locations,
            UnitTypeId.TECHLAB: self.free_techlab_locations,
        }
        self.locations_with_addon = {
            UnitTypeId.TECHLAB: set(),
            UnitTypeId.REACTOR: set(),
        }

        self.structures_at_positions: Dict[Point2:Unit] = {}

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)

    async def execute(self) -> bool:
        if self.only_once and self.completed:
            return True
        await self.update_units()
        await self.check_if_plan_is_completed()
        if self.completed:
            return True
        await self.plan_addon_swaps()
        # Block if structures are not satisfied
        return False

    async def update_units(self):
        self.locations_with_addon[UnitTypeId.TECHLAB] = {
            unit.add_on_land_position for unit in self.knowledge.unit_cache.own(TECHLABS)
        }
        self.locations_with_addon[UnitTypeId.REACTOR] = {
            unit.add_on_land_position for unit in self.knowledge.unit_cache.own(REACTORS)
        }

        barracks = self.knowledge.unit_cache.own({UnitTypeId.BARRACKS, UnitTypeId.BARRACKSFLYING})
        self.production_with_addon[UnitTypeId.BARRACKS][None] = barracks.filter(
            lambda unit: not self.has_addon(unit, UnitTypeId.TECHLAB) and not self.has_addon(unit, UnitTypeId.REACTOR)
        )
        self.production_with_addon[UnitTypeId.BARRACKS][UnitTypeId.TECHLAB] = barracks.filter(
            lambda unit: self.has_addon(unit, UnitTypeId.TECHLAB)
        )
        self.production_with_addon[UnitTypeId.BARRACKS][UnitTypeId.REACTOR] = barracks.filter(
            lambda unit: self.has_addon(unit, UnitTypeId.REACTOR)
        )

        factories = self.knowledge.unit_cache.own({UnitTypeId.FACTORY, UnitTypeId.FACTORYFLYING})
        self.production_with_addon[UnitTypeId.FACTORY][None] = factories.filter(
            lambda unit: not self.has_addon(unit, UnitTypeId.TECHLAB) and not self.has_addon(unit, UnitTypeId.REACTOR)
        )
        self.production_with_addon[UnitTypeId.FACTORY][UnitTypeId.TECHLAB] = factories.filter(
            lambda unit: self.has_addon(unit, UnitTypeId.TECHLAB)
        )
        self.production_with_addon[UnitTypeId.FACTORY][UnitTypeId.REACTOR] = factories.filter(
            lambda unit: self.has_addon(unit, UnitTypeId.REACTOR)
        )

        starports = self.knowledge.unit_cache.own({UnitTypeId.STARPORT, UnitTypeId.STARPORTFLYING})
        self.production_with_addon[UnitTypeId.STARPORT][None] = starports.filter(
            lambda unit: not self.has_addon(unit, UnitTypeId.TECHLAB) and not self.has_addon(unit, UnitTypeId.REACTOR)
        )
        self.production_with_addon[UnitTypeId.STARPORT][UnitTypeId.TECHLAB] = starports.filter(
            lambda unit: self.has_addon(unit, UnitTypeId.TECHLAB)
        )
        self.production_with_addon[UnitTypeId.STARPORT][UnitTypeId.REACTOR] = starports.filter(
            lambda unit: self.has_addon(unit, UnitTypeId.REACTOR)
        )

        all_production = self.knowledge.unit_cache.own(ALL_PRODUCTION_TYPES)
        self.structures_at_positions = {unit.position: unit for unit in all_production}

    async def check_if_plan_is_completed(self):
        """ Checks if all structures are satisfied with their addon count. """
        self.completed = True

        for production_type in PRODUCTION_TYPES:
            for addon_type in ADDON_TYPES:
                if (
                    self.production_with_addon[production_type][addon_type].amount
                    < self.desired_amount[production_type][addon_type]
                ):
                    self.completed = False
                    return

    async def plan_addon_swaps(self):
        """ Main function which first tries to move structures away from addons, then attaches them. """
        await self.mark_unused_addon_locations()
        await self.mark_structures_for_possible_dettach()
        await self.plan_attach_to_addons()

    async def mark_unused_addon_locations(self):
        self.knowledge.building_solver.free_addon_locations.clear()

        positions_with_target_of_addon_swaps: Set[Point2] = set(
            self.knowledge.building_solver.structure_target_move_location.values()
        )
        for pos in self.locations_with_addon[UnitTypeId.TECHLAB]:
            if pos not in self.structures_at_positions and pos not in positions_with_target_of_addon_swaps:
                self.free_techlab_locations.add(pos)
                self.knowledge.building_solver.free_addon_locations.add(pos)
        for pos in self.locations_with_addon[UnitTypeId.REACTOR]:
            if pos not in self.structures_at_positions and pos not in positions_with_target_of_addon_swaps:
                self.free_reactor_locations.add(pos)
                self.knowledge.building_solver.free_addon_locations.add(pos)

    async def mark_structures_for_possible_dettach(self):
        """ Marks all structures, that should no longer use their addons, as dettachable. """
        for production_type in PRODUCTION_TYPES:
            for addon_type in ADDON_TYPES:
                production_with_addon: Units = self.production_with_addon[production_type][addon_type]
                desired_amount: int = self.desired_amount[production_type][addon_type]
                surplus_count: int = max(0, production_with_addon.amount - desired_amount)
                for production in production_with_addon.idle[:surplus_count]:  # type: Unit
                    self.free_addon_locations[addon_type].add(production.position)
                    if (
                        self.force_move_to_naked
                        and production.tag not in self.knowledge.building_solver.structure_target_move_location
                    ):
                        await self.lift_away_from_addon(production)

    async def plan_attach_to_addons(self):
        """
        Forces structures to attach to free addons if there are less structures with a certain addon type than desired.
        Compared to the function above, here structures only use free addons to attach to.
        """
        for production_type in PRODUCTION_TYPES:
            for addon_type in ADDON_TYPES:
                production_with_addon: Units = self.production_with_addon[production_type][addon_type]
                target_amount: int = self.desired_amount[production_type][addon_type]
                deficit_count: int = max(0, target_amount - production_with_addon.amount)
                if deficit_count <= 0:
                    continue
                other_addon = OTHER_ADDON[addon_type]
                production_naked: Units = self.production_with_addon[production_type][None]
                production_with_other_addon: Units = self.production_with_addon[production_type][other_addon].filter(
                    lambda unit: unit.position in self.free_addon_locations[other_addon]
                )
                # Pick moving and idle structures to attach to free addons
                for production in (production_naked + production_with_other_addon).filter(
                    lambda unit: unit.is_moving
                    or unit.is_idle
                    or unit.is_using_ability(AbilityId.LIFT)
                    or unit.is_using_ability(AbilityId.LAND)
                )[
                    :deficit_count
                ]:  # type: Unit
                    land_location = await self.find_land_location_with_addon(production, addon_type)
                    if not land_location:
                        break
                    free_addon_locations: List[Point2] = self.free_addon_locations[addon_type]
                    free_addon_locations.remove(land_location)
                    await self.lift_to_target_location(production, land_location)
                    blocking_structure: Unit = self.structures_at_positions.get(land_location, None)
                    if blocking_structure:
                        await self.lift_away_from_addon(blocking_structure)

    def position_terran(self, unit: Unit) -> Optional[Point2]:
        """
        Copied and modified from grid_building.py
        Finds the closest landing location to dettach from addons.
        """
        buildings = self.ai.structures

        current_location: Optional[Point2] = None
        current_distance = math.inf

        reserved_landing_locations: Set[Point2] = set(
            self.knowledge.building_solver.structure_target_move_location.values()
        )

        for point in self.knowledge.building_solver.building_position:
            # If a structure is landing here from AddonSwap() then dont use this location
            if point in reserved_landing_locations:
                continue
                # If this location has a techlab or reactor next to it, then don't create a new structure here
            if point in self.knowledge.building_solver.free_addon_locations:
                continue
            if buildings.closer_than(1, point):
                continue
            dist = unit.distance_to(point)
            if dist < current_distance:
                current_location = point
                current_distance = dist
        return current_location

    async def lift_away_from_addon(self, unit: Unit):
        """ Plan to move structure away from addon. Find a free location to land to. """
        land_position = await self.find_land_location_with_addon(unit, addon_type=None)
        await self.lift_to_target_location(unit, land_position)

    async def lift_to_target_location(self, unit: Unit, location: Point2):
        """ Plan to move structure to target location. Reserve the location to not be used by any other structure or a GridBuilding() command. """
        self.knowledge.building_solver.structure_target_move_location[unit.tag] = location

    async def find_land_location_with_addon(self, unit: Unit, addon_type: UnitTypeId = None) -> Optional[Point2]:
        """
        Finds a suitable landing position for unit with specific addon type.
        Attempts to
            1) Return closest landing position of an addon with that addon type
            2) Return closest landing position of a idle structure with that addon type
            2) Return closest landing position of a busy structure with that addon type
        """
        if addon_type is None:
            return self.position_terran(unit)
        elif addon_type in {UnitTypeId.TECHLAB, UnitTypeId.REACTOR}:
            free_addon_locations: Set[Point2] = self.free_addon_locations[addon_type]
            # Prefer locations that have no production structure or idle structures
            locations_without_structures: List[Point2] = [
                location for location in free_addon_locations if location not in self.structures_at_positions
            ]
            if locations_without_structures:
                return unit.position.closest(locations_without_structures)

            locations_with_idle_structures: List[Point2] = [
                location
                for location in free_addon_locations
                if location in self.structures_at_positions and self.structures_at_positions[location].is_idle
            ]
            if locations_with_idle_structures:
                return unit.position.closest(locations_with_idle_structures)

            # If none above could be found, try to get an addon from a structure that is currently busy (e.g. producing a unit)
            locations_with_structures: List[Point2] = [
                location
                for location in free_addon_locations
                if location in self.structures_at_positions and not self.structures_at_positions[location].is_idle
            ]
            if locations_with_structures:
                return unit.position.closest(locations_with_structures)

    def has_addon(self, unit: Unit, addon_type: UnitTypeId):
        """ Checks if a unit (specifically: its tag) has the specific addon type or is planned to have the specific addon type. """
        assert addon_type in {UnitTypeId.TECHLAB, UnitTypeId.REACTOR}
        if unit.tag in self.knowledge.building_solver.structure_target_move_location:
            # If structure is ordered to move to a location which has a techlab, return true
            land_location = self.knowledge.building_solver.structure_target_move_location[unit.tag]
            return land_location in self.locations_with_addon[addon_type]
        elif not unit.is_flying and unit.position in self.locations_with_addon[addon_type]:
            # If structure is not ordered to move anywhere but is landed at a location with techlab, return true
            return True
        return False


class ExecuteAddonSwap(ActBase):
    """
    Executes the planned addon swap.
    Should permanently be called to finish swapping addons, if you have at least one 'PlanAddonSwap' in your build order plan.
    """

    def __init__(self):
        super().__init__()

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)

    async def execute(self) -> bool:
        if self.knowledge.building_solver.structure_target_move_location:
            alive_structures: Units = self.cache.by_tags(self.knowledge.building_solver.structure_target_move_location)
            for structure in alive_structures:
                await self.execute_order(structure)
            # Clear dead structures - TODO Perhaps move this to unit died event?
            alive_structures_tags = alive_structures.tags
            dead_structures_tags = (
                set(self.knowledge.building_solver.structure_target_move_location) - alive_structures_tags
            )
            for dead_structure_tag in dead_structures_tags:
                self.knowledge.building_solver.structure_target_move_location.pop(dead_structure_tag)
        return True

    async def execute_order(self, unit: Unit):
        assert (
            unit.tag in self.knowledge.building_solver.structure_target_move_location
        ), f"{unit.tag}\n{self.knowledge.building_solver.structure_target_move_location}"
        assert isinstance(unit, Unit), f"{unit}"

        unit_is_busy: bool = not (
            unit.is_idle
            or unit.is_moving
            or unit.is_using_ability(AbilityId.LIFT)
            or unit.is_using_ability(AbilityId.LAND)
        )
        if unit_is_busy:
            return

        land_location: Point2 = self.knowledge.building_solver.structure_target_move_location[unit.tag]

        # Structure has arrived and landed, done!
        if unit.position == land_location and not unit.is_flying and not unit.is_using_ability(AbilityId.LIFT):
            self.knowledge.building_solver.structure_target_move_location.pop(unit.tag)
        # Structure is landed but not in right position: lift
        elif unit.position != land_location and not unit.is_flying and unit.is_idle:
            self.do(unit(AbilityId.LIFT))
        # Structure is flying but not close to land location, order move command
        elif (
            unit.is_flying
            and land_location.distance_to(unit) > 2
            and (not unit.is_moving or isinstance(unit.order_target, Point2) and unit.order_target != land_location)
            and not unit.is_using_ability(AbilityId.LIFT)
        ):
            self.do(unit.move(land_location))
        # Structure is close to land location but flying, order land command
        elif unit.is_flying and land_location.distance_to(unit) < 2 and not unit.is_using_ability(AbilityId.LAND):
            # TODO If land location is blocked, attempt to find another land location instead
            self.do(unit(AbilityId.LAND, land_location))
