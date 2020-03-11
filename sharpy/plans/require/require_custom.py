from .require_base import RequireBase

class RequireCustom(RequireBase):
    def __init__(self, func):
        # function
        super().__init__()
        self.func  = func

    def check(self) -> bool:
        return self.func(self.knowledge)