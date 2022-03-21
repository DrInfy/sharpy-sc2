from typing import Dict

from sc2.ids.ability_id import AbilityId
from sc2.ids.effect_id import EffectId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.units import Units
from sharpy.combat import MicroStep, Action, MoveType
from sc2.unit import Unit

# voidrays don't have weapons in the current api
cd_ticks = 22.4 * 0.36
# We'll use a % of the cooldown to shoot and hope that'll be enough
ticks_to_shoot = 6  # cd_ticks * 0.6


high_priority: Dict[UnitTypeId, int] = {
    # Terran
    UnitTypeId.SIEGETANK: 8,
    UnitTypeId.SIEGETANKSIEGED: 10,  # sieged tanks are much higher priority than unsieged
    UnitTypeId.WIDOWMINE: 8,
    UnitTypeId.WIDOWMINEBURROWED: 10,
    UnitTypeId.MULE: 3,
    UnitTypeId.SCV: 10,  # prioritize scv because they'll continue repairing otherwise
    UnitTypeId.GHOST: 7,
    UnitTypeId.REAPER: 4,
    UnitTypeId.MARAUDER: 4,
    UnitTypeId.MARINE: 3,
    UnitTypeId.CYCLONE: 5,
    UnitTypeId.HELLION: 2,
    UnitTypeId.HELLIONTANK: 3,
    UnitTypeId.THOR: 7,
    UnitTypeId.MEDIVAC: 6,
    UnitTypeId.VIKINGFIGHTER: 9,
    UnitTypeId.VIKINGASSAULT: 9,
    UnitTypeId.LIBERATORAG: 7,
    UnitTypeId.LIBERATOR: 7,
    UnitTypeId.RAVEN: 10,
    UnitTypeId.BATTLECRUISER: 8,
    UnitTypeId.MISSILETURRET: 8,
    UnitTypeId.BUNKER: 2,
    # Zerg
    UnitTypeId.DRONE: 4,
    UnitTypeId.ZERGLING: 3,
    UnitTypeId.BANELING: 6,
    UnitTypeId.BANELINGCOCOON: 6,
    UnitTypeId.ULTRALISK: 6,
    UnitTypeId.QUEEN: 5,
    UnitTypeId.ROACH: 6,
    UnitTypeId.RAVAGER: 8,
    UnitTypeId.RAVAGERCOCOON: 8,
    UnitTypeId.HYDRALISK: 7,
    UnitTypeId.HYDRALISKBURROWED: 7,
    UnitTypeId.LURKERMP: 9,
    UnitTypeId.LURKERMPEGG: 9,
    UnitTypeId.LURKERMPBURROWED: 9,
    UnitTypeId.INFESTOR: 10,
    UnitTypeId.BROODLORD: 10,
    UnitTypeId.BROODLORDCOCOON: 10,
    UnitTypeId.MUTALISK: 6,
    UnitTypeId.CORRUPTOR: 10,
    UnitTypeId.INFESTEDTERRAN: 1,
    UnitTypeId.LARVA: -1,
    UnitTypeId.EGG: -1,
    UnitTypeId.LOCUSTMP: -1,
    UnitTypeId.SPINECRAWLER: 2,
    UnitTypeId.SPINECRAWLERUPROOTED: 2,
    UnitTypeId.SPORECRAWLER: 7,
    UnitTypeId.SPORECRAWLERUPROOTED: 7,
    # Protoss
    UnitTypeId.SENTRY: 5,
    UnitTypeId.PROBE: 4,
    UnitTypeId.HIGHTEMPLAR: 7,
    UnitTypeId.DARKTEMPLAR: 6,
    UnitTypeId.ADEPT: 4,
    UnitTypeId.ZEALOT: 4,
    UnitTypeId.STALKER: 9,
    UnitTypeId.IMMORTAL: 8,
    UnitTypeId.COLOSSUS: 10,
    UnitTypeId.ARCHON: 6,
    UnitTypeId.SHIELDBATTERY: 1,
    UnitTypeId.PHOTONCANNON: 7,
    UnitTypeId.PYLON: 2,
    UnitTypeId.FLEETBEACON: 3,
}


class MicroVoidrays(MicroStep):
    def __init__(self):
        super().__init__()
        self.prio_dict = high_priority

    def should_retreat(self, unit: Unit) -> bool:
        if unit.shield_max + unit.health_max > 0:
            health_percentage = (unit.shield + unit.health) / (unit.shield_max + unit.health_max)
        else:
            health_percentage = 0
        if health_percentage < 0.2:  # or unit.weapon_cooldown < 0:
            # low hp or unit can't attack
            return True

        for effect in self.ai.state.effects:
            if effect.id == EffectId.RAVAGERCORROSIVEBILECP:
                if Point2.center(effect.positions).distance_to(unit) < 3:
                    return True
            if effect.id == EffectId.BLINDINGCLOUDCP:
                if Point2.center(effect.positions).distance_to(unit) < 4:
                    return True
            if effect.id == EffectId.PSISTORMPERSISTENT:
                if Point2.center(effect.positions).distance_to(unit) < 4:
                    return True
        return False

    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        return current_command

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        if self.move_type in {MoveType.PanicRetreat, MoveType.DefensiveRetreat}:
            return current_command

        if self.cd_manager.is_ready(unit.tag, AbilityId.EFFECT_VOIDRAYPRISMATICALIGNMENT):
            close_enemies = self.cache.enemy_in_range(unit.position, 7).filter(lambda u: u.is_armored)
            if close_enemies:
                return Action(None, False, AbilityId.EFFECT_VOIDRAYPRISMATICALIGNMENT)

        shoot = self.should_shoot(unit)
        if not shoot:
            if self.should_retreat(unit):
                pos = self.pather.find_weak_influence_air(unit.position, 4)
                return Action(pos, False)

        current_command = self.focus_fire(unit, current_command, None)

        # if not shoot:
        #     if self.engaged_power.air_power < 1:
        #         if unit.distance_to(current_command.target) > 2:
        #             return Action(current_command.target.position, False)
        return current_command

    def should_shoot(self, unit: Unit):
        if unit.weapon_cooldown < 0:
            tick = self.ai.state.game_loop % cd_ticks
            return tick < ticks_to_shoot
        else:
            return self.ready_to_shoot(unit)
