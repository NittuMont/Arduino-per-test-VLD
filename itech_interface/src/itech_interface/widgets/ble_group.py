from PyQt5 import QtWidgets, QtCore

class BleGroup(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Monitor BLE 6 Circuiti", parent)
        layout = QtWidgets.QVBoxLayout()
        self.ble_status_label = QtWidgets.QLabel("BLE non connesso")
        self.ble_status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.ble_status_label.setStyleSheet("background:#ffe0e0; font-size:15pt; border-radius:6px; padding:8px;")
        layout.addWidget(self.ble_status_label)
        ble_btn_layout = QtWidgets.QHBoxLayout()
        self.ble_scan_btn = QtWidgets.QPushButton("Scansiona BLE")
        ble_btn_layout.addWidget(self.ble_scan_btn)
        self.ble_connect_btn = QtWidgets.QPushButton("Connetti BLE")
        self.ble_connect_btn.setEnabled(False)
        ble_btn_layout.addWidget(self.ble_connect_btn)
        self.ble_bypass_btn = QtWidgets.QPushButton("Bypass BLE (solo alimentatore)")
        self.ble_bypass_btn.setCheckable(True)
        ble_btn_layout.addWidget(self.ble_bypass_btn)
        layout.addLayout(ble_btn_layout)
        self.ble_device_combo = QtWidgets.QComboBox()
        self.ble_device_combo.setEditable(False)
        layout.addWidget(self.ble_device_combo)
        self.ble_circuit_labels = []
        grid = QtWidgets.QGridLayout()
        circuit_names = [
            "Relè AD OFF", "Relè AD ON", "Relè AL OFF",
            "Relè AL ON", "Relè AT OFF", "Relè AT ON"
        ]
        for i in range(6):
            label = QtWidgets.QLabel(f"{circuit_names[i]}: ?")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("background:#ccc; font-size:18px; border-radius:8px; padding:6px;")
            grid.addWidget(label, i // 3, i % 3)
            self.ble_circuit_labels.append(label)
        layout.addLayout(grid)
        self.setLayout(layout)
