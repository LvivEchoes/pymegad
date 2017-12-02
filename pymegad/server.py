import asyncio
from typing import Union

import concurrent.futures
import asyncio.streams
from pymegad.config import Config

from pymegad.const import *
from pymegad import logger
from pymegad.mega import MegaDevice


class MegadServer:
    def __init__(self, host, port, config=None, loop=None, bound_callback=None):

        self._host = host
        self._port = port

        self._config = Config(config)
        self._callback = bound_callback
        self._connected_devices = {}
        self._devices = {}

        self._cfg_devices = self._config.devices
        self._mega_variables = self._config.mega_variables

        self._loop = loop

        for ip in self._cfg_devices:
            self._loop.create_task(self.detect_device(ip))

        self._server = None

    @property
    def devices(self):
        return self._devices

    @property
    def connected_devices(self):
        return self._connected_devices

    @asyncio.coroutine
    def start(self):

        self._server = yield from self._loop.create_task(
            asyncio.start_server(
                self.handle_incomming_connection, host=self._host, port=self._port
            )
        )

        logger.info('Listening established on {0}'.format(
            self._server.sockets[0].getsockname())
        )

    @asyncio.coroutine
    def stop(self):
        self._server.close()
        yield from self._server.wait_closed()

    @asyncio.coroutine
    def check_device(self, ip, device):
        yield from device.check_online()

        if device.is_online:
            self._connected_devices[ip] = device

    @asyncio.coroutine
    def handle_incomming_connection(self, reader, writer):
        peer_name = writer.get_extra_info('peername')

        logger.info('Accepted connection from {}'.format(peer_name))

        device = yield from self.detect_device(peer_name[0])

        recived_data = False

        while not reader.at_eof():
            try:
                response = yield from asyncio.wait_for(
                    reader.readline(), timeout=READ_TIMEOUT
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

    @asyncio.coroutine
    def detect_device(self, ip) -> Union[MegaDevice, bool]:

        device = self.connected_devices.get(ip)

        if device:
            return device

        if ip in self._cfg_devices:
            prepare_device = self._cfg_devices[ip]
            prepare_device.update({
                "loop": self._loop,
                "config": self._config,
                "callback": self._callback
            })

            mega_device = MegaDevice(**prepare_device)
            self._devices[ip] = mega_device

            yield from self.check_device(ip, mega_device)

            return self._connected_devices.get(ip)

        return False


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    server = MegadServer('0.0.0.0', 16030, loop=loop)

    try:
        loop.run_until_complete(server.start())
        loop.run_forever()
    except KeyboardInterrupt:
        pass  # Press Ctrl+C to stop
    finally:
        server.stop()
        loop.close()
