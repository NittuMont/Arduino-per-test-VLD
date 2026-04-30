"""High-level control commands for the power supply."""

from .network import ITechConnection

class PowerSupplyController:
    def __init__(self, connection: ITechConnection):
        self.conn = connection

    def open(self):
        self.conn.connect()

    def close(self):
        self.conn.disconnect()

    def set_voltage(self, volts: float):
        self.conn.send(f"VOLT {volts}")

    def set_current(self, amps: float):
        self.conn.send(f"CURR {amps}")

    def output_on(self):
        self.conn.send("OUTP ON")

    def output_off(self):
        self.conn.send("OUTP OFF")

    def local_mode(self):
        """Switch the device to local (front-panel) control."""
        # SCPI command for local mode; adjust if device uses different syntax
        self.conn.send("SYST:LOC")

    def measure_voltage(self) -> float:
        resp = self.conn.query("MEAS:VOLT?")
        return float(resp)

    def measure_current(self) -> float:
        resp = self.conn.query("MEAS:CURR?")
        return float(resp)
