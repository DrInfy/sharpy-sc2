import warnings
from sharpy.plans import Step
from sharpy.plans.acts import BuildGas


class StepBuildGas(Step):
    """With conditions, builds a new gas mining facility closest to vespene geyser with closest worker"""

    def __init__(self, to_count: int, requirement=None, skip=None, skip_until=None):
        super().__init__(requirement, BuildGas(to_count), skip, skip_until)
