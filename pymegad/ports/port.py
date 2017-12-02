import asyncio
from pymegad import mega, logger
from pymegad.helpers.translit import translation


class Port:
    TYPE = "GenericPort"

    def __init__(self, id, device, name=None, *args, **kwargs):
        self._port_id = id
        self._name = name
        self._state = None
        self._count = None
        self._brightness = None
        self._event_callback = None
        self._device: 'mega.MegaDevice' = device

    @property
    def entity_id(self):
        device_name_tr = self.device.name.translate(
            translation
        )
        port_name_tr = self.name.translate(translation)

        return f"{device_name_tr}_{self.port}_{port_name_tr}".lower().replace(' ', '_')

    @property
    def device(self):
        return self._device

    @asyncio.coroutine
    def set_state(self, state):
        self._state = bool(state)

        params = {
            "state": state,
            "count": self.count
        }

        if self.event_callback:
            yield from self.event_callback(
                instance=self,
                params=params
            )

    @property
    def event_callback(self):
        return self._event_callback

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def port(self):
        return self._port_id

    def set_count(self, count):
        self._count = count

    @property
    def count(self):
        return self._count

    @property
    def is_on(self):
        return self._state

    @asyncio.coroutine
    def update(self):
        yield from self.fetch_status()

    @asyncio.coroutine
    def fetch_status(self):
        _state = yield from self._device.fetch_port_status(self.port)
        if _state is None:
            logger.error(f"[{self._device.ip}] # Can't fetch port status.")
            self._state = False
        else:
            self._state = _state

    def __repr__(self):
        return f"{self.TYPE} {self.port}: {self._device.ip}#{self.name}"

    def __str__(self) -> str:
        return f"{self.TYPE} {self.port}: {self._device.ip}#{self.name}"
