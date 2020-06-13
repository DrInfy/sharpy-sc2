import warnings
from sharpy.plans import Step
from sharpy.plans.acts import BuildGas


class StepBuildGas(Step):
    """With conditions, builds a new gas mining facility closest to vespene geyser with closest worker"""

    def __init__(self, to_count: int, requirement=None, skip=None, skip_until=None):
        self.build_gas = BuildGas(to_count)
        super().__init__(requirement, self.build_gas, skip, skip_until)

    @property
    def to_count(self):
        return self.build_gas.to_count

    @to_count.setter
    def to_count(self, value):
        self.build_gas.to_count = value
