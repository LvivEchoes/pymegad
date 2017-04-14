#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import logging
import concurrent.futures
import yaml
from urllib.parse import urlsplit, parse_qsl




class MegadServer:
    def __init__(self, host, port, loop=None):

        self._device_list = {}
        self._config = {}
        self.ports = {}
        self.mega_conf_load()
        self.config_parser()
        self.generate_ports()
        self.get_port_status()
        self._loop = loop or asyncio.get_event_loop()
        self._server = asyncio.start_server(self.handle_connection, host=host, port=port)

    def generate_ports(self):
        for ip, params in self._device_list.items():
            self.ports = {SwitchPort(port) for port in params.get('ports')}

    def mega_conf_load(self):
        with open('mega.yaml') as mega_conf:
            self._mega_def = yaml.load(mega_conf)
            logging.info('Mega definition loaded: {}'.format(self._mega_def))
    def config_parser(self):
        with open('config.yaml', 'r') as cfg:
            self._config = yaml.load(cfg)
            logging.info('Config loaded: {}'.format(self._config))

        if self._config:
            switch = self._config.get('switch')
            if isinstance(switch, dict):
                platform = switch.get('platform')
                if platform == 'megad':
                    self._device_list.update({
                        switch.get('ip'): {
                            "name": switch.get('name'),
                            "ports": switch.get('ports')
                        }
                    })
            elif isinstance(switch, list):
                for device in switch:
                    platform = device.get('platform')
                    if platform == 'megad':
                        self._device_list.update({
                            device.get('ip'): {
                                "name": device.get('name'),
                                "ports": device.get('ports')
                            }
                        })
            else:
                logging.error('Config not valid. No swich section')
        else:
            logging.error('No config found.')
        logging.info('Device list: {}'.format(self._device_list))

    def start(self, and_loop=True):
        self._server = self._loop.run_until_complete(self._server)
        logging.info('Listening established on {0}'.format(self._server.sockets[0].getsockname()))
        if and_loop:
            self._loop.run_forever()

    def stop(self, and_loop=True):
        self._server.close()
        if and_loop:
            self._loop.close()

    @asyncio.coroutine
    def handle_connection(self, reader, writer):
        peername = writer.get_extra_info('peername')
        logging.info('Accepted connection from {}'.format(peername))
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
                logging.error('Conection Timeout')
                break
        logging.info('Accepted command from {}: {}'.format(peername[0], get_params))
        self.ok_answer(writer)
        yield from writer.drain()

        self.parse_cmd(peername[0], get_params)

        logging.info('Closing connection')
        writer.close()
        self.get_port_status()

    def ok_answer(self, writer):
        writer.write('HTTP/1.1 200 OK\r\n'.encode())
        writer.write('Content-Type: text/plain; set=iso-8859-1\r\n\r\n'.encode())

    def get_port_status(self):
        for p in self.ports:
            logging.info('Port {} state {}'.format(p._port_id, 'ON' if p.is_on() else 'OFF'))

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

    def parse_cmd(self, device, cmd):
        command = self.cmd_decode(cmd)
        logging.info('Device {} cmd: {}'.format(self._device_list.get(device), command))


class SwitchPort:
    def __init__(self, id):
        self._port_id = id
        self.state = False

    def is_on(self):
        return self.state

    def turn_on(self):
        self.state = True

    def turn_off(self):
        self.state = False


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    server = MegadServer('0.0.0.0', 16030)
    try:
        server.start()
    except KeyboardInterrupt:
        pass  # Press Ctrl+C to stop
    finally:
        server.stop()
