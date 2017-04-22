#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

import requests

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')

LOGGER = logging.getLogger(__name__)


class MegadInstance:
    def __init__(self):
        pass

    def send_command(self, cmd, device, password):
        cmd_encoded = '&'.join(['{}={}'.format(k, v) for k, v in cmd.items()])
        LOGGER.info('Send command to {} cmd: {}'.format(device, cmd))
        cmd_status = self.call_url(
            'http://{}:80/{}/?{}'.format(device, password, cmd_encoded))
        return cmd_status

    def call_url(self, url):
        req = requests.get(url)
        LOGGER.info('Request {} finished with status {}'.format(
            url, req.status_code)
        )
        if req.status_code == 200:
            return req.text
        else:
            LOGGER.error('Request failed: {}'.format(req.text))
            return False
