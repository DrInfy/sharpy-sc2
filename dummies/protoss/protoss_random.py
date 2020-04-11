import random

val = random.randint(0, 9)

if val == 0:
    from .adept_allin import LadderBot
elif val == 1:
    from .cannon_rush import LadderBot
elif val == 2:
    from .dark_templar_rush import LadderBot
elif val == 3:
    from .gate4 import LadderBot
elif val == 4:
    from .macro_stalkers import LadderBot
elif val == 5:
    from .proxy_zealot_rush import LadderBot
elif val == 6:
    from .robo import LadderBot
elif val == 7:
    from .voidray import LadderBot
elif val == 8:
    from .one_base_tempests import LadderBot
elif val == 9:
    from .disruptor import LadderBot


class RandomProtossBot(LadderBot):
    pass
