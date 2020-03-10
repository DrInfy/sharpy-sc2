from typing import List

from sharpy.events import UnitDestroyedEvent
from sc2 import UnitTypeId, AbilityId
from sc2.unit import Unit

from sharpy.managers.roles import UnitTask
from .act_base import ActBase


class ActArchon(ActBase):
    def __init__(self, allowed_types: List[UnitTypeId]):
        assert allowed_types is not None and isinstance(allowed_types, List)
        self.allowed_types: List[UnitTypeId] = allowed_types
        # TODO: IF one the templars dies, this list will continue to ignore the unit!
        self.already_merging_tags: List[int] = []
        super().__init__()

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        knowledge.register_on_unit_destroyed_listener(self.on_unit_destroyed)

    async def execute(self) -> bool:
        templars = self.cache.own(self.allowed_types).ready
        for ht in templars:  # type: Unit
            if ht.is_idle and ht.tag in self.already_merging_tags:
                self.knowledge.roles.clear_task(ht)
                self.already_merging_tags.remove(ht.tag)

        templars = templars.tags_not_in(self.already_merging_tags)

        if templars.amount > 1:
            unit: Unit = templars[0]
            self.already_merging_tags.append(unit.tag)

            target: Unit = templars.tags_not_in(self.already_merging_tags).closest_to(unit)

            # Reserve upcoming archon so that they aren't stolen by other states.
            self.knowledge.roles.set_task(UnitTask.Reserved, unit)
            self.knowledge.roles.set_task(UnitTask.Reserved, target)
            self.knowledge.print(f"[ARCHON] merging {str(unit.type_id)} and {str(unit.type_id)}")

            from s2clientprotocol import raw_pb2 as raw_pb
            from s2clientprotocol import sc2api_pb2 as sc_pb
            command = raw_pb.ActionRawUnitCommand(
                ability_id=AbilityId.MORPH_ARCHON.value,
                unit_tags=[unit.tag, target.tag],
                queue_command=False
            )
            action = raw_pb.ActionRaw(unit_command=command)
            await self.ai._client._execute(action=sc_pb.RequestAction(
                actions=[sc_pb.Action(action_raw=action)]
            ))

        return True

    def on_unit_destroyed(self, event: UnitDestroyedEvent):
        if event.unit_tag in self.already_merging_tags:
            self.already_merging_tags.remove(event.unit_tag)
