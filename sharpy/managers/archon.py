from typing import Set

from sharpy.managers import ManagerBase


class ArchonManager(ManagerBase):
    def __init__(self) -> None:
        """
        Archon manager allows the player to tak control of selected units.
        Units that have been controlled by player are released on idle
        """
        super().__init__()
        self.controlled_tags: Set[int] = set()

    async def update(self):
        pass  # Do nothing

    async def post_update(self):
        for unit in self.knowledge.all_own:
            if unit.is_selected:
                if unit.tag not in self.controlled_tags:
                    self.controlled_tags.add(unit.tag)
            elif unit.tag in self.controlled_tags:
                # if unit.is_idle or unit.is_collecting or unit.is_structure:
                self.controlled_tags.remove(unit.tag)

        if self.ai.actions:
            for i in range(0, len(self.ai.actions))[::-1]:
                action = self.ai.actions[i]
                if action.unit.tag in self.controlled_tags:
                    self.print(f"Deleting action {action.ability} from {action.unit.type_id}")
                    del self.ai.actions[i]
