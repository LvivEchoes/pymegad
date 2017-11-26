from pymegad.ports.port import Port


class OutputPort(Port):
    def set_state(self, state):
        self._state = bool(state)

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
