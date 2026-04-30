from PyQt5 import QtCore, QtWidgets
import sys
import asyncio
from bleak import BleakScanner, BleakClient

# Worker BLE minimale: solo connessione, ricezione notifiche di stato
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

    def run(self):
        try:
            asyncio.run(self._main())
        except Exception as e:
            self.error.emit(str(e))

    async def _main(self):
        while self._running:
            await asyncio.sleep(0.1)
            if self._connect_device:
                await self._connect_and_notify(self._connect_device)
                self._connect_device = None

    def scan_ble(self):
        asyncio.create_task(self._scan_ble())

    async def _scan_ble(self):
        try:
            found = await BleakScanner.discover(timeout=5.0)
            self.devices_found.emit(found)
        except Exception as e:
            self.error.emit(str(e))

    def connect_device(self, device):
        self._connect_device = device

    async def _connect_and_notify(self, device):
        try:
            self._client = BleakClient(device)
            await self._client.connect()
            self.connected.emit()
            await self._client.start_notify(
                "b7e2e8c0-0001-4b1a-8e1e-000000000002",
                self._notification_handler
            )
            # Invia comando READY all'Arduino per ricevere lo stato iniziale
            try:
                await self._client.write_gatt_char(
                    "b7e2e8c0-0002-4b1a-8e1e-000000000003", b"READY"
                )
                print("[DEBUG] Comando READY inviato all'Arduino")
            except Exception as e:
                print(f"[DEBUG] Errore invio comando READY: {e}")
            while await self._client.is_connected():
                await asyncio.sleep(0.1)
            self.disconnected.emit()
        except Exception as e:
            self.error.emit(str(e))

    def _notification_handler(self, sender, data):
        # Ricevi solo pacchetti di stato: [0x00, seq, stato]
        if len(data) == 3 and data[0] == 0x00:
            seq, state_byte = data[1], data[2]
            print(f"[DEBUG] Ricevuto stato: seq={seq}, stato={state_byte:06b}")
            try:
                self.state_update.emit(state_byte)
            except Exception as e:
                print(f"[DEBUG] Exception in state_update.emit: {e}")
        # Gestione stato legacy (1 byte)
        elif len(data) == 1:
            state_byte = data[0]
            try:
                self.state_update.emit(state_byte)
            except Exception as e:
                print(f"[DEBUG] Exception in state_update.emit: {e}")




class CircuitMonitorWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.healthcheck_lost = False
        self.connection_timer = QtCore.QTimer()
        self.connection_timer.setInterval(5000)
        self.connection_timer.setSingleShot(True)
        self.connection_timer.timeout.connect(self._on_connection_timeout)
        self.setWindowTitle("Monitor BLE 6 Circuiti")
        self.resize(400, 200)
        layout = QtWidgets.QVBoxLayout()
        self.status_labels = []
        grid = QtWidgets.QGridLayout()
        # Nomi circuiti secondo la nuova mappatura
        self.circuit_names = [
            "Relè AD OFF",  # Circuito 1
            "Relè AD ON",   # Circuito 2
            "Relè AL OFF",  # Circuito 3
            "Relè AL ON",   # Circuito 4
            "Relè AT OFF",  # Circuito 5
            "Relè AT ON"    # Circuito 6
        ]
        for i in range(6):
            label = QtWidgets.QLabel(f"{self.circuit_names[i]}: ?")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("background:#ccc; font-size:22px; border-radius:8px; padding:10px;")
            grid.addWidget(label, i // 3, i % 3)
            self.status_labels.append(label)
        layout.addLayout(grid)

        self.device_combo = QtWidgets.QComboBox()
        self.device_combo.setEditable(False)
        self.device_combo.setMinimumWidth(250)
        layout.addWidget(self.device_combo)
        self.scan_btn = QtWidgets.QPushButton("Scansiona BLE")
        self.scan_btn.clicked.connect(self.scan_ble)
        layout.addWidget(self.scan_btn)
        self.connect_btn = QtWidgets.QPushButton("Connetti BLE")
        self.connect_btn.clicked.connect(self.start_ble)
        self.connect_btn.setEnabled(False)
        layout.addWidget(self.connect_btn)
        self.setLayout(layout)

        self.ble_worker = AsyncBLEWorker()
        self.ble_worker.devices_found.connect(self.on_devices_found)
        self.ble_worker.error.connect(self.on_scan_error)
        self.ble_worker.state_update.connect(self.update_status)
        self.ble_worker.connected.connect(self.on_ble_connected)
        self.ble_worker.disconnected.connect(self.on_ble_disconnected)
        self.ble_worker.start()
        self.devices = []
        # Avvia subito la scansione BLE all'avvio
        self.ble_worker.devices_found.connect(self.on_devices_found)
        self.ble_worker.error.connect(self.on_scan_error)
        self.ble_worker.state_update.connect(self.update_status)
        self.ble_worker.connected.connect(self.on_ble_connected)
        self.ble_worker.disconnected.connect(self.on_ble_disconnected)
        self.ble_worker.start()
        self.devices = []
        # Avvia subito la scansione BLE all'avvio
        QtCore.QTimer.singleShot(500, self.scan_ble)

    def scan_ble(self):
        self.scan_btn.setEnabled(False)
        self.device_combo.clear()
        self.devices = []
        self.ble_worker.scan_ble()

    def on_devices_found(self, found):
        # Cerca solo il device Arduino desiderato
        arduino_name = "NanoESP32-RelayMonitor"
        arduino_device = None
        self.device_combo.clear()
        self.devices = []
        for d in found:
            name = d.name if d.name else "<No Name>"
            if name == arduino_name:
                arduino_device = d
                self.device_combo.addItem(f"{name} [{d.address}]", d)
                self.devices.append(d)
                break  # Solo il primo trovato
        self.scan_btn.setEnabled(True)
        self.connect_btn.setEnabled(bool(self.devices))
        if arduino_device:
            self.device_combo.setCurrentIndex(0)
            self.start_ble()
        else:
            # Se non trovato, ripeti la scansione dopo 500 ms
            QtCore.QTimer.singleShot(500, self.scan_ble)

    def on_scan_error(self, msg):
        self.scan_btn.setEnabled(True)
        # Mostra errore solo se non connesso
        if self.connect_btn.text() != "Connesso!":
            QtWidgets.QMessageBox.critical(self, "Errore scansione BLE", msg)

    def start_ble(self):
        idx = self.device_combo.currentIndex()
        if idx < 0 or idx >= len(self.devices):
            QtWidgets.QMessageBox.warning(self, "BLE", "Seleziona un dispositivo BLE dalla lista.")
            return
        self.connect_btn.setEnabled(False)
        device = self.devices[idx]
        self.ble_worker.connect_device(device)

    def on_ble_connected(self):
        self.connect_btn.setText("Connesso!")

    def on_ble_disconnected(self):
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("Connetti BLE")
        QtWidgets.QMessageBox.warning(self, "Connessione persa", "Connessione BLE persa! Tentativo di riconnessione...")
        # Forza la scansione e la riconnessione automatica
        self.devices = []
        self.device_combo.clear()
        QtCore.QTimer.singleShot(500, self.scan_ble)

    def update_status(self, state_byte):
        print(f"[DEBUG] update_status chiamato con state_byte={state_byte:08b} ({state_byte})")
        # Reset del timer di connessione ogni volta che arriva un dato
        self.connection_timer.start()
        for i in range(6):
            closed = (state_byte >> i) & 1
            label = self.status_labels[i]
            if closed:
                label.setText(f"{self.circuit_names[i]}: CHIUSO")
                label.setStyleSheet("background:#8f8; font-size:22px; border-radius:8px; padding:10px;")
            else:
                label.setText(f"{self.circuit_names[i]}: APERTO")
                label.setStyleSheet("background:#f88; font-size:22px; border-radius:8px; padding:10px;")

    def _on_connection_timeout(self):
        QtWidgets.QMessageBox.warning(self, "Connessione persa", "Nessun dato ricevuto dall'Arduino negli ultimi 5 secondi. Tentativo di riconnessione...")
        self.connect_btn.setText("Riconnessione...")
        self.devices = []
        self.device_combo.clear()
        QtCore.QTimer.singleShot(500, self.scan_ble)

    def on_ble_error(self, msg):
        self.connect_btn.setEnabled(True)
        # Mostra errore solo se non connesso
        if self.connect_btn.text() != "Connesso!":
            self.connect_btn.setText("Errore BLE")
            QtWidgets.QMessageBox.critical(self, "Errore BLE", msg)
        else:
            self.connect_btn.setText("Connesso!")

    def on_ble_finished(self):
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("Connetti BLE")

import qasync
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    widget = CircuitMonitorWidget()
    widget.show()
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        loop.run_forever()
