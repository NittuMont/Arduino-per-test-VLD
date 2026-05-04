from PyQt5 import QtWidgets, QtCore

class TestATALDialog(QtWidgets.QDialog):
    # Step timer AT+AL: ora con 100ms, 50ms, 30ms, 25ms
    AT_AL_TIMER_STEPS_MS = [100, 50, 30, 25]

    def __init__(self, parent, ctrl, write_to_excel, update_status, safe_power_off, timer_step_ms=None):
        super().__init__(parent)
        self.ctrl = ctrl
        self.write_to_excel = write_to_excel
        self.update_status = update_status
        self.safe_power_off = safe_power_off
        self.setWindowTitle("Test AT e AL")
        self._at_al_voltage = 88  # AT_AL_START_VOLTAGE
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
        QDialog QLabel#cart_label {
            background-color: white;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            padding: 6px 10px;
            color: #333;
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

    def on_relay_tripped(self, relay_name, voltage=None):
        """Chiamato dal BLE handler quando un relè (AL o AT) scatta.

        relay_name: 'AL' o 'AT'
        voltage:    tensione impostata al momento dello scatto (None = usa valore corrente)
        """
        print(f"[DEBUG][AT+AL] on_relay_tripped: relay={relay_name}, V={voltage}")
        self._record_trip(voltage)

    def _cart1(self):
        """Bottone manuale primo scatto."""
        self._record_trip()

    def _cart2(self):
        """Bottone manuale secondo scatto."""
        self._record_trip()

    def _record_trip(self, voltage=None):
        """Registra uno scatto. Primo → cart1, secondo → cart2 e finalizza.

        voltage: tensione al momento dello scatto. Se None usa self._at_al_voltage.
        """
        v = voltage if voltage is not None else self._at_al_voltage
        if self._at_al_cart1_value is None:
            self._at_al_cart1_value = v
            self.cart1_label.setText(f"Cartellino1: {v} V")
            self.cart2_btn.setEnabled(True)
            print(f"[DEBUG][AT+AL] Primo scatto registrato a {v} V")
        elif self._at_al_cart2_value is None:
            self._at_al_cart2_value = v
            self.cart2_label.setText(f"Cartellino2: {v} V")
            print(f"[DEBUG][AT+AL] Secondo scatto registrato a {v} V")
            self._finalize()

    def _finalize(self):
        """Ferma il timer, salva il valore minimo su Excel e chiude il dialog."""
        if hasattr(self, '_timer') and self._timer.isActive():
            self._timer.stop()
        if self._at_al_cart1_value is None or self._at_al_cart2_value is None:
            return
        min_value = min(self._at_al_cart1_value, self._at_al_cart2_value)
        print(
            f"[DEBUG][AT+AL] Salvo: min={min_value}, "
            f"cart1={self._at_al_cart1_value}, cart2={self._at_al_cart2_value}"
        )
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
        )
        self.update_status("Test AT+AL completato", "ok")
        self.accept()
