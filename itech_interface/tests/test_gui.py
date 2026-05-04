"""Basic smoke tests for the GUI module.

These verify imports and widget construction without requiring
a real PSU or BLE connection.
"""
import pytest
from PyQt5 import QtWidgets

from itech_interface import gui
from itech_interface.gui import (
    MainWindow,
    AD_START_VOLTAGE,
    AT_AL_START_VOLTAGE,
    INNESCO_START_VOLTAGE,
    TEST_CURRENT_A,
    INNESCO_DIODE_OFFSET_V,
)


class DummyConn:
    def __init__(self, host=None):
        self.sent = []
        self.connected = False
    def connect(self):
        self.connected = True
    def disconnect(self):
        self.connected = False
    def send(self, cmd):
        self.sent.append(cmd)
    def query(self, cmd):
        return "1.23"
    def ping(self):
        return self.connected
    def reconnect(self):
        self.connect()
    @property
    def is_connected(self):
        return self.connected


@pytest.fixture(scope="module")
def qapp():
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


def test_default_ip_and_auto_connect(monkeypatch, qapp):
    monkeypatch.setattr(gui, "ITechConnection", DummyConn)
    window = MainWindow()
    qapp.processEvents()
    assert isinstance(window.ctrl, gui.PowerSupplyController)
    assert window.conn.connected is True


def test_constants_defined():
    assert AD_START_VOLTAGE == 87
    assert AT_AL_START_VOLTAGE == 88
    assert INNESCO_START_VOLTAGE == 89
    assert TEST_CURRENT_A == 2
    assert INNESCO_DIODE_OFFSET_V == 10.55
    assert not trip_btn.isEnabled()
    # find status label (last QLabel added)
    labels = popup.findChildren(QtWidgets.QLabel)
    status_label = labels[-1]
    assert "Tensione applicata" in status_label.text()
    # closing popup via button should hide it
    close_btn.click()
    assert not popup.isVisible()

    # simulate clicking start and a few voltage increments
    start_btn.click()
    # after start, trip button enabled and initial commands sent
    assert trip_btn.isEnabled()
    assert f"VOLT {AD_START_VOLTAGE}" in window.conn.sent
    assert f"CURR {TEST_CURRENT_A}" in window.conn.sent
    assert "OUTP ON" in window.conn.sent
    # simulate a couple of timer ticks manually
    window._ad_step()
    window._ad_step()
    assert f"VOLT {AD_START_VOLTAGE + 1}" in window.conn.sent
    assert f"VOLT {AD_START_VOLTAGE + 2}" in window.conn.sent
    # status label updated accordingly
    assert f"Tensione applicata: {AD_START_VOLTAGE + 2}" in status_label.text()
    # simulate trip button
    trip_btn.click()
    assert "Cartellino scattato a" in status_label.text()
    # ensure timer stopped
    assert not getattr(window, '_ad_timer').isActive()
    # output should be disabled then device put in local
    assert "OUTP OFF" in window.conn.sent
    assert "SYST:LOC" in window.conn.sent

    window.ad_al_btn.click()
    # popup created with two cartellino buttons
    assert hasattr(window, '_at_al_popup')
    popup2 = window._at_al_popup
    buttons = popup2.findChildren(QtWidgets.QPushButton)
    start_btn = next((b for b in buttons if b.text() == "INIZIO TEST"), None)
    cart1_btn = next((b for b in buttons if b.text() == "Cartellino 1 scattato"), None)
    cart2_btn = next((b for b in buttons if b.text() == "Cartellino 2 scattato"), None)
    close_btn2 = next((b for b in buttons if b.text() == "Chiudi"), None)
    assert start_btn is not None and cart1_btn is not None and cart2_btn is not None and close_btn2 is not None
    assert not cart1_btn.isEnabled()
    assert not cart2_btn.isEnabled()
    # closing second popup
    close_btn2.click()
    assert not popup2.isVisible()
    # start test
    start_btn.click()
    assert cart1_btn.isEnabled()
    assert f"VOLT {AT_AL_START_VOLTAGE}" in window.conn.sent
    assert f"CURR {TEST_CURRENT_A}" in window.conn.sent
    assert "OUTP ON" in window.conn.sent
    # simulate couple of steps
    window._at_al_step()
    window._at_al_step()
    assert f"VOLT {AT_AL_START_VOLTAGE + 1}" in window.conn.sent
    assert f"VOLT {AT_AL_START_VOLTAGE + 2}" in window.conn.sent
    # press cart1 and check label
    cart1_btn.click()
    assert hasattr(window, '_at_al_cart1_value')
    assert "Cartellino1" in window._at_al_cart1_label.text()
    # second button enabled
    assert cart2_btn.isEnabled()
    # press cart2 and verify stop and local/off commands
    cart2_btn.click()
    assert "OUTP OFF" in window.conn.sent
    assert "SYST:LOC" in window.conn.sent
    assert not getattr(window, '_at_al_timer').isActive()

    window.innesco_btn.click()
    # pre-test popup should appear
    assert hasattr(window, '_pre_innesco_popup')
    pre_popup = window._pre_innesco_popup
    pre_buttons = pre_popup.findChildren(QtWidgets.QPushButton)
    pre_start = next((b for b in pre_buttons if b.text() == "INIZIO TEST"), None)
    pre_close = next((b for b in pre_buttons if b.text() == "Chiudi"), None)
    assert pre_start is not None and pre_close is not None
    # ensure close works
    pre_close.click()
    assert not pre_popup.isVisible()
    # reopen to continue normal sequence
    window.innesco_btn.click()
    pre_popup = window._pre_innesco_popup
    pre_buttons = pre_popup.findChildren(QtWidgets.QPushButton)
    pre_start = next((b for b in pre_buttons if b.text() == "INIZIO TEST"), None)
    pre_start.click()
    assert "Test Innesco in corso" in window.result_label.text()

    # also verify the main window quit button hides the window
    window.quit_btn.click()
    assert not window.isVisible()
    # recreate window to continue testing further routines
    window = MainWindow()
    qapp.processEvents()

    # now test innesco tiristore procedure
    class CounterCtrl(DummyConn):
        def __init__(self, host=None):
            super().__init__(host)
            # will return increasing values then a drop
            self._meas_seq = [89, 90, 91, 89]
        def query(self, cmd):
            # ignore command string, pop next measurement
            if self._meas_seq:
                return str(self._meas_seq.pop(0))
            return "120"
    # patch the connection to our counter
    monkeypatch.setattr(gui, "ITechConnection", CounterCtrl)
    window = MainWindow()
    qapp.processEvents()
    window.innesco_btn.click()
    # click pre-test start button as before
    assert hasattr(window, '_pre_innesco_popup')
    pre_popup2 = window._pre_innesco_popup
    pre_buttons2 = pre_popup2.findChildren(QtWidgets.QPushButton)
    pre_start2 = next((b for b in pre_buttons2 if b.text() == "INIZIO TEST"), None)
    assert pre_start2 is not None
    pre_start2.click()
    # initial commands should be sent
    assert f"VOLT {INNESCO_START_VOLTAGE}" in window.conn.sent
    assert f"CURR {TEST_CURRENT_A}" in window.conn.sent
    assert "OUTP ON" in window.conn.sent
    # simulate timer steps until drop detected (innesco_running becomes False)
    while getattr(window, '_innesco_running', False):
        window._innesco_step()
    # after stopping, history should contain at least two values
    assert len(window._innesco_history) >= 2
    # history should include the drop (last < previous)
    assert window._innesco_history[-1] < window._innesco_history[-2]
    # simulate the delayed diode drop measurement
    window._calculate_diode_drop(max(window._innesco_history[:-1]))
    # after diode drop the popup should close automatically and
    # _write_to_excel calls _safe_power_off which sends OUTP OFF
    assert "OUTP OFF" in window.conn.sent
    assert "SYST:LOC" in window.conn.sent
    # popup should have been closed by _write_to_excel
    assert getattr(window, '_innesco_popup', None) is None
