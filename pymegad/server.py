import asyncio
from typing import Union

import concurrent.futures

from pymegad.config import Config

from pymegad.const import *
from pymegad import logger
from pymegad.mega import MegaDevice

config = Config()


class MegadServer:
    def __init__(self, host, port, loop=None):

        self._cfg_devices = config.devices
        self._mega_variables = config.mega_variables

        self.connected_devices = {}

        self._loop = loop or asyncio.get_event_loop()
        self._server = asyncio.start_server(self.handle_incomming_connection, host=host, port=port)

    @property
    def devices(self):
        return self.connected_devices

    def start(self, and_loop=True):
        self._server = self._loop.run_until_complete(self._server)

        logger.info('Listening established on {0}'.format(self._server.sockets[0].getsockname()))

        if and_loop:
            self._loop.run_forever()

    def stop(self, and_loop=True):
        self._server.close()

        if and_loop:
            self._loop.close()

    def add_device(self, ip, device):
        self.connected_devices[ip] = device

    @asyncio.coroutine
    def handle_incomming_connection(self, reader, writer):
        peer_name = writer.get_extra_info('peername')

        logger.info('Accepted connection from {}'.format(peer_name))

        device = self.detect_device(peer_name[0])

        recived_data = False

        while not reader.at_eof():
            try:
                response = yield from asyncio.wait_for(
                    reader.readline(), timeout=10.0
                )

                line = response.decode().strip()
                split_line = line.split()

                if split_line and split_line[0].lower() == 'get':
                    recived_data = split_line[1]

                if not line:
                    break

            except concurrent.futures.TimeoutError:
                logger.error('Conection Timeout...')
                break

        if device:

            logger.info(f'[MegaD Server] [{peer_name[0]}] Accepted command from {device.name}: {recived_data}')

            yield from device.parse_incoming_cmd(recived_data)

            yield from writer.drain()

            self.answer(writer)

            device.show_port_status()

        else:
            logger.warning(f'[MegaD Server] Accepted command from unknown device {peer_name[0]}: {recived_data}')

        logger.info(f'Closing connection to {device}')

        writer.close()

    def answer(self, writer):
        writer.write(OK_RESPONSE.encode())
        writer.write(CONTENT_TYPE.encode())

    def detect_device(self, ip) -> Union[MegaDevice, bool]:
        if ip in self.connected_devices:
            return self.connected_devices[ip]

        if ip in self._cfg_devices:
            prepare_device = self._cfg_devices[ip]
            prepare_device.update({"loop": self._loop})

            self.add_device(ip, MegaDevice(**prepare_device))

            return self.connected_devices[ip]

        return False

        # def port_state_update(self, param, port_state):
        #     raise NotImplemented()
        #
        # def set_state_all(self, all_statuses, device):
        #     raise NotImplemented()
        #
        # def log_port_status(self):
        #     raise NotImplemented()
        #
        # def async_fetch_all_data(self, device):
        #     raise NotImplemented()
        #
        # def parse_statuses(self, new_statuses, device):
        #     raise NotImplemented()
        #
        # def recv_all_statuses(self, all_statuses, device):
        #     raise NotImplemented()
        #
        # def recv_port_update(self, command, port_update, device):
        #     raise NotImplemented()
        #
        # def parse_incomming_cmd(self, param, get_params):
        #     raise NotImplemented()


if __name__ == '__main__':

    server = MegadServer('0.0.0.0', 16030)
    try:
        server.start()
    except KeyboardInterrupt:
        pass  # Press Ctrl+C to stop
    finally:
        server.stop()
