from PyQt5 import QtCore
import asyncio
from bleak import BleakScanner, BleakClient

SERVICE_UUID = "b7e2e8c0-0000-4b1a-8e1e-000000000001"
STATE_CHAR_UUID = "b7e2e8c0-0001-4b1a-8e1e-000000000002"
ACK_CHAR_UUID = "b7e2e8c0-0002-4b1a-8e1e-000000000003"

class AsyncBLEWorker(QtCore.QThread):
    devices_found = QtCore.pyqtSignal(list)
    error = QtCore.pyqtSignal(str)
    state_update = QtCore.pyqtSignal(int)
    connected = QtCore.pyqtSignal()
    disconnected = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self._running = True
        self._connect_device = None
        self._client = None
        self._scan_requested = False

    def run(self):
        import traceback
        try:
            asyncio.run(self._main())
        except Exception as e:
            print("[BLE WORKER ERROR TRACE]")
            traceback.print_exc()
            self.error.emit(str(e))

    async def _main(self):
        while self._running:
            await asyncio.sleep(0.1)
            if self._scan_requested:
                await self._scan_ble()
                self._scan_requested = False
            if self._connect_device:
                await self._connect_and_notify(self._connect_device)
                self._connect_device = None

    def scan_ble(self):
        self._scan_requested = True

    async def _scan_ble(self):
        import traceback
        try:
            found = await BleakScanner.discover(timeout=5.0)
            self.devices_found.emit(found)
        except Exception as e:
            print("[BLE WORKER ERROR TRACE]")
            traceback.print_exc()
            self.error.emit(str(e))

    def connect_device(self, device):
        self._connect_device = device

    async def _connect_and_notify(self, device):
        import traceback
        try:
            self._client = BleakClient(device)
            await self._client.connect()
            self.connected.emit()
            await self._client.start_notify(
                STATE_CHAR_UUID,
                self._notification_handler
            )
            # Invia comando READY all'Arduino per ricevere lo stato iniziale
            try:
                await self._client.write_gatt_char(
                    ACK_CHAR_UUID, b"READY"
                )
            except Exception as e:
                print(f"[DEBUG] Errore invio comando READY: {e}")
            while self._client.is_connected:
                await asyncio.sleep(0.1)
            self.disconnected.emit()
        except Exception as e:
            print("[BLE WORKER ERROR TRACE]")
            traceback.print_exc()
            self.error.emit(str(e))

    def _notification_handler(self, sender, data):
        # Ricevi solo pacchetti di stato: [0x00, seq, stato] oppure 1 byte
        if len(data) == 3 and data[0] == 0x00:
            seq, state_byte = data[1], data[2]
            try:
                self.state_update.emit(state_byte)
            except Exception as e:
                print(f"[DEBUG] Exception in state_update.emit: {e}")
        elif len(data) == 1:
            state_byte = data[0]
            try:
                self.state_update.emit(state_byte)
            except Exception as e:
                print(f"[DEBUG] Exception in state_update.emit: {e}")
