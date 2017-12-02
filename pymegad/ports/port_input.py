from pymegad import logger
from pymegad.ports.port import Port
import asyncio
from pymegad.mega_const import mega


class InputPort(Port):
    TYPE = "InputPort"

    @asyncio.coroutine
    def turn_on(self):

        response = yield from self.device.send_cmd(
            pt=self.port,
            cmd='d'
        )

        if response == mega['done']:
            logger.info(f"{self} did default action.")
        else:
            logger.warning(f"{self} can't turn on. Exception: {response}")

        self._state = False

    def turn_off(self):
        self._state = False
