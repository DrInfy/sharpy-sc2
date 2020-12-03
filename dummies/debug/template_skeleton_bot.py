from typing import Optional, List
from sharpy.knowledges import SkeletonBot


class TemplateSkeletonBot(SkeletonBot):
    def __init__(self):
        self.realtime_split = False  # No worker split on minerals
        self.realtime_worker = True  # First worker
        super().__init__("Skeleton bot")

    def configure_managers(self) -> Optional[List["ManagerBase"]]:
        return []

    async def execute(self):
        if self.knowledge.iteration == 0:
            for worker in self.workers:
                self.do(worker.attack(self.enemy_start_locations[0]))
