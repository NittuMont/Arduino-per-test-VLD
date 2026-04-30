from PyQt5 import QtWidgets, QtCore
from .status_semaphore import StatusSemaphore

class BLEStatusBar(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.status_light = StatusSemaphore("", "#ccc")
        self.status_text = QtWidgets.QLabel("BLE")
        self.status_text.setStyleSheet("font-size:13pt; font-weight:bold;")
        self.reconnect_btn = QtWidgets.QPushButton("Riconnetti BLE")
        self.reconnect_btn.setToolTip("Tenta una nuova connessione manuale BLE")
        layout.addWidget(self.status_light)
        layout.addWidget(self.status_text)
        layout.addWidget(self.reconnect_btn)
        layout.addStretch()
        self.setLayout(layout)

    def set_status(self, state):
        if state == 'ok':
            self.status_light.set_status("", "#4caf50")
            self.status_text.setText("BLE: Connesso")
        elif state == 'connecting':
            self.status_light.set_status("", "#ffd600")
            self.status_text.setText("BLE: Connessione...")
        elif state == 'fail':
            self.status_light.set_status("", "#d13438")
            self.status_text.setText("BLE: Non connesso")
        else:
            self.status_light.set_status("", "#ccc")
            self.status_text.setText("BLE")
