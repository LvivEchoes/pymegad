#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio

from ports import InputPort
from ports import OutputPort
from const import *
from pymegad import logger
from server import MegadServer


class MegaDevice(MegadServer):
    def __init__(self, host, port, loop=None, config=None):
        super().__init__(host, port, loop, config)

        self.generate_ports()
        self.get_port_status()

    def port_state_update(self, port, status):
        port_instance = self.ports.get(port)
        if port_instance:
            port_instance.set_state(True if status.lower() == 'on' else False)

    @asyncio.coroutine
    def set_state_all(self, device, statuses):
        for id, status in enumerate(statuses.split(';')):
            portid = id
            if status:
                if 'on' in status.lower() or 'off' in status.lower():
                    if '/' in status:
                        status = status.split('/')[0]
            if portid in self.ports:
                self.port_state_update(portid, status)
        yield
    @asyncio.coroutine
    def async_fetch_all_data(self, device):
        response = yield from self.async_send_cmd(device, cmd='all')
        return response

    def get_port_status(self):

        for id, p in self.ports.items():
            logger.info('Port {} state {}'.format(p._port_id, 'ON' if p.is_on else 'OFF'))

    def generate_ports(self):
        for ip, params in self._device_list.items():
            for port, param in params.get('ports').items():
                if param.get('type') == PORT_TYPE_INPUT:
                    self.ports[port] = InputPort(port)
                elif param.get('type') == PORT_TYPE_OUTPUT:
                    self.ports[port] = OutputPort(port)


if __name__ == '__main__':

    server = MegaDevice('0.0.0.0', 16030)
    try:
        server.start()
    except KeyboardInterrupt:
        pass  # Press Ctrl+C to stop
    finally:
        server.stop()
