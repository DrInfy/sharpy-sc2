import enum


class Advantage(enum.IntEnum):
    OverwhelmingDisadvantage = -4
    ClearDisadvantage = -3
    SmallDisadvantage = -2
    SlightDisadvantage = -1
    Even = 0
    SlightAdvantage = 1
    SmallAdvantage = 2
    ClearAdvantage = 3
    OverwhelmingAdvantage = 4


almost_even = {Advantage.Even, Advantage.SlightAdvantage, Advantage.SlightDisadvantage}

at_least_clear_advantage = {Advantage.OverwhelmingAdvantage, Advantage.ClearAdvantage}
at_least_small_advantage = {Advantage.OverwhelmingAdvantage, Advantage.ClearAdvantage, Advantage.SmallAdvantage}

at_least_advantage = {
    Advantage.OverwhelmingAdvantage,
    Advantage.ClearAdvantage,
    Advantage.SmallAdvantage,
    Advantage.SlightAdvantage,
}

at_least_clear_disadvantage = {Advantage.OverwhelmingDisadvantage, Advantage.ClearDisadvantage}
at_least_small_disadvantage = {
    Advantage.OverwhelmingDisadvantage,
    Advantage.ClearDisadvantage,
    Advantage.SmallDisadvantage,
}
at_least_disadvantage = {
    Advantage.OverwhelmingDisadvantage,
    Advantage.ClearDisadvantage,
    Advantage.SmallDisadvantage,
    Advantage.SlightDisadvantage,
}
