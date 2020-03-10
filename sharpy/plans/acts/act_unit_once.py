from .act_unit import ActUnit

class ActUnitOnce(ActUnit):
    def get_unit_count(self) -> int:
        count = super().get_unit_count()
        count += self.knowledge.lost_units_manager.own_lost_type(self.unit_type)

        return count