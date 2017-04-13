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
        while not reader.at_eof():
            try:
                data = yield from asyncio.wait_for(reader.readline(), timeout=10.0)
                writer.write(data)
            except concurrent.futures.TimeoutError:
                break
        writer.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    server = EchoServer('192.168.81.73', 16030)
    try:
        server.start()
    except KeyboardInterrupt:
        pass  # Press Ctrl+C to stop
    finally:
        server.stop()
