import itertools
import random

import sc2
from sc2.ids.ability_id import AbilityId as AbilID
from sc2.ids.unit_typeid import UnitTypeId as UnitID


class RoachRush(sc2.BotAI):
    def __init__(self):
        # set of things that come from a larva
        self.from_larva = {UnitID.DRONE, UnitID.OVERLORD, UnitID.ZERGLING, UnitID.ROACH}
        # set of things that come from a drone
        self.from_drone = {UnitID.SPAWNINGPOOL, UnitID.EXTRACTOR, UnitID.ROACHWARREN}
        # buildorder
        self.buildorder = [
            UnitID.DRONE,
            UnitID.SPAWNINGPOOL,
            UnitID.DRONE,
            UnitID.DRONE,
            UnitID.EXTRACTOR,
            UnitID.DRONE,
            UnitID.OVERLORD,
            UnitID.ROACHWARREN,
            UnitID.QUEEN,
            UnitID.OVERLORD,
            "END",
        ]
        # current step of the buildorder
        self.buildorder_step = 0
        # expansion we need to clear next, changed in 'send_idle_army'
        self.army_target = None
        # generator we need to cycle through expansions, created in 'send_idle_army'
        self.clear_map = None
        # unit groups, created in 'set_unit_groups'
        self.queens = None
        self.army = None
        # flag we wave in case we want to give up
        self.surrendered: bool = False
        # expansions ordered by distance from starting location
        self.ordered_expansions = None

    async def on_step(self, iteration):
        # dont do anything if we surrendered already
        if self.surrendered:
            return
        # create selections one time for the whole frame
        # so that we dont have to filter the same units multiple times
        self.set_unit_groups()
        # things to only do in the first step
        if iteration == 0:
            await self.start_step()
        # give up if no drones are left
        if not self.workers:
            # surrender phrase for ladder manager
            await self.chat_send("(pineapple)")
            self.surrendered = True
            return
        await self.do_buildorder()
        await self.inject()
        self.fill_extractors()
        # buildorder completed, start second phase of the bot
        if self.buildorder[self.buildorder_step] == "END":
            self.build_additional_overlords()
            self.build_army()
            self.set_army_target()
            self.control_army()

    def set_unit_groups(self):
        self.queens = self.units(UnitID.QUEEN)
        self.army = self.units.filter(lambda unit: unit.type_id in {UnitID.ROACH, UnitID.ZERGLING})

    async def start_step(self):
        # send a welcome message
        await self.chat_send("(kappa)")
        # split workers
        for drone in self.workers:
            # find closest mineral patch
            closest_mineral_patch = self.mineral_field.closest_to(drone)
            self.do(drone.gather(closest_mineral_patch))
        # prepare ordered expansions, sort by distance to start location
        self.ordered_expansions = sorted(
            self.expansion_locations.keys(), key=lambda expansion: expansion.distance_to(self.start_location)
        )
        # only do on_step every nth frame, 8 is standard
        self._client.game_step = 2

    def fill_extractors(self):
        for extractor in self.gas_buildings:
            # returns negative value if not enough workers
            if extractor.surplus_harvesters < 0:
                drones_with_no_resource = self.workers.filter(
                    lambda unit: not unit.is_carrying_resource and unit.is_collecting
                )
                if drones_with_no_resource:
                    # surplus_harvesters is negative when workers are missing
                    for n in range(-extractor.surplus_harvesters):
                        # prevent crash by only taking the minimum
                        drone = drones_with_no_resource[min(n, drones_with_no_resource.amount) - 1]
                        self.do(drone.gather(extractor))
            # take out workers if we somehow have too many
            elif extractor.surplus_harvesters > 0:
                drones_in_extractor = self.workers.filter(
                    lambda unit: not unit.is_carrying_resource and unit.order_target == extractor.tag
                )
                if drones_in_extractor:
                    for n in range(extractor.surplus_harvesters):
                        # prevent crash by only taking the minimum
                        drone = drones_in_extractor[min(n, drones_in_extractor.amount) - 1]
                        closest_mineral_patch = self.mineral_field.closest_to(drone)
                        self.do(drone.gather(closest_mineral_patch))

    async def do_buildorder(self):
        # only try to build something if we have 25 minerals, otherwise we dont have enough anyway
        if self.minerals < 25:
            return
        current_step = self.buildorder[self.buildorder_step]
        # do nothing if we are done already or dont have enough resources for current step of build order
        if current_step == "END" or not self.can_afford(current_step):
            return
        # check if current step needs larva
        if current_step in self.from_larva and self.larva:
            self.do(self.larva.first.train(current_step))
        # check if current step needs drone
        elif current_step in self.from_drone:
            if current_step == UnitID.EXTRACTOR:
                # get geysers that dont have extractor on them
                geysers = self.vespene_geyser.filter(
                    lambda g: all(g.position != e.position for e in self.units(UnitID.EXTRACTOR))
                )
                # pick closest
                position = geysers.closest_to(self.start_location)
            else:
                if current_step == UnitID.ROACHWARREN:
                    # check tech requirement
                    if not self.structures(UnitID.SPAWNINGPOOL).ready:
                        return
                # pick position towards ramp to avoid building between hatchery and resources
                buildings_around = self.townhalls(UnitID.HATCHERY).first.position.towards(
                    self.main_base_ramp.depot_in_middle, 7
                )
                # look for position until we find one that is not already used
                position = None
                while not position:
                    position = await self.find_placement(building=current_step, near=buildings_around, placement_step=4)
                    if any(building.position == position for building in self.units.structure):
                        position = None
            # got building position, pick collecting worker without resources that will get there the fastest
            worker = self.workers.filter(lambda unit: not unit.is_carrying_minerals and unit.is_collecting).closest_to(
                position
            )
            self.do(worker.build(current_step, position))
        elif current_step == UnitID.QUEEN:
            # tech requirement check
            if not self.structures(UnitID.SPAWNINGPOOL).ready:
                return
            hatch = self.townhalls(UnitID.HATCHERY).first
            self.do(hatch.train(UnitID.QUEEN))
        print(f"{self.time_formatted} STEP {self.buildorder_step:2} {current_step.name}")
        self.buildorder_step += 1

    async def inject(self):
        if not self.queens:
            return
        for queen in self.queens.idle:
            abilities = await self.get_available_abilities(queen)
            # check if queen can inject
            # its also possible to use queen.energy >= 25 to save the async call
            if AbilID.EFFECT_INJECTLARVA in abilities:
                hatch = self.townhalls(UnitID.HATCHERY).first
                self.do(queen(AbilID.EFFECT_INJECTLARVA, hatch))

    def build_army(self):
        # we cant build any unit with less than 50 minerals
        if self.minerals < 50:
            return
        # rebuild lost queen
        if (
            self.structures(UnitID.SPAWNINGPOOL).ready
            and not self.queens
            and not self.already_pending(UnitID.QUEEN)
            and self.townhalls(UnitID.HATCHERY).idle
            and self.can_afford(UnitID.QUEEN)
        ):
            hatch = self.townhalls(UnitID.HATCHERY).first
            self.do(hatch.train(UnitID.QUEEN))
            return
        if self.larva and self.structures(UnitID.ROACHWARREN).ready:
            if self.can_afford(UnitID.ROACH):
                # note that this only builds one unit per step
                larva = self.larva.pop()
                self.do(larva.train(UnitID.ROACH))
                return
            # only build zergling if we cant build roach soon
            elif self.minerals >= 50 and self.vespene <= 8:
                larva = self.larva.pop()
                self.do(larva.train(UnitID.ZERGLING))
                return

        # rebuild lost workers if we have roaches
        if (
            self.larva
            and self.units(UnitID.ROACH).ready
            and self.supply_workers + self.already_pending(UnitID.DRONE) < 16
            and self.can_afford(UnitID.DRONE)
        ):
            larva = self.larva.pop()
            self.do(larva.train(UnitID.DRONE))
            return

    def set_army_target(self):
        # sets the next waypoint for the army in case there is nothing on the map
        # if we didnt start to clear the map already
        if not self.clear_map:
            # start with enemy starting location, then cycle through all expansions
            self.clear_map = itertools.cycle(reversed(self.ordered_expansions))
            self.army_target = next(self.clear_map)
        # we can see the expansion but there seems to be nothing there, get next
        if self.units.closer_than(6, self.army_target):
            self.army_target = next(self.clear_map)

    def control_army(self):
        # calculate actions for the army units
        army = self.units.filter(lambda unit: unit.type_id in {UnitID.ROACH, UnitID.ZERGLING})
        # dont do anything if we dont have an army
        if not army:
            return
        # we can only fight ground units and we dont want to fight larva or eggs
        ground_enemies = self.enemy_units.filter(
            lambda unit: not unit.is_flying and unit.type_id not in {UnitID.LARVA, UnitID.EGG}
        )
        # we dont see anything so start to clear the map
        if not ground_enemies:
            for unit in army:
                # clear found structures
                if self.enemy_structures:
                    # focus down low hp structures first
                    in_range_structures = self.enemy_structures.in_attack_range_of(unit)
                    if in_range_structures:
                        lowest_hp = min(in_range_structures, key=lambda e: (e.health + e.shield, e.tag))
                        if unit.weapon_cooldown == 0:
                            self.do(unit.attack(lowest_hp))
                        else:
                            # dont go closer than 1 with roaches to use ranged attack
                            if unit.ground_range > 1:
                                self.do(unit.move(lowest_hp.position.towards(unit, 1 + lowest_hp.radius)))
                            else:
                                self.do(unit.move(lowest_hp.position))
                    else:
                        self.do(unit.move(self.enemy_structures.closest_to(unit)))
                # check bases to find new structures
                else:
                    self.do(unit.move(self.army_target))
            return
        # create selection of dangerous enemy units.
        enemy_fighters = ground_enemies.filter(lambda u: u.can_attack) + self.enemy_structures(
            {UnitID.BUNKER, UnitID.SPINECRAWLER, UnitID.PHOTONCANNON}
        )
        for unit in army:
            if enemy_fighters:
                # select enemies in range
                in_range_enemies = enemy_fighters.in_attack_range_of(unit)
                if in_range_enemies:
                    # prioritize workers
                    workers = in_range_enemies({UnitID.DRONE, UnitID.SCV, UnitID.PROBE})
                    if workers:
                        in_range_enemies = workers
                    # special micro for ranged units
                    if unit.ground_range > 1:
                        # attack if weapon not on cooldown
                        if unit.weapon_cooldown == 0:
                            # attack enemy with lowest hp of the ones in range
                            lowest_hp = min(in_range_enemies, key=lambda e: (e.health + e.shield, e.tag))
                            self.do(unit.attack(lowest_hp))
                        else:
                            # micro away from closest unit
                            # move further away if too many enemies are near
                            friends_in_range = army.in_attack_range_of(unit)
                            closest_enemy = in_range_enemies.closest_to(unit)
                            distance = unit.ground_range + unit.radius + closest_enemy.radius
                            if (
                                len(friends_in_range) <= len(in_range_enemies)
                                and closest_enemy.ground_range <= unit.ground_range
                            ):
                                distance += 1
                            else:
                                # if more than 5 units friends are close, use distance one shorter than range
                                # to let other friendly units get close enough as well and not block each other
                                if len(army.closer_than(7, unit.position)) >= 5:
                                    distance -= -1
                            self.do(unit.move(closest_enemy.position.towards(unit, distance)))
                    else:
                        # target fire with melee units
                        lowest_hp = min(in_range_enemies, key=lambda e: (e.health + e.shield, e.tag))
                        self.do(unit.attack(lowest_hp))
                else:
                    # no unit in range, go to closest
                    self.do(unit.move(enemy_fighters.closest_to(unit)))
            # no dangerous enemy at all, attack closest anything
            else:
                self.do(unit.attack(ground_enemies.closest_to(unit)))

    def build_additional_overlords(self):
        # build more overlords after buildorder
        # we need larva and enough minerals
        # prevent overlords if we have reached the cap already
        # calculate if we need more supply
        if (
            self.can_afford(UnitID.OVERLORD)
            and self.larva
            and self.supply_cap != 200
            and self.supply_left + self.already_pending(UnitID.OVERLORD) * 8 < 2 + self.supply_used // 7
        ):
            self.do(self.larva.first.train(UnitID.OVERLORD))
