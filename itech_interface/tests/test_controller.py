from itech_interface.controller import PowerSupplyController
from itech_interface.network import ITechConnection

class DummyConn:
    def __init__(self):
        self.sent = []
    def connect(self):
        pass
    def disconnect(self):
        pass
    def send(self, cmd):
        self.sent.append(cmd)
    def query(self, cmd):
        return "1.23"


def test_controller_commands():
    dummy = DummyConn()
    ctrl = PowerSupplyController(dummy)
    ctrl.open()
    ctrl.set_voltage(5)
    ctrl.set_current(1)
    ctrl.output_on()
    ctrl.output_off()
    v = ctrl.measure_voltage()
    i = ctrl.measure_current()
    assert v == 1.23
    assert i == 1.23
