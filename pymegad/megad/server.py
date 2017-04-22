import asyncio
import concurrent.futures
import logging
from urllib.parse import urlsplit

from pymegad import app_config
from pymegad.app_config import mega
from pymegad.megad.switch import SwitchPort

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')

LOGGER = logging.getLogger(__name__)


class MegadServer:
    def __init__(self, config=None):
        self._config = {}
        self._device_list = {}
        self.ports = {}

        self.__load_config(config)

        self.__generate_ports()
        self.get_port_status()

    def __load_config(self, config=None):
        if config:
            self._config = config
        else:
            self._config = app_config.config

        if self._config:
            switch = self._config.get('switch')
            if isinstance(switch, dict):
                platform = switch.get('platform')
                if platform == 'megad':
                    self._device_list.update({
                        switch.get('ip'): {
                            "name": switch.get('name'),
                            "ports": switch.get('ports'),
                            "password": switch.get('password')
                        }
                    })
            elif isinstance(switch, list):
                for device in switch:
                    platform = device.get('platform')
                    if platform == 'megad':
                        self._device_list.update({
                            device.get('ip'): {
                                "name": device.get('name'),
                                "ports": device.get('ports'),
                                "password": device.get('password')
                            }
                        })
            else:
                LOGGER.error('Config not valid. No swich section')
        else:
            LOGGER.error('No config found.')
        LOGGER.info('Device list: {}'.format(self._device_list))

    def __generate_ports(self):
        for ip, params in self._device_list.items():
            self.ports.update({ip: {port: SwitchPort(port, ip, params.get(
                'password', mega.CONF_DEFAULT_PASSWORD)
                                                     ) for port in
                                    params.get('ports')}})
            LOGGER.info('Device {} port {} start listening.'.format(
                ip, ', '.join(
                    [str(p) for p in params.get('ports', {}).keys()]
                )))

    @asyncio.coroutine
    def __handle_connection(self, reader, writer):
        peername = writer.get_extra_info('peername')
        LOGGER.info('Accepted connection from {}'.format(peername))
        get_params = False
        while not reader.at_eof():
            try:
                response = yield from asyncio.wait_for(reader.readline(),
                                                       timeout=10.0)
                line = response.decode().strip()
                split_line = line.split()
                if split_line:
                    if split_line[0].lower() == 'get':
                        get_params = split_line[1]
                if not line:
                    break
            except concurrent.futures.TimeoutError:
                LOGGER.error('Conection Timeout')
                break
        LOGGER.info(
            'Accepted command from {}: {}'.format(peername[0], get_params))
        self.__ok_answer(writer)
        yield from writer.drain()

        self.__parse_cmd(peername[0], get_params)

        LOGGER.info('Closing connection')
        writer.close()
        self.get_port_status()

    def __ok_answer(self, writer):
        writer.write('HTTP/1.1 200 OK\r\n'.encode())
        writer.write(
            'Content-Type: text/plain; set=iso-8859-1\r\n\r\n'.encode())

    def __cmd_decode(self, url):
        """Need to manual spliting, cause parse_qsl dont work with semicolons properly"""
        query_param = urlsplit(url).query
        decoded_params = {}
        print('QUERY RECIEVE: ', query_param)
        if '&' in query_param:
            for param in query_param.split('&'):
                if '=' in param:
                    decoded_params.update(
                        {param.split('=')[0]: param.split('=')[1]})
                else:
                    decoded_params.update({param: ''})
        elif '=' in query_param:
            decoded_params.update(
                {query_param.split('=')[0]: query_param.split('=')[1]})

        return decoded_params

    def __update_all(self, device, statuses):
        for portid, status in enumerate(statuses.split(';')):
            if status:
                if mega.CONF_ON_STATE in status.upper() or \
                        mega.CONF_OFF_STATE in status.upper():
                    if '/' in status:
                        status = status.split('/')[0]

            if self.ports.get(device):
                if portid in self.ports.get(device):
                    self.port_state_update(device, portid, status)

    def __parse_cmd(self, device, cmd):
        command = self.__cmd_decode(cmd)

        LOGGER.info(
            'Device {} cmd: {}'.format(
                self._device_list.get(device, {}).get('name'), command))

        all_statuses = command.get(mega.CMD_ALL)
        port_update = command.get(mega.CMD_PORT_UPDATE)

        if all_statuses:
            self.__update_all(device, all_statuses)
        if port_update:
            port_state = mega.CONF_ON_STATE
            if command.get(mega.CMD_PORT_OFF):
                port_state = mega.CONF_OFF_STATE
            if int(port_update) in self.ports.get(device, {}):
                self.port_state_update(device, int(port_update), port_state)
            LOGGER.info('Port {} state changed. New state: {}'.format(
                port_update, port_state
            ))

    def get_port_status(self):
        for ip, pts in self.ports.items():
            for id, p in pts.items():
                LOGGER.info('Device {} port {} state {}'.format(
                    ip, p._port_id, mega.CONF_ON_STATE if p.is_on()
                    else
                    mega.CONF_OFF_STATE))

    def port_state_update(self, device, port, status):
        port_instance = self.ports.get(device, {}).get(port)
        port_instance.update_state(True if status.upper() == mega.CONF_ON_STATE
                                   else False)

    def start(self, host, port, loop=None, and_loop=True):
        self._loop = loop or asyncio.get_event_loop()
        self._coro = asyncio.start_server(self.__handle_connection, host=host,
                                          port=port)

        self._server = self._loop.run_until_complete(self._coro)
        LOGGER.info('Listening established on {0}'.format(
            self._server.sockets[0].getsockname()))
        if and_loop:
            self._loop.run_forever()

    def stop(self, and_loop=True):
        self._server.close()
        if and_loop:
            self._loop.close()
