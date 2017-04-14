#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import logging
import concurrent.futures


class EchoServer(object):
    """Echo server class"""

    def __init__(self, host, port, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._server = asyncio.start_server(self.handle_connection, host=host, port=port)

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
        host = False
        get_params = False
        while not reader.at_eof():
            try:
                response = yield from asyncio.wait_for(reader.readline(), timeout=10.0)
                line = response.decode().strip()
                split_line = line.split()
                if split_line:
                    if split_line[0].lower() == 'get':
                        get_params = split_line[1]
                    elif split_line[0].lower() == 'host:':
                        host = split_line[1].split(':')[0]
                if not line:
                    break
                logging.debug('Recived data: {}'.format(line))
            except concurrent.futures.TimeoutError:
                logging.error('Conection Timeout')
                break
        logging.info('Accepted command from {}: {}'.format(host, get_params))
        writer.write(b'{"OK":1}')
        yield from writer.drain()
        logging.info('Closing connection')
        writer.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    server = EchoServer('0.0.0.0', 16030)
    try:
        server.start()
    except KeyboardInterrupt:
        pass  # Press Ctrl+C to stop
    finally:
        server.stop()
