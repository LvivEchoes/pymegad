import collections
from collections import OrderedDict

import yaml

from pymegad.const import *
from pymegad import logger
from pymegad.mega_const import mega


class Config:
    def __init__(self, config=None) -> None:
        self._devices = {}

        self.mega_conf_load()
        self.set_config(config)
        self.set_device()
        self.config_parser()

    @property
    def devices(self):
        return self._devices

    def mega_variables(self, key):
        return self._mega_def.get(key)

    def set_config(self, config=None):
        if config:
            if config.__class__.__name__ == 'NodeListClass':
                config = {CONFIG_PLATFORM: config}
            self._config = config
        else:
            with open('config.yaml', 'r') as cfg:
                self._config = yaml.load(cfg)
                logger.info('Config loaded: {}'.format(self._config))

    def mega_conf_load(self):
        self._mega_def = mega
        logger.info('Mega definition loaded: {}'.format(self._mega_def))

    def _update_dict_items(self, old_items, new_items):

        for k, v in new_items.items():
            if isinstance(v, collections.Mapping):
                old_items[k] = self._update_dict_items(old_items.get(k, {}), v)
            else:
                old_items[k] = v
        return old_items

    def set_device(self):
        megad_devices = self._config.get(CONFIG_PLATFORM)
        if megad_devices:
            for device in megad_devices:
                if not self._devices.get(device.get('ip')):
                    self._devices[device.get('ip')] = device

    def _find_device_by_id(self, id):
        return list(
            filter(
                bool, map(lambda k: k[0] if k[1].get('id') == id else None, self.devices.items())
            )
        )[0]

    def config_parser(self):

        if self._config:

            input_ports = self._get_valid_platform(

                self._config.get('switch'),
                CONFIG_PLATFORM
            )

            output_ports = self._get_valid_platform(
                self._config.get('light'),
                CONFIG_PLATFORM
            )

            for device in input_ports:
                self._devices[self._find_device_by_id(list(device.keys())[0])]['switch'] = list(device.values())[0]

            for device in output_ports:
                self._devices[self._find_device_by_id(list(device.keys())[0])]['light'] = list(device.values())[0]

                # if output_ports:
                #     for device in output_ports:
                #
                #         for p, params in list(device.values())[0].items():
                #             output_ports[0]['ports'][p]['type'] = PORT_TYPE_OUTPUT
                #
                #         self._update_dict_items(
                #             self._devices,
                #             {
                #                 output_ports[0].get('ip'): {
                #                     "name": output_ports[0].get('name'),
                #                     "ports": output_ports[0]['ports']
                #                 }
                #             })
                #
                # if input_ports:
                #     for device in input_ports:
                #
                #         for p in device:
                #             input_ports[0]['ports'][p]['type'] = PORT_TYPE_INPUT
                #
                #         self._update_dict_items(
                #             self._devices,
                #
                #             {
                #                 input_ports[0].get('ip'): {
                #                     "name": input_ports[0].get('name'),
                #                     "ports": input_ports[0]['ports']
                #                 }
                #             }
                #         )


        else:
            logger.error('No config found.')

        logger.info('Device list: {}'.format(self._devices))

    def _get_valid_platform(self, platform_list, platform):
        return list(
            filter(bool, map(lambda pl: pl.get('devices') if platform == pl.get('platform') else None, platform_list)))
