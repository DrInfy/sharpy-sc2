import enum


class Advantage(enum.Enum):
    Even = 0,
    SlightAdvantage = 1,
    SmallAdvantage = 2,
    ClearAdvantage = 3,
    OverwhelmingAdvantage = 4
    SlightDisadvantage = -1,
    SmallDisadvantage = -2,
    ClearDisadvantage = -3,
    OverwhelmingDisadvantage = -4


at_least_clear_advantage = {Advantage.OverwhelmingAdvantage, Advantage.ClearAdvantage}
at_least_small_advantage = {Advantage.OverwhelmingAdvantage,
                            Advantage.ClearAdvantage,
                            Advantage.SmallAdvantage}

at_least_advantage = {Advantage.OverwhelmingAdvantage,
                      Advantage.ClearAdvantage,
                      Advantage.SmallAdvantage,
                      Advantage.SlightAdvantage}

at_least_clear_disadvantage = {Advantage.OverwhelmingDisadvantage, Advantage.ClearDisadvantage}
at_least_small_disadvantage = {Advantage.OverwhelmingDisadvantage,
                               Advantage.ClearDisadvantage,
                               Advantage.SmallDisadvantage}
at_least_disadvantage = {Advantage.OverwhelmingDisadvantage,
                         Advantage.ClearDisadvantage,
                         Advantage.SmallDisadvantage,
                         Advantage.SlightDisadvantage}