import signal

from sc2.controller import Controller
from sc2.sc2process import SC2Process, kill_switch


class SC2OnlyProcess(SC2Process):
    async def __aenter__(self):
        async def __aenter__(self):
            kill_switch.add(self)

            def signal_handler(*args):
                # unused arguments: signal handling library expects all signal
                # callback handlers to accept two positional arguments
                kill_switch.kill_all()

            signal.signal(signal.SIGINT, signal_handler)

            try:
                self._process = self._launch()
                self._ws = None
                self._ws = await self._connect()
            except:
                await self._close_connection()
                self._clean()
                raise

            return Controller(self._ws, self)
