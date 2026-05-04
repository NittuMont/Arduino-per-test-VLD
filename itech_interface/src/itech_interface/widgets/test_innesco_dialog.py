from PyQt5 import QtWidgets, QtCore

class TestInnescoDialog(QtWidgets.QDialog):
    def __init__(self, parent, ctrl, write_to_excel, update_status, safe_power_off, timer_step_ms=None):
        super().__init__(parent)
        self.ctrl = ctrl
        self.write_to_excel = write_to_excel
        self.update_status = update_status
        self.safe_power_off = safe_power_off
        self.setWindowTitle("Innesco Tiristore")
        self._innesco_voltage = 89  # INNESCO_START_VOLTAGE
        # timer_step_ms: valore scelto dall'utente, default 500ms se non specificato
        self._timer_interval = timer_step_ms if timer_step_ms is not None else 500
        self._diode_delay = 1000    # INNESCO_DIODE_DELAY_MS
        self._diode_offset = 10.55  # INNESCO_DIODE_OFFSET_V
        self._max_voltage = 120     # TEST_MAX_VOLTAGE
        self._history = []
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
        label = QtWidgets.QLabel("Collegare il filo bianco al faston TP2.")
        label.setObjectName("instructions")
        label.setWordWrap(True)
        layout.addWidget(label)
        self.start_btn = QtWidgets.QPushButton("INIZIO TEST")
        self.start_btn.setObjectName("start_btn")
        layout.addWidget(self.start_btn)
        self.voltage_label = QtWidgets.QLabel(f"Tensione applicata: {self._innesco_voltage} V")
        self.voltage_label.setObjectName("voltage_live")
        layout.addWidget(self.voltage_label)
        self.status_label = QtWidgets.QLabel("Test Innesco: Attendere il completamento del test")
        layout.addWidget(self.status_label)
        self.exit_btn = QtWidgets.QPushButton("Esci dal test")
        self.exit_btn.setObjectName("close_btn")
        layout.addWidget(self.exit_btn)
        self.exit_btn.clicked.connect(self.reject)
        self.setLayout(layout)
        self.start_btn.clicked.connect(self._start_test)

    def _start_test(self):
        if not self.ctrl:
            QtWidgets.QMessageBox.warning(
                self, "Errore", "Collegare l'alimentatore prima di avviare il test Innesco Tiristore."
            )
            return
        self.update_status("Test Innesco in corso...", "working")
        self.ctrl.set_voltage(self._innesco_voltage)
        self.ctrl.set_current(2)  # TEST_CURRENT_A
        self.ctrl.output_on()
        self._history = []
        self._running = True
        self._schedule_step()

    def _schedule_step(self):
        """Pianifica il prossimo step con singleShot.

        Usando singleShot invece di un timer repeating, il prossimo step
        viene schedulato DOPO il completamento del precedente (inclusa la
        query SCPI measure_voltage). Cosi' l'intervallo e' rispettato anche
        a valori bassi (10-25 ms) senza rischio di chiamate sovrapposte.
        """
        if self._running:
            QtCore.QTimer.singleShot(self._timer_interval, self._innesco_step)

    def _innesco_step(self):
        if not self._running:
            return
        if self._innesco_voltage >= self._max_voltage:
            self._running = False
            self.ctrl.output_off()
            self.ctrl.local_mode()
            return
        self._innesco_voltage += 1
        self.ctrl.set_voltage(self._innesco_voltage)
        self.voltage_label.setText(f"Tensione applicata: {self._innesco_voltage} V")
        try:
            measured = self.ctrl.measure_voltage()
        except Exception:
            measured = None
        if measured is not None:
            self._history.append(measured)
            if len(self._history) >= 2 and measured < self._history[-2]:
                self._running = False
                highest = max(self._history)
                QtCore.QTimer.singleShot(self._diode_delay, lambda: self._calculate_diode_drop(highest))
                return
        # Schedula il prossimo step solo DOPO aver completato questo
        self._schedule_step()

    def _calculate_diode_drop(self, highest):
        try:
            raw = self.ctrl.measure_voltage()
        except Exception:
            raw = None
        if raw is not None:
            adjusted = raw - self._diode_offset
            summary = (
                f"Innesco Tiristore\n"
                f"Valore massimo raggiunto: {highest} V\n"
                f"Caduta diodo: {adjusted:.2f} V\n"
                f"Colonne: H={adjusted:.2f}, J=POS., "
                f"K={int(round(highest))}, M=OK, N=POS."
            )
            self.write_to_excel(
                lambda handler, row: handler.write_innesco_results(row, round(adjusted, 2), highest),
                summary=summary,
                popup_to_close=self,
            )
            self.update_status("Test Innesco completato", "ok")
        else:
            self.safe_power_off()
            self.status_label.setText(
                f"Valore massimo raggiunto: {highest} V\n"
                "Errore: impossibile leggere la caduta di tensione."
            )
            self.update_status("Test Innesco — errore lettura", "error")
        self.accept()
