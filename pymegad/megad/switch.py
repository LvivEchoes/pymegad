from pymegad.app_config import mega
from pymegad.megad import megad


class SwitchPort(megad.MegadInstance):
    def __init__(self, id, device, password):
        self._port_id = id
        self.state = False
        self.device = device
        self.password = password

    def set_state(self, state):
        cmd = mega.CMD_ON_STATE if state else mega.CMD_OFF_STATE
        self.__send_cmd(self.__make_cmd(cmd))
        self.state = bool(state)

    def toggle_state(self):
        cmd = mega.CMD_OFF_STATE if self.state else mega.CMD_ON_STATE
        self.__send_cmd(self.__make_cmd(cmd))
        self.state = not bool(self.state)

    def update_state(self, state):
        self.state = bool(state)

    def is_on(self):
        return self.state

    def turn_on(self):
        self.set_state(mega.CONF_ON_STATE)

    def turn_off(self):
        self.set_state(mega.CONF_OFF_STATE)

    def __send_cmd(self, cmd):
        self.send_command(cmd, self.device, self.password)

    def __make_cmd(self, cmd):
        return {'cmd': '{}:{}'.format(self._port_id, cmd)}
