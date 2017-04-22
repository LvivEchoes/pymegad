#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from pymegad.megad.server import MegadServer

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')

LOGGER = logging.getLogger(__name__)


if __name__ == '__main__':
    server = MegadServer()
    try:
        server.start('0.0.0.0', 16030)
    except KeyboardInterrupt:
        pass  # Press Ctrl+C to stop
    finally:
        server.stop()
