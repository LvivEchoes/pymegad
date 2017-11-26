import collections

import yaml
from pymegad.const import *
from pymegad import logger


class Config:
    def __init__(self, config) -> None:
        self._device_list = {}
        self._devices = {}
        self._mega_conf_load()
        self.set_config(config)
        self._config_parser()

    @property
    def devices(self):
        return self._devices

    @property
    def device_list(self):
        return self._device_list

    def mega_def(self, key):
        return self._mega_def.get(key)

    def set_config(self, config=None):
        if config:
            self._config = config
        else:
            with open('config.yaml', 'r') as cfg:
                self._config = yaml.load(cfg)
                logger.info('Config loaded: {}'.format(self._config))

    def _mega_conf_load(self):
        with open('mega.yaml') as mega_conf:
            self._mega_def = yaml.load(mega_conf)
            logger.info('Mega definition loaded: {}'.format(self._mega_def))

    def _update_dict_items(self, old_items, new_items):

        for k, v in new_items.items():
            if isinstance(v, collections.Mapping):
                old_items[k] = self._update_dict_items(old_items.get(k, {}), v)
            else:
                old_items[k] = v
        return old_items

    def _store_device(self, **device_params):
        device_params.pop('ports', None)
        if not self._devices.get(device_params.get('ip')):
            self._devices[device_params.pop('ip')] = dict(device_params)

    def _config_parser(self):

        if self._config:

            input_ports = self._get_valid_platform(

                self._config.get('switch'),
                CONFIG_PLATFORM
            )

            output_ports = self._get_valid_platform(
                self._config.get('light'),
                CONFIG_PLATFORM
            )

            if output_ports:

                self._store_device(**output_ports[0])

                for p in output_ports[0].get('ports'):
                    output_ports[0]['ports'][p]['type'] = PORT_TYPE_OUTPUT

                self._update_dict_items(
                    self._device_list,
                    {
                        output_ports[0].get('ip'): {
                            "name": output_ports[0].get('name'),
                            "ports": output_ports[0]['ports']
                        }
                    })

            if input_ports:
                self._store_device(**input_ports[0])

                for p in input_ports[0].get('ports'):
                    input_ports[0]['ports'][p]['type'] = PORT_TYPE_INPUT

                self._update_dict_items(
                    self._device_list,

                    {
                        input_ports[0].get('ip'): {
                            "name": input_ports[0].get('name'),
                            "ports": input_ports[0]['ports']
                        }
                    }
                )

            else:
                logger.error('Config not valid. No swich section')
        else:
            logger.error('No config found.')
        logger.info('Device list: {}'.format(self._device_list))

    def _get_valid_platform(self, platform_list, platform):
        return list(filter(lambda pl: platform == pl.get('platform'), platform_list))
