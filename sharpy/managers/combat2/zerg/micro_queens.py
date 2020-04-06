from sharpy.managers.combat2 import GenericMicro, Action
from sc2 import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit


class MicroQueens(GenericMicro):
    def __init__(self, knowledge):
        super().__init__(knowledge)

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        if self.cd_manager.is_ready(unit.tag, AbilityId.TRANSFUSION_TRANSFUSION):
            own_close = self.cache.own_in_range(unit.position, 7)
            for own_unit in own_close:  # type: Unit
                if own_unit.health_max - own_unit.health > 70 and not own_unit.has_buff(BuffId.TRANSFUSION):
                    return Action(own_unit, False, AbilityId.TRANSFUSION_TRANSFUSION)

        return super().unit_solve_combat(unit, current_command)
