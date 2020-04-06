from typing import Dict, Optional

from sc2 import UnitTypeId, AbilityId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from sharpy.managers.combat2 import GenericMicro, Action, MoveType, MicroStep, CombatModel

high_priority: Dict[UnitTypeId, int] = {
    # Terran
    UnitTypeId.MULE: 9,
    UnitTypeId.SCV: 9,

    UnitTypeId.SIEGETANK: 3,
    UnitTypeId.SIEGETANKSIEGED: 5,  # sieged tanks are much higher priority than unsieged
    UnitTypeId.GHOST: 10,
    UnitTypeId.REAPER: 8,
    UnitTypeId.MARAUDER: 4,
    UnitTypeId.MARINE: 8,
    UnitTypeId.CYCLONE: 4,
    UnitTypeId.HELLION: 8,
    UnitTypeId.HELLIONTANK: 3,
    UnitTypeId.THOR: 3,
    UnitTypeId.MEDIVAC: -1,
    UnitTypeId.VIKINGFIGHTER: -1,
    UnitTypeId.VIKINGASSAULT: -1,
    UnitTypeId.LIBERATORAG: -1,
    UnitTypeId.LIBERATOR: -1,
    UnitTypeId.RAVEN: -1,
    UnitTypeId.BATTLECRUISER: -1,

    UnitTypeId.MISSILETURRET: 1,
    UnitTypeId.BUNKER: 2,

    # Zerg
    UnitTypeId.DRONE: 9,
    UnitTypeId.ZERGLING: 8,
    UnitTypeId.BANELING: 10,
    UnitTypeId.ULTRALISK: 4,
    UnitTypeId.QUEEN: 6,
    UnitTypeId.ROACH: 4,
    UnitTypeId.RAVAGER: 4,
    UnitTypeId.HYDRALISK: 8,
    UnitTypeId.HYDRALISKBURROWED: 8,
    UnitTypeId.LURKERMP: 3,
    UnitTypeId.LURKERMPBURROWED: 3,
    UnitTypeId.INFESTOR: 10,
    UnitTypeId.BROODLORD: -1,
    UnitTypeId.MUTALISK: -1,
    UnitTypeId.CORRUPTOR: -1,
    UnitTypeId.INFESTEDTERRAN: 1,


    UnitTypeId.LARVA: -1,
    UnitTypeId.EGG: -1,
    UnitTypeId.LOCUSTMP: -1,

    # Protoss
    UnitTypeId.SENTRY: 9,
    UnitTypeId.PROBE: 10,
    UnitTypeId.HIGHTEMPLAR: 10,
    UnitTypeId.DARKTEMPLAR: 9,
    UnitTypeId.ADEPT: 8,
    UnitTypeId.ZEALOT: 8,
    UnitTypeId.STALKER: 4,
    UnitTypeId.IMMORTAL: 2,
    UnitTypeId.COLOSSUS: 3,
    UnitTypeId.ARCHON: 4,

    UnitTypeId.SHIELDBATTERY: 1,
    UnitTypeId.PHOTONCANNON: 1,
    UnitTypeId.PYLON: 2,
    UnitTypeId.FLEETBEACON: 3,

}


class MicroAdepts(GenericMicro):
    def __init__(self, knowledge):
        super().__init__(knowledge)
        self.prio_dict = high_priority

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        shuffler = unit.tag % 10

        target: Optional[Unit] = None
        enemy: Unit

        target = self.get_target(self.enemies_near_by, target, unit, shuffler)

        shade_tag = self.cd_manager.adept_to_shade.get(unit.tag, None)
        if shade_tag:
            shade = self.cache.by_tag(shade_tag)
            if shade:
                if target is None:
                    nearby: Units = self.knowledge.unit_cache.enemy_in_range(shade.position, 12)
                    target = self.get_target(nearby, target, shade, shuffler)

                if target is not None:
                    pos: Point2 = target.position
                    self.ai.do(shade.move(pos.towards(unit, -1)))

        if self.move_type in {MoveType.SearchAndDestroy, MoveType.Assault} and self.model == CombatModel.RoachToStalker:
            if self.cd_manager.is_ready(unit.tag, AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT):
                if target is not None:
                    return Action(target.position, False, AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT)

        return super().unit_solve_combat(unit, current_command)

    def get_target(self, nearby: Units, target: Optional[Unit], unit: Unit, shuffler: float) -> Optional[Unit]:
        best_score = 0

        for enemy in nearby:
            d = enemy.distance_to(unit)
            if d < 12 and not enemy.is_flying:
                score = d * 0.2 - self.unit_values.power(enemy)
                if enemy.is_light:
                    score += 5
                score += 0.1 * (enemy.tag % (shuffler + 2))

                if score > best_score:
                    target = enemy
                    best_score = score
        return target

    # TODO: Adepts shade on top of marines
    # TODO: Adepts put out a escape shade
    # TODO: Adepts shade to kill workers?
