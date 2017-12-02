import asyncio

from pymegad.ports.port import Port


class OutputPort(Port):
    TYPE = "OutputPort"

    def turn_on(self):
        self._state = True

    def turn_off(self):
        self._state = False
