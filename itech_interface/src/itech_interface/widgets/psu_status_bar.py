from PyQt5 import QtWidgets, QtCore
from .status_semaphore import StatusSemaphore

class PSUStatusBar(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.status_light = StatusSemaphore("", "#ccc")
        self.status_text = QtWidgets.QLabel("Alimentatore")
        self.status_text.setStyleSheet("font-size:13pt; font-weight:bold;")
        self.attempts_label = QtWidgets.QLabel("Tentativi: 0")
        self.reconnect_btn = QtWidgets.QPushButton("Riconnetti PSU")
        self.reconnect_btn.setToolTip("Tenta una nuova connessione manuale all'alimentatore")
        layout.addWidget(self.status_light)
        layout.addWidget(self.status_text)
        layout.addWidget(self.attempts_label)
        layout.addWidget(self.reconnect_btn)
        layout.addStretch()
        self.setLayout(layout)

    def set_status(self, state):
        if state == 'ok':
            self.status_light.set_status("", "#4caf50")
            self.status_text.setText("Alimentatore: Connesso")
        elif state == 'connecting':
            self.status_light.set_status("", "#ffd600")
            self.status_text.setText("Alimentatore: Connessione...")
        elif state == 'fail':
            self.status_light.set_status("", "#d13438")
            self.status_text.setText("Alimentatore: Non connesso")
        else:
            self.status_light.set_status("", "#ccc")
            self.status_text.setText("Alimentatore")

    def set_attempts(self, n):
        self.attempts_label.setText(f"Tentativi: {n}")
