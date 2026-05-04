from PyQt5 import QtWidgets, QtCore
from .dialog_style import POPUP_STYLESHEET

class Test100VDialog(QtWidgets.QDialog):
    def __init__(self, parent, ctrl, excel_path_edit, matricola_edit, write_to_excel, update_status, safe_power_off):
        super().__init__(parent)
        self.ctrl = ctrl
        self.excel_path_edit = excel_path_edit
        self.matricola_edit = matricola_edit
        self.write_to_excel = write_to_excel
        self.update_status = update_status
        self.safe_power_off = safe_power_off
        self.setWindowTitle("Prova 100 V")
        self._setup_ui()


    def _setup_ui(self):
        self.setMinimumWidth(500)
        self.setStyleSheet(POPUP_STYLESHEET)
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        instructions = QtWidgets.QLabel(
            "Collegare l'alimentatore con il polo positivo al punto \"T\" (palo) "
            "e il polo negativo al punto \"B\" (binario) e allontanarsi."
        )
        instructions.setObjectName("instructions")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        self.start_btn = QtWidgets.QPushButton("INIZIO TEST")
        self.start_btn.setObjectName("start_btn")
        layout.addWidget(self.start_btn)

        self.result_label = QtWidgets.QLabel("In attesa...")
        self.result_label.setObjectName("voltage_live")
        layout.addWidget(self.result_label)

        self.close_btn = QtWidgets.QPushButton("Chiudi")
        self.close_btn.setObjectName("close_btn")
        layout.addWidget(self.close_btn)
        self.close_btn.clicked.connect(self.reject)

        self.setLayout(layout)
        self.start_btn.clicked.connect(self._start_test)

    def _start_test(self):
        if not self.ctrl:
            QtWidgets.QMessageBox.warning(
                self, "Errore", "Collegare l'alimentatore prima di avviare la prova 100 V."
            )
            return
        self.update_status("Prova 100 V in corso...", "working")
        self.result_label.setText("Test in corso...")
        self.ctrl.set_voltage(100)  # TEST_100V_VOLTAGE
        self.ctrl.set_current(2)    # ISOLATION_CURRENT_A
        self.ctrl.output_on()
        QtCore.QTimer.singleShot(500, self._measure)

    def _measure(self):
        try:
            current = self.ctrl.measure_current()
        except Exception as e:
            self.result_label.setText(f"Errore lettura corrente: {e}")
            self.safe_power_off()
            self.update_status("Prova 100 V — errore lettura", "error")
            return
        if current > 1.9:  # PASS_CURRENT_100V
            self.result_label.setText(
                f"Corrente misurata: {current:.3f} A — TEST SUPERATO"
            )
            summary = (
                f"Prova 100 V\n"
                f"Corrente misurata: {current:.3f} A\n"
                f"Colonne: B=OK, C=POS., D=OK, E=POS."
            )
            self.write_to_excel(
                lambda handler, row: handler.write_100v_results(row, current),
                summary=summary,
                popup_to_close=self
            )
            self.update_status("Prova 100 V superata", "ok")
        else:
            self.result_label.setText(
                f"Corrente misurata: {current:.3f} A — TEST NON SUPERATO (soglia > 1.9 A)"
            )
            self.safe_power_off()
            self.update_status("Prova 100 V NON superata", "error")
        self.accept()
