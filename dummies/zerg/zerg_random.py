import random

val = random.randint(0, 5)

if val == 0:
    from .lings import LadderBot
elif val == 1:
    from .macro_roach import LadderBot
elif val == 2:
    from .macro_zerg_v2 import LadderBot
elif val == 3:
    from .mutalisk import LadderBot
elif val == 4:
    from .roach_hydra import LadderBot
elif val == 5:
    from .twelve_pool import LadderBot


class RandomZergBot(LadderBot):
    pass
