import os
import shutil
import time

from typing import Any
from sc2.sc2process import kill_switch

"""
Process that is automatically killed by sc2.
"""


class KillableProcess:
    def __init__(self, process: Any, tmp_dir: str = None) -> None:
        self._tmp_dir = tmp_dir
        self._process: Any = process
        super().__init__()
        kill_switch.add(self)

    def _clean(self) -> None:
        """
        Method name is required to be _clean to be compatible with python-sc2
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info("Cleaning up...")

        if self._process is not None:
            if self._process.poll() is None:
                for _ in range(3):
                    self._process.terminate()
                    time.sleep(0.5)
                    if not self._process or self._process.poll() is not None:
                        break
                else:
                    self._process.kill()
                    self._process.wait()
                    logger.error("KILLED")

        if self._tmp_dir and os.path.exists(self._tmp_dir):
            shutil.rmtree(self._tmp_dir)

        self._process = None
        self._ws = None
        logger.info("Cleanup complete")
