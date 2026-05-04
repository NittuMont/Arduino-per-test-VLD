from PyQt5 import QtWidgets, QtCore
from .dialog_style import POPUP_STYLESHEET

class TestATALDialog(QtWidgets.QDialog):
    # Step timer AT+AL: ora con 100ms, 50ms, 30ms, 25ms
    AT_AL_TIMER_STEPS_MS = [100, 50, 30, 25]

    def __init__(self, parent, ctrl, write_to_excel, update_status, safe_power_off,
                 timer_step_ms=None, next_test_callback=None):
        super().__init__(parent)
        self.ctrl = ctrl
        self.write_to_excel = write_to_excel
        self.update_status = update_status
        self.safe_power_off = safe_power_off
        self._next_test_callback = next_test_callback
        self.setWindowTitle("Test AT e AL")
        self._at_al_voltage = 88  # AT_AL_START_VOLTAGE
        self._timer_interval = timer_step_ms if timer_step_ms is not None else 1000
        self._setup_ui()


    def _setup_ui(self):
        self.setMinimumWidth(500)
        self.setStyleSheet(POPUP_STYLESHEET)
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        label = QtWidgets.QLabel(
            "Spostare il filo rosso sul faston TP4 e il filo nero sul faston TP1.\n"
            "Lasciare il filo bianco non connesso."
        )
        label.setObjectName("instructions")
        label.setWordWrap(True)
        layout.addWidget(label)
        self.start_btn = QtWidgets.QPushButton("INIZIO TEST")
        self.start_btn.setObjectName("start_btn")
        layout.addWidget(self.start_btn)
        self.status_label = QtWidgets.QLabel(f"Tensione applicata: {self._at_al_voltage} V")
        self.status_label.setObjectName("voltage_live")
        layout.addWidget(self.status_label)
        self.cart1_btn = QtWidgets.QPushButton("Cartellino 1 scattato")
        self.cart1_btn.setObjectName("cart_btn")
        self.cart1_btn.setEnabled(False)
        layout.addWidget(self.cart1_btn)
        self.cart1_label = QtWidgets.QLabel("Cartellino1: - V")
        self.cart1_label.setObjectName("cart_label")
        layout.addWidget(self.cart1_label)
        self.cart2_btn = QtWidgets.QPushButton("Cartellino 2 scattato")
        self.cart2_btn.setObjectName("cart_btn")
        self.cart2_btn.setEnabled(False)
        layout.addWidget(self.cart2_btn)
        self.cart2_label = QtWidgets.QLabel("Cartellino2: - V")
        self.cart2_label.setObjectName("cart_label")
        layout.addWidget(self.cart2_label)
        self.close_btn = QtWidgets.QPushButton("Chiudi")
        self.close_btn.setObjectName("close_btn")
        layout.addWidget(self.close_btn)
        self.close_btn.clicked.connect(self.reject)
        self.setLayout(layout)
        self.start_btn.clicked.connect(self._start_test)
        self.cart1_btn.clicked.connect(self._cart1)
        self.cart2_btn.clicked.connect(self._cart2)

    def _start_test(self):
        if not self.ctrl:
            QtWidgets.QMessageBox.warning(
                self, "Errore", "Collegare l'alimentatore prima di avviare il test AT+AL."
            )
            return
        self.update_status("Test AT+AL in corso...", "working")
        self._at_al_cart1_value = None
        self._at_al_cart2_value = None
        self.cart1_label.setText("Cartellino1: - V")
        self.cart2_label.setText("Cartellino2: - V")
        self.ctrl.set_voltage(self._at_al_voltage)
        self.ctrl.set_current(2)  # TEST_CURRENT_A
        self.ctrl.output_on()
        self.cart1_btn.setEnabled(True)
        self.status_label.setText(f"Tensione applicata: {self._at_al_voltage} V")
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._at_al_step)
        self._timer.start(self._timer_interval)

    def _at_al_step(self):
        if self._at_al_voltage >= 120:  # TEST_MAX_VOLTAGE
            self._timer.stop()
            self.ctrl.output_off()
            self.ctrl.local_mode()
            self.status_label.setText(f"Tensione massima (120 V) raggiunta.")
            self.update_status("Test AT+AL completato", "ok")
            return
        self._at_al_voltage += 1
        self.ctrl.set_voltage(self._at_al_voltage)
        self.status_label.setText(f"Tensione applicata: {self._at_al_voltage} V")

    # ------------------------------------------------------------------
    # Interfaccia pubblica per BLE handler e bottoni manuali
    # ------------------------------------------------------------------

    def on_relay_tripped(self, relay_name):
        """Chiamato dal BLE handler quando un relè (AL o AT) scatta."""
        self._record_trip()

    def _cart1(self):
        """Bottone manuale primo scatto."""
        self._record_trip()

    def _cart2(self):
        """Bottone manuale secondo scatto."""
        self._record_trip()

    def _record_trip(self):
        """Registra uno scatto. Primo → cart1, secondo → cart2 e finalizza."""
        v = self._at_al_voltage
        if self._at_al_cart1_value is None:
            self._at_al_cart1_value = v
            self.cart1_label.setText(f"Cartellino1: {v} V")
            self.cart2_btn.setEnabled(True)
        elif self._at_al_cart2_value is None:
            self._at_al_cart2_value = v
            self.cart2_label.setText(f"Cartellino2: {v} V")
            self._finalize()

    def _finalize(self):
        """Ferma il timer, salva il valore minimo su Excel e chiude il dialog."""
        if hasattr(self, '_timer') and self._timer.isActive():
            self._timer.stop()
        if self._at_al_cart1_value is None or self._at_al_cart2_value is None:
            return
        min_value = min(self._at_al_cart1_value, self._at_al_cart2_value)
        summary = (
            f"Anomalia Tiristore e Limiti (AT+AL)\n"
            f"Tensione Cartellino 1: {self._at_al_cart1_value} V\n"
            f"Tensione Cartellino 2: {self._at_al_cart2_value} V\n"
            f"Colonne: O={min_value}, Q=OK, R=OK, S=POS.\n\n"
            f"Riarmare i cartellini."
        )
        self.write_to_excel(
            lambda handler, row: handler.write_at_al_results(row, min_value),
            summary=summary,
            popup_to_close=self,
            next_test_label="Prosegui con test INNESCO" if self._next_test_callback else None,
            next_test_callback=self._next_test_callback,
        )
        self.update_status("Test AT+AL completato", "ok")
