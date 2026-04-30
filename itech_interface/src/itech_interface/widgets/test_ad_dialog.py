from PyQt5 import QtWidgets, QtCore

class TestADDialog(QtWidgets.QDialog):
    def __init__(self, parent, ctrl, write_to_excel, update_status, safe_power_off, timer_step_ms=None):
        super().__init__(parent)
        self.ctrl = ctrl
        self.write_to_excel = write_to_excel
        self.update_status = update_status
        self.safe_power_off = safe_power_off
        self.setWindowTitle("Anomalia Diodo (AD)")
        self._ad_voltage = 87  # AD_START_VOLTAGE
        # timer_step_ms: valore scelto dall'utente, default 1000ms se non specificato
        self._timer_interval = timer_step_ms if timer_step_ms is not None else 1000
        self._setup_ui()

    _POPUP_STYLESHEET = """
        QDialog {
            background-color: #f0f2f5;
        }
        QDialog * {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 15pt;
        }
        QDialog QPushButton {
            min-height: 46px;
            padding: 8px 18px;
            background-color: #0078d4;
            color: white;
            border: none;
            border-radius: 6px;
        }
        QDialog QPushButton:hover {
            background-color: #106ebe;
        }
        QDialog QPushButton:pressed {
            background-color: #005a9e;
        }
        QDialog QPushButton:disabled {
            background-color: #b0b0b0;
            color: #e0e0e0;
        }
        QDialog QPushButton#start_btn {
            background-color: #107c10;
            font-weight: bold;
        }
        QDialog QPushButton#start_btn:hover {
            background-color: #0b6a0b;
        }
        QDialog QPushButton#close_btn {
            background-color: #d13438;
        }
        QDialog QPushButton#close_btn:hover {
            background-color: #a4262c;
        }
        QDialog QPushButton#cart_btn {
            min-height: 92px;
        }
        QDialog QLabel#instructions {
            background-color: #e8f4fd;
            border: 1px solid #b3d7f0;
            border-radius: 6px;
            padding: 12px;
            color: #004578;
            font-size: 14pt;
        }
        QDialog QLabel#voltage_live {
            background-color: #fff4ce;
            border: 1px solid #f0d060;
            border-radius: 6px;
            padding: 10px;
            font-size: 16pt;
            font-weight: bold;
            color: #8a6d00;
        }
        QDialog QLabel {
            padding: 4px 0px;
            color: #333;
        }
    """

    def _setup_ui(self):
        self.setMinimumWidth(500)
        self.setStyleSheet(self._POPUP_STYLESHEET)
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        instructions = QtWidgets.QLabel(
            "Collegare l'alimentatore con il positivo al punto \"B\" (binario) e il negativo al punto \"T\" (palo).\n"
            "Collegare il filo rosso al faston TP1 e il filo nero al faston TP4.\n"
            "Lasciare il filo bianco non connesso."
        )
        instructions.setObjectName("instructions")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        self.start_btn = QtWidgets.QPushButton("INIZIO TEST")
        self.start_btn.setObjectName("start_btn")
        layout.addWidget(self.start_btn)
        self.trip_btn = QtWidgets.QPushButton("Cartellino scattato")
        self.trip_btn.setObjectName("cart_btn")
        self.trip_btn.setEnabled(False)
        layout.addWidget(self.trip_btn)
        self.status_label = QtWidgets.QLabel(f"Tensione applicata: {self._ad_voltage} V")
        self.status_label.setObjectName("voltage_live")
        layout.addWidget(self.status_label)
        self.close_btn = QtWidgets.QPushButton("Chiudi")
        self.close_btn.setObjectName("close_btn")
        layout.addWidget(self.close_btn)
        self.close_btn.clicked.connect(self.reject)
        self.setLayout(layout)
        self.start_btn.clicked.connect(self._start_test)
        self.trip_btn.clicked.connect(self._ad_tripped)

    def _start_test(self):
        if not self.ctrl:
            QtWidgets.QMessageBox.warning(
                self, "Errore", "Collegare l'alimentatore prima di avviare il test Anomalia Diodo (AD)."
            )
            return
        self.update_status("Test AD in corso...", "working")
        self.ctrl.set_voltage(self._ad_voltage)
        self.ctrl.set_current(2)  # TEST_CURRENT_A
        self.ctrl.output_on()
        self.trip_btn.setEnabled(True)
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._ad_step)
        self._timer.start(self._timer_interval)

    def _ad_step(self):
        if self._ad_voltage >= 120:  # TEST_MAX_VOLTAGE
            self._timer.stop()
            self.ctrl.output_off()
            self.ctrl.local_mode()
            self.status_label.setText(f"Tensione massima (120 V) raggiunta senza scatto.")
            self.update_status("Test AD completato", "ok")
            return
        self._ad_voltage += 1
        self.ctrl.set_voltage(self._ad_voltage)
        self.status_label.setText(f"Tensione applicata: {self._ad_voltage} V")

    def _ad_tripped(self):
        if hasattr(self, "_timer") and self._timer.isActive():
            self._timer.stop()
        self.status_label.setText(f"Cartellino scattato a {self._ad_voltage} V")
        summary = (
            f"Anomalia Diodo (AD)\n"
            f"Tensione di scatto: {self._ad_voltage} V\n"
            f"Colonne: T={self._ad_voltage}, V=POS.\n\n"
            f"Riarmare i cartellini."
        )
        self.write_to_excel(
            lambda handler, row: handler.write_ad_results(row, self._ad_voltage),
            summary=summary,
            popup_to_close=self,
        )
        self.update_status("Test AD completato", "ok")
        self.accept()
