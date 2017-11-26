import asyncio
import concurrent.futures
from urllib.parse import urlsplit
from config import Config
from pymegad.const import *
from pymegad import logger
import aiohttp


class MegadServer:
    def __init__(self, host, port, loop=None, config=None):

        self._device_list = {}
        self._config = Config(config)
        self._devices = self._config.devices
        self._device_list = self._config.device_list
        self.mega_def = self._config.mega_def

        self.ports = {}

        self._loop = loop or asyncio.get_event_loop()
        self._server = asyncio.start_server(self.async_handle_connection, host=host, port=port)

    def start(self, and_loop=True):
        self._server = self._loop.run_until_complete(self._server)
        logger.info('Listening established on {0}'.format(self._server.sockets[0].getsockname()))
        if and_loop:
            self._loop.run_forever()

    def stop(self, and_loop=True):
        self._server.close()
        if and_loop:
            self._loop.close()

    @asyncio.coroutine
    def async_handle_connection(self, reader, writer):
        peername = writer.get_extra_info('peername')
        logger.info('Accepted connection from {}'.format(peername))
        get_params = False
        while not reader.at_eof():
            try:
                response = yield from asyncio.wait_for(reader.readline(), timeout=10.0)
                line = response.decode().strip()
                split_line = line.split()
                if split_line:
                    if split_line[0].lower() == 'get':
                        get_params = split_line[1]
                if not line:
                    break
            except concurrent.futures.TimeoutError:
                logger.error('Conection Timeout')
                break
        logger.info('Accepted command from {}: {}'.format(peername[0], get_params))
        self.ok_answer(writer)
        yield from writer.drain()

        yield from self.parse_cmd(peername[0], get_params)

        logger.info('Closing connection')
        writer.close()
        self.get_port_status()

    def ok_answer(self, writer):
        writer.write('HTTP/1.1 200 OK\r\n'.encode())
        writer.write('Content-Type: text/plain; set=iso-8859-1\r\n\r\n'.encode())

    def cmd_decode(self, url):
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

    @asyncio.coroutine
    def async_send_cmd(self, device, *args, **kwargs):
        cmd = '&'.join(list(args))
        cmd_value = '&'.join([f'{k}={v}' for k, v in kwargs.items()])

        compiled_cmd = f'?{cmd}{f"&{cmd_value}" if cmd else cmd_value}'
        request_url = f'{DEVICE_PROTOCOL}://{device}/{self._devices[device]["pass"]}/{compiled_cmd}'
        response = yield from aiohttp.request('GET', request_url)
        data = yield from response.read()
        return data

    @asyncio.coroutine
    def parse_cmd(self, device, cmd):
        command = self.cmd_decode(cmd)

        all_statuses = command.get(self.mega_def('all'))

        port_update = command.get(self.mega_def('port_update'))

        if all_statuses:
            self.set_state_all(device, all_statuses)

        if port_update:
            new_statuses = yield from self.async_fetch_all_data(device)
            yield from self.set_state_all(device, new_statuses)

            port_state = CONF_ON_STATE

            if command.get(self.mega_def('port_off')):
                port_state = CONF_OFF_STATE
            self.port_state_update(int(port_update), port_state)

        logger.info('Device {} cmd: {}'.format(self._device_list.get(device), command))

    def port_state_update(self, param, port_state):
        raise NotImplemented()

    def set_state_all(self, device, all_statuses):
        raise NotImplemented()

    def get_port_status(self):
        raise NotImplemented()

    def async_fetch_all_data(self):
        raise NotImplemented()
