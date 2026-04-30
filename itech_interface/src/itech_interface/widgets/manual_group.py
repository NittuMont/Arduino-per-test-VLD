from PyQt5 import QtWidgets

class ManualGroup(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Prove di Isolamento", parent)
        layout = QtWidgets.QHBoxLayout()
        self.voltage_100_btn = QtWidgets.QPushButton("Prova 100 V")
        self.voltage_500_btn = QtWidgets.QPushButton("Prova 500 V")
        layout.addWidget(self.voltage_100_btn)
        layout.addWidget(self.voltage_500_btn)
        self.setLayout(layout)
