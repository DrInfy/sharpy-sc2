from math import floor
from typing import List

from sharpy.unit_count import UnitCount
from sc2 import Race, UnitTypeId


class CompositionGuesser:
    def __init__(self, knowledge: 'Knowledge'):
        self.knowledge = knowledge
        self.unit_values: 'UnitValue' = knowledge.unit_values
        self.left_minerals = 0
        self.left_gas = 0

    def predict_enemy_composition(self) -> List[UnitCount]:
        if self.knowledge.enemy_race == Race.Random:
            return []# let's wait until we know the actual race.

        additional_guess: List[UnitCount] = []
        # if self.knowledge.enemy_army_predicter.enemy_mined_gas < 150:
        #     # Should be only mineral units
        #     if self.knowledge.enemy_race == Race.Zerg:
        #         additional_guess.append(UnitCount(UnitTypeId.ZERGLING, self.left_minerals / 25))
        #     if self.knowledge.enemy_race == Race.Terran:
        #         additional_guess.append(UnitCount(UnitTypeId.MARINE, self.left_minerals / 50))
        #     if self.knowledge.enemy_race == Race.Protoss:
        #         additional_guess.append(UnitCount(UnitTypeId.ZEALOT, self.left_minerals / 100))
        # else:
        if self.knowledge.enemy_race == Race.Zerg:
            self.add_units(UnitTypeId.ROACH, 1, additional_guess)
            if self.knowledge.known_enemy_structures(UnitTypeId.GREATERSPIRE).exists:
                self.add_units(UnitTypeId.BROODLORD, 5, additional_guess)
                self.add_units(UnitTypeId.CORRUPTOR, 5, additional_guess)
            if self.knowledge.known_enemy_structures(UnitTypeId.SPIRE).exists:
                self.add_units(UnitTypeId.MUTALISK, 6, additional_guess)
            if self.knowledge.known_enemy_structures(UnitTypeId.HYDRALISK).exists:
                self.add_units(UnitTypeId.HYDRALISK, 10, additional_guess)
            if self.knowledge.known_enemy_structures(UnitTypeId.ROACHWARREN).exists:
                self.add_units(UnitTypeId.ROACH, 10, additional_guess)
            if self.knowledge.known_enemy_structures(UnitTypeId.SPAWNINGPOOL).exists:
                self.add_units(UnitTypeId.ZERGLING, 4, additional_guess)
                if self.knowledge.lost_units_manager.enemy_lost_type(UnitTypeId.ZERGLING) > 10:
                    self.add_units(UnitTypeId.ZERGLING, 20, additional_guess)

        elif self.knowledge.enemy_race == Race.Protoss:
            if self.knowledge.known_enemy_structures(UnitTypeId.FLEETBEACON).exists:
                self.add_units(UnitTypeId.TEMPEST, 3, additional_guess)
            elif self.knowledge.known_enemy_structures(UnitTypeId.STARGATE).exists:
                if self.history(UnitTypeId.PHOENIX) > self.history(UnitTypeId.VOIDRAY):
                    self.add_units(UnitTypeId.PHOENIX, 5, additional_guess)
                else:
                    self.add_units(UnitTypeId.VOIDRAY, 5, additional_guess)
            if self.knowledge.known_enemy_structures(UnitTypeId.DARKSHRINE).exists:
                self.add_units(UnitTypeId.DARKTEMPLAR, 4, additional_guess)
            if self.knowledge.known_enemy_structures(UnitTypeId.TEMPLARARCHIVE).exists:
                self.add_units(UnitTypeId.HIGHTEMPLAR, 4, additional_guess)
            if self.knowledge.known_enemy_structures(UnitTypeId.ROBOTICSBAY).exists:
                self.add_units(UnitTypeId.COLOSSUS, 2, additional_guess)
            if self.knowledge.known_enemy_structures(UnitTypeId.ROBOTICSFACILITY).exists:
                self.add_units(UnitTypeId.IMMORTAL, 4, additional_guess)
            if self.knowledge.known_enemy_structures(UnitTypeId.CYBERNETICSCORE).exists:
                if self.history(UnitTypeId.STALKER) > self.history(UnitTypeId.ADEPT) \
                        and self.history(UnitTypeId.STALKER) > self.history(UnitTypeId.ZEALOT):
                    self.add_units(UnitTypeId.STALKER, 8, additional_guess)
                elif self.history(UnitTypeId.ADEPT) > self.history(UnitTypeId.ZEALOT):
                    self.add_units(UnitTypeId.ADEPT, 9, additional_guess)
                elif self.history(UnitTypeId.ZEALOT):
                    self.add_units(UnitTypeId.ZEALOT, 10, additional_guess)
            if not self.knowledge.known_enemy_structures(UnitTypeId.CYBERNETICSCORE).exists \
                    and self.knowledge.known_enemy_structures(UnitTypeId.WARPGATE).exists:
                self.add_units(UnitTypeId.ZEALOT, 8, additional_guess)
            if len(additional_guess):
                self.add_units(UnitTypeId.STALKER, 1, additional_guess)

        elif self.knowledge.enemy_race == Race.Terran:
            self.add_units(UnitTypeId.MARAUDER, 1, additional_guess)
            if self.knowledge.known_enemy_structures(UnitTypeId.FUSIONCORE).exists:
                self.add_units(UnitTypeId.BATTLECRUISER, 3, additional_guess)
            if self.knowledge.known_enemy_structures(UnitTypeId.GHOSTACADEMY).exists:
                self.add_units(UnitTypeId.GHOST, 5, additional_guess)
            if self.knowledge.known_enemy_structures(UnitTypeId.STARPORTREACTOR).exists:
                self.add_units(UnitTypeId.VIKINGFIGHTER, 4, additional_guess)
            if self.knowledge.known_enemy_structures(UnitTypeId.STARPORTTECHLAB).exists:
                self.add_units(UnitTypeId.BANSHEE, 2, additional_guess)
                self.add_units(UnitTypeId.RAVEN, 2, additional_guess)
            if self.knowledge.known_enemy_structures(UnitTypeId.FACTORYTECHLAB).exists:
                self.add_units(UnitTypeId.SIEGETANK, 4, additional_guess)
            if self.knowledge.known_enemy_structures(UnitTypeId.BARRACKSTECHLAB).exists:
                self.add_units(UnitTypeId.MARAUDER, 5, additional_guess)
            if self.knowledge.known_enemy_structures(UnitTypeId.BARRACKSREACTOR).exists:
                self.add_units(UnitTypeId.MARINE, 10, additional_guess)
            if self.knowledge.known_enemy_structures(UnitTypeId.BARRACKS).amount > 2:
                self.add_units(UnitTypeId.MARINE, 10, additional_guess)


        return additional_guess

    def history(self, type_id: UnitTypeId) -> int:
        return self.knowledge.enemy_units_manager.unit_count(type_id) \
               + self.knowledge.lost_units_manager.enemy_lost_type(type_id)

    def add_units(self, type_id, count, additional_guess):
        mineral_price = self.unit_values.minerals(type_id)
        gas_price = self.unit_values.gas(type_id)
        supply = self.unit_values.supply(type_id) # TODO: use this for something

        if mineral_price > 0:
            mineral_amount = self.left_minerals / mineral_price
        else:
            mineral_amount = 100

        if gas_price > 0:
            gas_amount = self.left_gas / gas_price
        else:
            gas_amount = 100

        count = max(0, floor(min(count, mineral_amount, gas_amount)))

        self.left_minerals -= count * mineral_price
        self.left_gas -= count * gas_price

        additional_guess.append(UnitCount(type_id, count))
