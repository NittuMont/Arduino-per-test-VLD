from PyQt5 import QtWidgets, QtCore

class BleGroup(QtWidgets.QGroupBox):
        # Legenda associazione circuiti ↔ pin Arduino:
        # "Relè AT ON"   → D12
        # "Relè AL ON"   → D7
        # "Relè AD ON"   → D3
        # "Relè AT OFF"  → D11
        # "Relè AL OFF"  → D6
        # "Relè AD OFF"  → D2
    def __init__(self, parent=None):
        super().__init__("Monitor BLE 6 Circuiti", parent)
        layout = QtWidgets.QVBoxLayout()
        # RIMOSSO: self.ble_status_label
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
        # Nuovo ordine richiesto:
        # Sinistra: AT ON (0,0), AL ON (1,0), AD ON (2,0)
        # Destra:   AT OFF (0,1), AL OFF (1,1), AD OFF (2,1)
        self.circuit_names = [
            "Relè AT ON", "Relè AL ON", "Relè AD ON",
            "Relè AT OFF", "Relè AL OFF", "Relè AD OFF"
        ]
        positions = [
            (0, 0),  # AT ON
            (1, 0),  # AL ON
            (2, 0),  # AD ON
            (0, 1),  # AT OFF
            (1, 1),  # AL OFF
            (2, 1),  # AD OFF
        ]
        for i, pos in enumerate(positions):
            label = QtWidgets.QLabel(f"{self.circuit_names[i]}: ?")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("background:#ccc; font-size:18px; border-radius:8px; padding:6px;")
            grid.addWidget(label, *pos)
            self.ble_circuit_labels.append(label)
        layout.addLayout(grid)
        self.setLayout(layout)
