from PyQt5 import QtWidgets

class TestGroup(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Routine di Test", parent)
        layout = QtWidgets.QVBoxLayout()
        self.ad_btn = QtWidgets.QPushButton("Anomalia Diodo (AD)")
        self.ad_al_btn = QtWidgets.QPushButton("Anomalia Tiristore e Limiti (AT e AL)")
        self.innesco_btn = QtWidgets.QPushButton("Innesco Tiristore")
        layout.addWidget(self.ad_btn)
        layout.addWidget(self.ad_al_btn)
        layout.addWidget(self.innesco_btn)
        self.setLayout(layout)
