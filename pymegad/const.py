from pymegad.mega_const import mega

CONF_ON_STATE = 'ON'
CONF_OFF_STATE = 'OFF'

PORT_TYPE_INPUT = 1
PORT_TYPE_OUTPUT = 2
DEVICE_PROTOCOL = 'http'
CONFIG_PLATFORM = 'megad'


OK_RESPONSE = 'HTTP/1.1 200 OK\r\n'
CONTENT_TYPE = 'Content-Type: text/plain; set=iso-8859-1\r\n\r\n'

CONNECTION_TIMEOUT = 2
READ_TIMEOUT = 2


FETCH_ALL_AFTER_CMD = {
    mega.get('do_default'),
    mega.get('port_update'),

}
