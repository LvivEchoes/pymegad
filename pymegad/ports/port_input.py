from pymegad.ports.port import Port
import asyncio


class InputPort(Port):
    @asyncio.coroutine
    def set_state(self, state):
        self._state = bool(state)
        yield

    @asyncio.coroutine
    def set_count(self, count):
        self._count = count
        yield

    @property
    def count(self):
        return self._count

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._state

    def turn_on(self):
        self._state = True

    def turn_off(self):
        self._state = False

    def update(self):
        pass
