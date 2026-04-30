import asyncio
from bleak import BleakClient, BleakScanner

SERVICE_UUID = "b7e2e8c0-0000-4b1a-8e1e-000000000001"
STATE_CHAR_UUID = "b7e2e8c0-0001-4b1a-8e1e-000000000002"
ACK_CHAR_UUID = "b7e2e8c0-0002-4b1a-8e1e-000000000003"

class BLEStateClient:
    def __init__(self):
        self.client = None
        self.device = None
        self.connected = False
        self.on_state_update = None  # callback: def(state_byte: int)

    async def connect_device(self, device):
        self.device = device
        self.client = BleakClient(self.device)
        await self.client.connect()
        self.connected = True
        await self.client.start_notify(STATE_CHAR_UUID, self._notification_handler)

    async def connect(self, device_name="NanoESP32-RelayMonitor"):
        devices = await BleakScanner.discover(timeout=5.0)
        for d in devices:
            if d.name and device_name in d.name:
                self.device = d
                break
        if not self.device:
            raise RuntimeError(f"Dispositivo BLE '{device_name}' non trovato")
        self.client = BleakClient(self.device)
        await self.client.connect()
        self.connected = True
        await self.client.start_notify(STATE_CHAR_UUID, self._notification_handler)

    async def disconnect(self):
        if self.client and self.connected:
            await self.client.disconnect()
            self.connected = False

    async def send_ack(self):
        if self.client and self.connected:
            await self.client.write_gatt_char(ACK_CHAR_UUID, b"\x01")

    def _notification_handler(self, sender, data):
        state_byte = data[0]
        if self.on_state_update:
            self.on_state_update(state_byte)
        # ACK automatico
        asyncio.create_task(self.send_ack())
