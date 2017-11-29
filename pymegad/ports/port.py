class Port:
    def __init__(self, id, name=None):
        self._port_id = id
        self._name = name
        self._state = None
        self._count = None
        self._brightness = None
