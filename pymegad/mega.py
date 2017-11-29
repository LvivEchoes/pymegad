#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
from urllib.parse import urlsplit

import aiohttp

from pymegad.ports import InputPort
from pymegad.ports import OutputPort
from pymegad.const import *
from pymegad import logger
from pymegad.config import Config
from functools import singledispatch

config = Config()


class MegaDevice:
    def __init__(self, name, platform, ip, password, ports, loop=None):
        self._name = name
        self._platform = platform
        self._ip = ip
        self._password = password
        self._raw_ports = ports
        self._loop = loop
        self._ports = dict()
        self._connector = aiohttp.TCPConnector(loop=self._loop, limit=1)
        self._session = aiohttp.ClientSession(connector=self._connector)

        self.generate_ports()
        self.show_port_status()

    @property
    def name(self):
        return self._name

    @property
    def password(self):
        return self._password

    @property
    def ip(self):
        return self._ip

    @property
    def platform(self):
        return self._platform

    @property
    def ports(self):
        return self._ports

    @asyncio.coroutine
    def send_cmd(self, *args, **kwargs):
        cmd = '&'.join(list(args))
        cmd_value = '&'.join([f'{k}={v}' for k, v in kwargs.items()])

        compiled_cmd = f'?{cmd}{f"&{cmd_value}" if cmd else cmd_value}'
        request_url = f'{DEVICE_PROTOCOL}://{self.ip}/{self.password}/{compiled_cmd}'

        response = yield from self._session.request('GET', request_url)
        data = yield from response.read()

        decoded_data = data.decode()
        logger.info(f"[{self.ip}] Incomming command {decoded_data} from device: {self.name}")
        return decoded_data

    @asyncio.coroutine
    def parse_incoming_cmd(self, cmd):
        command = self.url_to_command(cmd)

        logger.info(f"[{self.ip}] Incomming command {cmd} from device: {self.name}")

        all_statuses = command.get(config.mega_variables('all'))
        updated_port = command.get(config.mega_variables('port_update'))

        if all_statuses:
            yield from self.recv_all_statuses(all_statuses)

        if updated_port:
            yield from self.recv_port_update()
        yield

    @asyncio.coroutine
    def port_state_update(self, port, status, count=None):
        port_instance = self.ports.get(port)
        if port_instance:
            yield from port_instance.set_state(True if status.lower() == 'on' else False)
            if count is not None:
                yield from port_instance.set_count(count)
        yield

    @asyncio.coroutine
    def set_port_status(self, port_status: str, port_id: int = None, switch_count: int = None):
        port_status = port_status.lower()
        if port_id is None:

            # All ports update
            for port_id, port_status in enumerate(port_status.split(';')):
                switch_count = None
                if 'on' in port_status or 'off' in port_status:
                    if '/' in port_status:
                        port_status, switch_count = port_status.split('/')

                    yield from self.set_port_status(port_status, port_id, switch_count)

        else:
            # Single port update

            port_instance = self.ports.get(port_id)

            if port_instance:

                yield from port_instance.set_state(True if port_status == 'on' else False)

                if switch_count is not None:
                    yield from port_instance.set_count(switch_count)

            else:
                logger.debug(
                    f"[{self.ip}] {self.name} # Can't set port status ({port_id} - {port_status}), cause port is not defined in main config."
                )
        yield

    @asyncio.coroutine
    def fetch_port_status(self) -> str:
        response = yield from self.send_cmd(cmd='all')
        return response

    @asyncio.coroutine
    def recv_port_update(self):

        new_statuses = yield from self.fetch_port_status()
        yield from self.set_port_status(new_statuses)

    @asyncio.coroutine
    def recv_all_statuses(self, statuses):
        yield from self.set_port_status(statuses)

    def generate_ports(self):
        for port, param in self._raw_ports.items():
            if param.get('type') == PORT_TYPE_INPUT:
                self._ports[port] = InputPort(port)
            elif param.get('type') == PORT_TYPE_OUTPUT:
                self._ports[port] = OutputPort(port)

    def show_port_status(self):
        for id, p in self.ports.items():
            logger.info(f"[{self.ip}] {self.ip} # Port {p._port_id} state {'ON' if p.is_on else 'OFF'}")

    def url_to_command(self, url):
        """Need to manual spliting, cause parse_qsl dont work with semicolons properly"""

        query_param = urlsplit(url).query
        decoded_params = {}

        if '&' in query_param:
            for param in query_param.split('&'):
                if '=' in param:
                    decoded_params.update({param.split('=')[0]: param.split('=')[1]})
                else:
                    decoded_params.update({param: ''})
        elif '=' in query_param:
            decoded_params.update({query_param.split('=')[0]: query_param.split('=')[1]})

        return decoded_params
