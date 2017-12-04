#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
from functools import partial
from urllib.parse import urlsplit

import aiohttp

from pymegad.ports import InputPort
from pymegad.ports import OutputPort
from pymegad.const import *
from pymegad import logger


class MegaDevice:
    def __init__(self, name, ip, password, id, controller, switch, light, config, loop=None, callback=None):

        self._config = config
        self._callback = callback
        self._name = name
        self._ip = ip
        self._password = password
        self._loop = loop
        self._raw_switch = switch
        self._raw_light = light
        self._light = dict()
        self._switch = dict()
        self._controller = controller
        self._id = id
        self._connector = aiohttp.TCPConnector(loop=self._loop, limit=1)
        self._session = aiohttp.ClientSession(
            connector=self._connector,
            conn_timeout=CONNECTION_TIMEOUT,
            read_timeout=READ_TIMEOUT
        )
        self._online = False
        self.generate_ports()
        self.show_port_status()

    @property
    def raw_switch(self):
        return self._raw_switch

    @property
    def switch(self):
        return self._switch

    @property
    def raw_light(self):
        return self._raw_light

    @property
    def light(self):
        return self._light

    @property
    def id(self):
        return self._id

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
    def ports(self):
        return {**self._light, **self._switch}

    @property
    def is_online(self):
        return self._online

    @asyncio.coroutine
    def check_online(self):
        status = yield from self.process_port_update()
        self._online = bool(status)
        return self._online

    @asyncio.coroutine
    def send_cmd(self, *args, **kwargs):
        cmd = '&'.join(list(args))
        cmd_value = '&'.join([f'{k}={v}' for k, v in kwargs.items()])

        compiled_cmd = f'?{cmd}{f"&{cmd_value}" if cmd else cmd_value}'
        request_url = f'{DEVICE_PROTOCOL}://{self.ip}/{self.password}/{compiled_cmd}'

        try:
            response = yield from self._session.request('GET', request_url)
            data = yield from response.read()

        except aiohttp.ServerTimeoutError as e:
            logger.error(f"[{self.ip}] {e}")
            return None

        decoded_data = data.decode()

        if FETCH_ALL_AFTER_CMD.intersection(kwargs):
            yield from self.process_port_update()


        logger.info(f"[{self.ip}] Incomming command {decoded_data} from device: {self.name}")
        return decoded_data

    @asyncio.coroutine
    def parse_incoming_cmd(self, cmd):
        command = self.url_to_command(cmd)

        logger.info(f"[{self.ip}] Incomming command {cmd} from device: {self.name}")

        all_statuses = command.get(self._config.mega_variables('all'))
        updated_port = command.get(self._config.mega_variables('port_update'))

        if all_statuses:
            yield from self.recv_all_statuses(all_statuses)

        if updated_port:
            yield from self.process_port_update()
        yield

    def parse_state(self, port_status):
        switch_count = None
        if 'on' in port_status or 'off' in port_status:
            if '/' in port_status:
                port_status, switch_count = port_status.split('/')

        return {'port_status': port_status, 'switch_count': switch_count}

    @asyncio.coroutine
    def set_port_status(self, port_status: str, port_id: int = None, switch_count: int = None):
        port_status = port_status.lower()
        if port_id is None:

            # All ports update
            for port_id, port_status in enumerate(port_status.split(';')):

                state = self.parse_state(port_status)
                if state is not None:
                    yield from self.set_port_status(port_id=port_id, **state)

        else:
            # Single port update

            port_instance = self.ports.get(port_id)

            if port_instance:
                status = True if port_status == 'on' else False

                if port_instance.state == status:
                    return

                yield from port_instance.set_state(status)

                if switch_count is not None:
                    port_instance.set_count(switch_count)

                if self._callback:
                    params = {
                        "state": status,
                        "count": switch_count
                    }
                    self._callback(
                        instance=port_instance,
                        params=params
                    )

            else:
                logger.debug(
                    f"[{self.ip}] {self.name} # Can't set port status ({port_id} - {port_status}), cause port is not defined in main config."
                )
        yield

    @asyncio.coroutine
    def fetch_port_status(self, port=None) -> str:
        response = yield from self.send_cmd(cmd='all')

        if response is None:
            return None

        if port is not None:
            try:
                port_status = response.split(';')[port]
                return self.parse_state(port_status)
            except IndexError:
                logger.warning(f"{self.ip}] {self.name} # Can't fetch unknown port {port}.")

        return response

    @asyncio.coroutine
    def process_port_update(self):

        new_statuses = yield from self.fetch_port_status()
        if new_statuses is None:
            logger.error(f"{self.ip}] {self.name} # Can't fetch other port status.")
            return None
        yield from self.set_port_status(new_statuses)

    @asyncio.coroutine
    def recv_all_statuses(self, statuses):
        yield from self.set_port_status(statuses)

    def generate_ports(self):

        for port, params in self._raw_switch.items():
            input_port = InputPort(port, device=self, **params)
            self._switch[port] = input_port

        for port, params in self._raw_light.items():
            output_port = OutputPort(port, device=self, **params)
            self._light[port] = output_port

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
