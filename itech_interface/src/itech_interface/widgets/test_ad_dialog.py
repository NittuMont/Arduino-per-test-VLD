from PyQt5 import QtWidgets, QtCore
from .dialog_style import POPUP_STYLESHEET

class TestADDialog(QtWidgets.QDialog):
    def __init__(self, parent, ctrl, write_to_excel, update_status, safe_power_off,
                 timer_step_ms=None, next_test_callback=None):
        super().__init__(parent)
        self.ctrl = ctrl
        self.write_to_excel = write_to_excel
        self.update_status = update_status
        self.safe_power_off = safe_power_off
        self._next_test_callback = next_test_callback
        self.setWindowTitle("Anomalia Diodo (AD)")
        self._ad_voltage = 87  # AD_START_VOLTAGE
        self._timer_interval = timer_step_ms if timer_step_ms is not None else 1000
        self._setup_ui()


    def _setup_ui(self):
        self.setMinimumWidth(500)
        self.setStyleSheet(POPUP_STYLESHEET)
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
        self.status_label = QtWidgets.QLabel("Tensione applicata: — V")
        self.status_label.setObjectName("voltage_live")
        layout.addWidget(self.status_label)
        self.close_btn = QtWidgets.QPushButton("Chiudi")
        self.close_btn.setObjectName("close_btn")
        layout.addWidget(self.close_btn)
        self.close_btn.clicked.connect(self.reject)
        self.setLayout(layout)
        self.start_btn.clicked.connect(self._start_test)
        self.start_btn.setDefault(True)
        self.start_btn.setFocus()
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

    def on_relay_tripped(self):
        """Chiamato dal BLE handler quando il relè AD scatta."""
        self._ad_tripped()

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
            next_test_label="Prosegui con test AL+AT" if self._next_test_callback else None,
            next_test_callback=self._next_test_callback,
        )
        self.update_status("Test AD completato", "ok")
