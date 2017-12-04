from pymegad import logger
from pymegad.ports.port import Port
import asyncio
from pymegad.mega_const import mega


class InputPort(Port):
    TYPE = "InputPort"

    @asyncio.coroutine
    def turn_on(self):

        cmd = {
            mega['port_update']: self.port,
            mega['cmd']: mega['do_default']
        }

        response = yield from self.device.send_cmd(**cmd)

        if response == mega['done']:
            logger.info(f"{self} did default action.")
        else:
            logger.warning(f"{self} can't turn on. Exception: {response}")

        yield from self.set_state(False)

    @asyncio.coroutine
    def turn_off(self):
        yield from self.set_state(False)
