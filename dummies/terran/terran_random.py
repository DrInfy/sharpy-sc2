import random

val = random.randint(0, 7)

if val == 0:
    from .battle_cruisers import LadderBot
elif val == 1:
    from .banshees import LadderBot
elif val == 2:
    from .cyclones import LadderBot
elif val == 3:
    from .marine_rush import LadderBot
elif val == 4:
    from .rusty import LadderBot
elif val == 5:
    from .two_base_tanks import LadderBot
elif val == 6:
    from .bio import LadderBot
elif val == 7:
    from .one_base_turtle import LadderBot


class RandomTerranBot(LadderBot):
    pass
