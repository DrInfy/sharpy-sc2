from enum import Enum
import random

from sharpy.plans.acts import ActBase


class TauntType(Enum):
    GameStart = 0,
    RushDetected = 1,
    Victory = 2,
    Defeat = 3,
    # Concede = 4,
    RealTime = 5

taunt_conditions = {
    TauntType.GameStart: lambda k: k.ai.time > 20,

    TauntType.RushDetected: lambda k: k.possible_rush_detected,

    TauntType.Victory: lambda k: k.game_analyzer.predicting_victory,

    TauntType.Defeat: lambda k: k.game_analyzer.predicting_defeat,

    # TauntType.Concede: lambda k: k.game_analyzer.bean_predicting_defeat_for > 7,

    TauntType.RealTime: lambda k: k.ai.realtime and k.ai.time > 6,
}

taunts = {
    TauntType.GameStart: [
        # "This edge was sharpened just for you",
        # "WARNING: SHARP EDGE/POINT HAZARD - This toy contains a functional sharp edge/point. Not for children under 4 years.",
        "WARNING: SHARP EDGE/POINT HAZARD",
        "This toy contains a functional sharp edge/point. Not for children under 4 years.",
        # "Caution, this bot has sharp edges",
        "Touching can cause serious injury",
    ],

    TauntType.RushDetected: [
        "Do you need a knife for that cheese?",
        "Don't you run with scissors"
        ],

    TauntType.Victory: [
        # "Don’t jump, you have so much potential!",
        "Custom sharpening is endorsed and recommended.",
        # "Just sharpening a knife without a whetstone.",
        # "How about sharpening your competitive edge?",
        "Sharp edges have consequences.",
        # "We learn what doesn't kill us makes us stronger.",
        ],

    TauntType.Defeat: [
        "Edging flowerbeds like a pro, eh?",
        # "I've started blunting knives to help myself relax. Really takes the edge off.",
        # "Was that a never need sharpening knife?",
        # "How to Succeed at Knife-Sharpening Without Losing a Thumb?",
        "Seems like dishwashers really do blunt knives.",
        "What did a pencil say to another pencil? You're looking sharp!",
        # "Should've played safer from the start"
        ],

    TauntType.RealTime: [
        "Real time detected, disabling debug messages.",
        "Space time irregularity detected, debugging can no longer function."
        ],

    # TauntType.Concede: ["pineapple"]
}


class TauntEnemy(ActBase):

    def __init__(self):
        super().__init__()

    async def execute(self) -> bool:
        if not self.knowledge.is_chat_allowed:
            return True
        for taunt_type in TauntType:
            if taunt_conditions.get(taunt_type)(self.knowledge):
                taunt_list = taunts.get(taunt_type)
                await self.knowledge.chat_manager.chat_taunt_once(str(taunt_type), lambda: random.choice(taunt_list))

        return True
