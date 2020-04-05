from sc2.ids.buff_id import BuffId
from sc2.ids.effect_id import EffectId
from sc2.position import Point2
from sc2.units import Units
from sharpy.managers.combat2 import MicroStep, Action, MoveType
from sc2 import AbilityId, UnitTypeId, Optional
from sc2.unit import Unit


class MicroMedivacs(MicroStep):

    def __init__(self, knowledge):
        super().__init__(knowledge)
        self.anti_armor_available = 0

    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        return current_command

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        if self.engage_ratio < 0.25 and self.can_engage_ratio < 0.25:
            return current_command

        if self.move_type in {MoveType.PanicRetreat, MoveType.DefensiveRetreat}:
            return current_command

        if unit.energy < 5:
            return self.stay_safe(unit)

        healable_targets = self.group.ground_units.filter(lambda x:
                                                    (x.health_percentage < 1 and not x.is_flying
                                                     and (x.is_biological or x.type_id == UnitTypeId.HELLIONTANK)))

        if not healable_targets:
            return self.stay_safe(unit)

        return current_command

    def stay_safe(self, unit: Unit) -> Action:
        shuffler = (unit.tag % 11) * 5 / 11 - 2.5
        shuffler2 = (unit.tag % 7) * 5 / 7 - 2.5
        focus = self.group.center + Point2((shuffler, shuffler2))
        best_position = self.pather.find_weak_influence_air(focus, 8)
        return Action(best_position, False)
