from PyQt5 import QtWidgets, QtCore

# Handler BLE per MainWindow
class BLEHandlers:
    def __init__(self, main_window):
        self.main = main_window

    def on_ble_reconnect_clicked(self):
        self.main.ble_status_bar.set_status('connecting')
        self.main.ble_worker.scan_ble()

    def on_ble_devices_found(self, found):
        self.main.ble_device_combo.clear()
        self.main._ble_devices = []
        arduino_name = "NanoESP32-RelayMonitor"
        arduino_device = None
        for d in found:
            name = d.name if d.name else "<No Name>"
            if name == arduino_name:
                arduino_device = d
                self.main.ble_device_combo.addItem(f"{name} [{d.address}]", d)
                self.main._ble_devices.append(d)
                break
        self.main.ble_connect_btn.setEnabled(bool(self.main._ble_devices))
        if arduino_device:
            self.main.ble_device_combo.setCurrentIndex(0)
            self.on_ble_connect_clicked()  # Connessione automatica
        else:
            QtCore.QTimer.singleShot(500, self.main.ble_worker.scan_ble)
        self.main.ble_status_bar.set_status('fail' if not self.main._ble_devices else 'connecting')

    def on_ble_error(self, msg):
        import traceback
        self.main.ble_status_bar.set_status('fail')
        print(f"[BLE ERROR SUPPRESSED] {msg}")
        print("[BLE ERROR TRACE]")
        traceback.print_stack()

    def on_ble_state_update(self, state_byte):
        for i in range(6):
            closed = (state_byte >> i) & 1
            label = self.main.ble_circuit_labels[i]
            if closed:
                label.setText(self.main.ble_group.circuit_names[i] + ": CHIUSO")
                label.setStyleSheet("background:#8f8; font-size:18px; border-radius:8px; padding:6px;")
            else:
                label.setText(self.main.ble_group.circuit_names[i] + ": APERTO")
                label.setStyleSheet("background:#f88; font-size:18px; border-radius:8px; padding:6px;")

    def on_ble_connected(self):
        print(f"[DEBUG] on_ble_connected: setting self.main._ble_connected_flag = True (was {self.main._ble_connected_flag})")
        self.main.ble_status_bar.set_status('ok')
        self.main._ble_connected_flag = True
        self.main._ad_timer_interval_ms = max(1, int(self.main.AD_TIMER_INTERVAL_MS * 0.1))
        self.main._at_al_timer_interval_ms = max(1, int(self.main.AT_AL_TIMER_INTERVAL_MS * 0.1))
        self.main._innesco_timer_interval_ms = max(1, int(self.main.INNESCO_TIMER_INTERVAL_MS * 0.1))

    def on_ble_disconnected(self):
        print(f"[DEBUG] on_ble_disconnected: setting self.main._ble_connected_flag = False (was {self.main._ble_connected_flag})")
        self.main.ble_status_bar.set_status('fail')
        self.main._ble_connected_flag = False
        self.main._ad_timer_interval_ms = self.main.AD_TIMER_INTERVAL_MS
        self.main._at_al_timer_interval_ms = self.main.AT_AL_TIMER_INTERVAL_MS
        self.main._innesco_timer_interval_ms = self.main.INNESCO_TIMER_INTERVAL_MS
        QtWidgets.QMessageBox.warning(self.main, "Connessione BLE", "Connessione BLE persa! Tentativo di riconnessione...")
        self.main._ble_devices = []
        self.main.ble_device_combo.clear()
        QtCore.QTimer.singleShot(500, self.main.ble_worker.scan_ble)

    def on_ble_connect_clicked(self):
        idx = self.main.ble_device_combo.currentIndex()
        print(f"[DEBUG] on_ble_connect_clicked: _ble_connected_flag is {self.main._ble_connected_flag}")
        if hasattr(self.main, '_ble_devices') and self.main._ble_devices and 0 <= idx < len(self.main._ble_devices):
            device = self.main._ble_devices[idx]
            self.main.ble_status_bar.set_status('connecting')
            self.main.ble_worker.connect_device(device)
        else:
            QtWidgets.QMessageBox.warning(self.main, "BLE", "Nessun dispositivo selezionato.")
