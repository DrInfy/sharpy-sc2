from typing import Optional, TYPE_CHECKING, Dict, Union, List

from sc2.dicts.unit_train_build_abilities import TRAIN_INFO
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit_command import UnitCommand
from sharpy.managers.core.manager_base import ManagerBase
from sc2.unit import Unit

if TYPE_CHECKING:
    from sharpy.knowledges import Knowledge


class ActionIssued:
    """
    Individual action that is assigned to a unit. Used for preventing duplicate build orders.
    """

    def __init__(self, knowledge: "Knowledge", action: UnitCommand) -> None:
        self.knowledge = knowledge

        if knowledge.ai.realtime:
            # 11th frame or 3rd iteration after casting is ok to remove the reference to prevent duplicates
            self.frame_delay = 12
            self.iteration_delay = 2
        else:
            # 2nd frame or 2nd iteration after casting is ok to remove the reference to prevent duplicates
            self.frame_delay = 1
            self.iteration_delay = 1

        self.frame: int = knowledge.ai.state.game_loop
        self.iteration: int = knowledge.iteration
        self.tag: int = action.unit.tag
        self.type_id = action.unit.type_id
        self.ability_id = action.ability
        self.target = action.target

    @property
    def is_old(self):
        if (
            self.iteration + self.iteration_delay < self.knowledge.iteration
            or self.frame + self.frame_delay < self.knowledge.ai.state.game_loop
        ):
            return True
        return False


class ActionManager(ManagerBase):
    """
    Handles and allows preventing duplicate actions especially when using real time.
    """

    def __init__(self):
        self.blocks_target_self = {
            AbilityId.EFFECT_STIM_MARINE,
            AbilityId.EFFECT_STIM_MARAUDER,
            AbilityId.GUARDIANSHIELD_GUARDIANSHIELD,
            AbilityId.HALLUCINATION_ADEPT,
            AbilityId.HALLUCINATION_ARCHON,
            AbilityId.HALLUCINATION_COLOSSUS,
            AbilityId.HALLUCINATION_DISRUPTOR,
            AbilityId.HALLUCINATION_HIGHTEMPLAR,
            AbilityId.HALLUCINATION_IMMORTAL,
            AbilityId.HALLUCINATION_ORACLE,
            AbilityId.HALLUCINATION_PHOENIX,
            AbilityId.HALLUCINATION_PROBE,
            AbilityId.HALLUCINATION_STALKER,
            AbilityId.HALLUCINATION_VOIDRAY,
            AbilityId.HALLUCINATION_WARPPRISM,
            AbilityId.HALLUCINATION_ZEALOT,
            AbilityId.SPAWNCHANGELING_SPAWNCHANGELING,
        }

        for train_dict in TRAIN_INFO.values():
            for unittype_dict in train_dict.values():
                for key, value in unittype_dict.items():
                    if key == "ability" and isinstance(value, AbilityId):
                        self.blocks_target_self.add(value)

        self.blocks_targets = {
            # Nexus
            AbilityId.EFFECT_CHRONOBOOSTENERGYCOST,
            AbilityId.BATTERYOVERCHARGE_BATTERYOVERCHARGE,
            AbilityId.EFFECT_MASSRECALL_NEXUS,
            # Orbital command
            AbilityId.SCANNERSWEEP_SCAN,
            AbilityId.CALLDOWNMULE_CALLDOWNMULE,
            # Queen
            AbilityId.BUILD_CREEPTUMOR,
            AbilityId.BUILD_CREEPTUMOR_QUEEN,
            AbilityId.EFFECT_INJECTLARVA,
            AbilityId.TRANSFUSION_TRANSFUSION,
            # OVERSEER
            AbilityId.CONTAMINATE_CONTAMINATE,
            # Raven
            AbilityId.BUILDAUTOTURRET_AUTOTURRET,
            AbilityId.EFFECT_ANTIARMORMISSILE,
            AbilityId.EFFECT_INTERFERENCEMATRIX,
            # Ghost
            AbilityId.EFFECT_GHOSTSNIPE,
            AbilityId.EMP_EMP,
            # High Templar
            AbilityId.FEEDBACK_FEEDBACK,
            AbilityId.PSISTORM_PSISTORM,
            # Viper
            AbilityId.VIPERCONSUMESTRUCTURE_VIPERCONSUME,
            AbilityId.PARASITICBOMB_PARASITICBOMB,
            AbilityId.BLINDINGCLOUD_BLINDINGCLOUD,
            # Infestor
            AbilityId.AMORPHOUSARMORCLOUD_AMORPHOUSARMORCLOUD,
            AbilityId.INFESTEDTERRANS_INFESTEDTERRANS,
            AbilityId.FUNGALGROWTH_FUNGALGROWTH,
            AbilityId.NEURALPARASITE_NEURALPARASITE,
            # Mothership
            AbilityId.EFFECT_MASSRECALL_STRATEGICRECALL,
            AbilityId.EFFECT_TIMEWARP,
            # Oracle
            AbilityId.ORACLEREVELATION_ORACLEREVELATION,
            AbilityId.BEHAVIOR_PULSARBEAMON,
            AbilityId.BUILD_STASISTRAP,
            # Sentry
            AbilityId.FORCEFIELD_FORCEFIELD,
            # Rest of sentry abilities have not target
        }
        self.actions: List[ActionIssued] = []
        self.block_list: Dict[int, List[ActionIssued]] = dict()

        self.ability_duplicate_distances: Dict[AbilityId, float] = {
            AbilityId.SCANNERSWEEP_SCAN: 5,
            AbilityId.PSISTORM_PSISTORM: 3,
            AbilityId.EMP_EMP: 3,
            AbilityId.FORCEFIELD_FORCEFIELD: 1.5,
            AbilityId.FUNGALGROWTH_FUNGALGROWTH: 3,
            AbilityId.AMORPHOUSARMORCLOUD_AMORPHOUSARMORCLOUD: 3,
            AbilityId.EFFECT_TIMEWARP: 2,
        }
        super().__init__()

    async def update(self):
        self.block_list.clear()

        # Loop in reverse order in order to remove old actions properly
        for i in range(0, len(self.actions))[::-1]:
            action = self.actions[i]
            # TODO: check if the unit in question has received the specified action.
            if action.is_old:
                self.actions.pop(i)
            else:
                action_list = self.block_list.get(action.tag, None)
                if action_list is None:
                    action_list = []
                    self.block_list[action.tag] = action_list
                action_list.append(action)

    def attempt_action(self, action: UnitCommand) -> bool:
        unit = action.unit
        target = action.target
        if self.allow_action(unit, action.ability, target):
            self.action_made(action)
            return True
        return False

    def action_made(self, action: UnitCommand):
        issued_action = ActionIssued(self.knowledge, action)
        self.actions.append(issued_action)
        action_list = self.block_list.get(action.unit.tag, None)
        if action_list is None:
            action_list = []
            self.block_list[action.unit.tag] = action_list
        action_list.append(issued_action)

    def allow_action(self, unit: Unit, ability_id: AbilityId, target: Optional[Union[Unit, Point2]]) -> bool:
        """
        Should the action be allowed to pass duplicate action check?

        @return: True if the action is allowed
        """
        # if not self.ai.realtime and self.ai.client.game_step > 1:
        #     # Save some cycles, duplicate action protection is not required in step mode with step size 2 or more
        #     return True

        if target is None:
            # Ability targets nothing, or the unit itself
            # Stim pack and train units for example
            if ability_id not in self.blocks_target_self:
                return True
            action_list = self.block_list.get(unit.tag, None)
            if action_list:
                for action_issued in action_list:  # type: ActionIssued
                    if action_issued.ability_id == ability_id:
                        # Command was already issued!
                        return False
        else:
            # Ability targets either ground or another unit.
            # Ability is only duplicate if it gets casted on the same location
            if ability_id not in self.blocks_targets:
                return True

            action_list = self.block_list.get(unit.tag, None)
            if action_list:
                for action_issued in action_list:  # type: ActionIssued
                    if action_issued.ability_id == ability_id:
                        # Command was already issued

                        if isinstance(action_issued.target, Unit) and isinstance(target, Unit):
                            # both targets units
                            if action_issued.target.tag == target.tag:
                                return False

                        if isinstance(action_issued.target, Point2) and isinstance(target, Point2):
                            # both targets units
                            distance = self.ability_duplicate_distances.get(ability_id, 1)  # Use 1 as default distance
                            if action_issued.target.distance_to_point2(target.position) < distance:
                                # Casts are close enough to be considered duplicates
                                return False
        return True

    async def post_update(self):
        pass
