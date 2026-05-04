"""GUI implementation using PyQt5."""
from PyQt5 import QtWidgets, QtCore
from .widgets import ExcelGroup, ManualGroup, TestGroup, BleGroup, PSUStatusBar, ResultLabel, BLEStatusBar, AsyncBLEWorker, TestTrackerWidget
from .handlers.ble_handlers import BLEHandlers
import datetime
from .controller import PowerSupplyController
from .excel_handler import ExcelHandler
from .network import ITechConnection

# Thread worker per connessione asincrona alimentatore
class PSUConnectWorker(QtCore.QThread):
    status = QtCore.pyqtSignal(str, object, object)  # status, conn, ctrl
    attempt = QtCore.pyqtSignal(int)  # numero tentativo
    def __init__(self, host):
        super().__init__()
        self.host = host
    def run(self):
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            self.attempt.emit(attempt)
            try:
                conn = ITechConnection(self.host)
                conn.connect()
                ctrl = PowerSupplyController(conn)
                self.status.emit('success', conn, ctrl)
                return
            except Exception:
                pass
        self.status.emit('fail', None, None)

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

# Network
DEFAULT_HOST = "192.168.1.100"
HEARTBEAT_INTERVAL_MS = 10_000  # ms — connection health check interval

# Common test parameters
TEST_MAX_VOLTAGE = 120       # V — upper bound for all three ramps
TEST_CURRENT_A = 2           # A — current limit applied before each ramp

# Anomalia Diodo (AD) test
AD_START_VOLTAGE = 87        # V — voltage at INIZIO TEST
AD_TIMER_INTERVAL_MS = 1000  # ms — ramp step interval

# Anomalia Tiristore e Limiti (AT + AL) test
AT_AL_START_VOLTAGE = 88        # V
AT_AL_TIMER_INTERVAL_MS = 1000  # ms

# Innesco Tiristore test
INNESCO_START_VOLTAGE = 89       # V
INNESCO_TIMER_INTERVAL_MS = 500  # ms — half-second steps
INNESCO_DIODE_DELAY_MS = 1000    # ms — wait after trip before reading diode drop
INNESCO_DIODE_OFFSET_V = 10.55   # V — subtracted from raw reading to get diode drop

# Prove di isolamento (100 V / 500 V)
TEST_100V_VOLTAGE = 100          # V
TEST_500V_VOLTAGE = 500          # V
ISOLATION_CURRENT_A = 2          # A — current limit
ISOLATION_MEASURE_DELAY_MS = 500  # ms — delay before current measurement (100 V)
ISOLATION_500V_DELAY_MS = 1000   # ms — delay before current measurement (500 V)
PASS_CURRENT_100V = 1.9          # A — minimum current for 100 V pass
PASS_CURRENT_500V = 0.005        # A — maximum current for 500 V pass


class BLELogWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log tempi notifica BLE")
        self.resize(600, 400)
        layout = QtWidgets.QVBoxLayout(self)
        self.text_edit = QtWidgets.QPlainTextEdit(self)
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
        close_btn = QtWidgets.QPushButton("Chiudi")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        self.setLayout(layout)
    def set_log(self, log_lines):
        self.text_edit.setPlainText("\n".join(log_lines))


class MainWindow(QtWidgets.QMainWindow):

    def _close_ad_test(self):
        self._close_test('_ad_test_active', '_ad_dialog', self._close_ad_test)

    def _on_ble_connect_clicked(self):
        # Solo gestione BLE, mai ricostruire la GUI qui!
        self.ble_handlers.on_ble_connect_clicked()

    _MAINWINDOW_STYLESHEET = """
        QMainWindow {
            background-color: #f5f6fa;
        }
        QMainWindow * {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 14pt;
        }
        QGroupBox {
            background-color: white;
            border: 1px solid #e0e3eb;
            border-radius: 10px;
            margin-top: 18px;
            padding: 16px 14px 14px 14px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 14px;
            padding: 2px 10px;
            background-color: white;
            border: 1px solid #e0e3eb;
            border-radius: 4px;
            color: #444;
            font-size: 11pt;
            font-weight: bold;
        }
        QLineEdit, QComboBox {
            border: 1px solid #ccd1dc;
            border-radius: 6px;
            padding: 6px 10px;
            background: #fafbfd;
            font-size: 13pt;
            selection-background-color: #0078d4;
        }
        QLineEdit:focus, QComboBox:focus {
            border-color: #0078d4;
        }
        QComboBox::drop-down {
            border: none;
            width: 28px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #555;
            margin-right: 8px;
        }
        QPushButton {
            min-height: 40px;
            padding: 6px 16px;
            background-color: #0078d4;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 13pt;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #106ebe;
        }
        QPushButton:pressed {
            background-color: #005a9e;
        }
        QPushButton:disabled {
            background-color: #d0d4dc;
            color: #8a8a8a;
        }
        QPushButton#quit_btn {
            background-color: #d13438;
            min-height: 36px;
            font-size: 12pt;
        }
        QPushButton#quit_btn:hover {
            background-color: #a4262c;
        }
        QMenuBar {
            background: white;
            border-bottom: 1px solid #e0e3eb;
            font-size: 11pt;
            padding: 2px 0;
        }
        QMenuBar::item:selected {
            background: #e8f0fe;
            border-radius: 4px;
        }
        QMenu {
            background: white;
            border: 1px solid #e0e3eb;
            border-radius: 6px;
            padding: 4px;
        }
        QMenu::item {
            padding: 6px 24px;
            border-radius: 4px;
        }
        QMenu::item:selected {
            background: #e8f0fe;
        }
    """

    def __init__(self):
        super().__init__()
        self.setStyleSheet(self._MAINWINDOW_STYLESHEET)
        self.setWindowTitle("Test dei VLD RFI - Interfaccia Operatore")
        self.ble_handlers = BLEHandlers(self)
        self._setup_ui()
        self.conn = None
        self.ctrl = None
        self._heartbeat_timer = QtCore.QTimer(self)
        self._heartbeat_timer.timeout.connect(self._heartbeat_check)
        self._connection_lost = False
        self._closing = False
        self._psu_attempt = 0
        self._ad_test_active = False
        self._at_al_test_active = False
        self._innesco_test_active = False

    def on_test_anomalia_tiristore_limiti(self):
        """Apre la finestra del test AT+AL (Anomalia Tiristore + Limiti)."""
        self._start_at_al_test()
    def _on_psu_reconnect_clicked(self):
        self._start_psu_connect()

    # ------------------------------------------------------------------
    # Window close – stop all timers and disconnect immediately
    # ------------------------------------------------------------------
    def closeEvent(self, event):           # noqa: N802 (Qt naming)
        """Ensure a clean shutdown: stop timers, kill socket, accept close."""
        self._closing = True

        # Ferma il timer heartbeat
        self._heartbeat_timer.stop()

        # Disconnetti il PSU
        if self.conn is not None:
            try:
                self.conn.disconnect()
            except Exception:
                pass
        self.ctrl = None

        event.accept()       # let Qt close the window



    def _setup_ui(self):
        # Worker BLE (dopo che tutti i riferimenti sono pronti)
        self.ble_worker = AsyncBLEWorker()
        self.ble_worker.devices_found.connect(self.ble_handlers.on_ble_devices_found)
        self.ble_worker.error.connect(self.ble_handlers.on_ble_error)
        self.ble_worker.state_update.connect(self._on_ble_state_update_with_log)
        self.ble_worker.connected.connect(self.ble_handlers.on_ble_connected)
        self.ble_worker.disconnected.connect(self.ble_handlers.on_ble_disconnected)
        self.ble_worker.start()
        self._ble_connected_flag = False
        # Timer dinamici per test
        # AD e AT_AL: 1000ms senza BLE, 100ms con BLE collegato
        # Innesco: fisso a 100ms sempre
        self._ad_timer_interval_ms = AD_TIMER_INTERVAL_MS
        self._at_al_timer_interval_ms = AT_AL_TIMER_INTERVAL_MS
        self._innesco_timer_interval_ms = 100

        # Avvio automatico BLE scan e PSU connect all'avvio
        QtCore.QTimer.singleShot(0, self._start_ble_scan_with_status)
        QtCore.QTimer.singleShot(0, self._start_psu_connect)
        # WARNING: chiamare _setup_ui SOLO dal costruttore!

        # Colonna sinistra (tutto tranne BLE)
        self.left_col = QtWidgets.QVBoxLayout()
        self.left_col.setSpacing(14)

        # Colonna destra (BLE)
        self.right_col = QtWidgets.QVBoxLayout()
        self.right_col.setSpacing(14)

        # Excel
        self.excel_group = ExcelGroup()
        self.left_col.addWidget(self.excel_group)
        self.excel_group.browse_btn.clicked.connect(self._browse_excel)
        self.excel_group.matricola_dec_btn.clicked.connect(self._matricola_decrement)
        self.excel_group.matricola_inc_btn.clicked.connect(self._matricola_increment)
        self.excel_path_edit = self.excel_group.excel_path_edit
        self.matricola_edit = self.excel_group.matricola_edit
        self.matricola_dec_btn = self.excel_group.matricola_dec_btn
        self.matricola_inc_btn = self.excel_group.matricola_inc_btn
        self.excel_path_edit.textChanged.connect(lambda _: self._refresh_tracker())
        self.matricola_edit.textChanged.connect(lambda _: self._refresh_tracker())

        # BLE Monitor
        self.ble_group = BleGroup()
        self.right_col.addWidget(self.ble_group)
        self.ble_scan_btn = self.ble_group.ble_scan_btn
        self.ble_connect_btn = self.ble_group.ble_connect_btn
        self.ble_connect_btn.clicked.connect(self._on_ble_connect_clicked)
        self.ble_bypass_btn = self.ble_group.ble_bypass_btn
        self.ble_device_combo = self.ble_group.ble_device_combo
        self.ble_circuit_labels = self.ble_group.ble_circuit_labels

        # ManualGroup
        self.manual_group = ManualGroup()
        self.right_col.addWidget(self.manual_group)
        self.voltage_100_btn = self.manual_group.voltage_100_btn
        self.voltage_500_btn = self.manual_group.voltage_500_btn
        self.voltage_100_btn.clicked.connect(self.on_test_100v)
        self.voltage_500_btn.clicked.connect(self.on_test_500v)

        # TestGroup
        self.test_group = TestGroup()
        self.right_col.addWidget(self.test_group)
        self.ad_btn = self.test_group.ad_btn
        self.ad_al_btn = self.test_group.ad_al_btn
        self.innesco_btn = self.test_group.innesco_btn
        self.ad_btn.clicked.connect(self.on_test_anomalia_diodo)
        self.ad_al_btn.clicked.connect(self.on_test_anomalia_tiristore_limiti)
        self.innesco_btn.clicked.connect(self.on_test_innesco_tiristore)

        # Crea la label step PRIMA del layout
        self._step_interval_ms = 100  # default
        self._step_interval_label = QtWidgets.QLabel(f"Step: {self._step_interval_ms} ms")
        self._step_interval_label.setStyleSheet(
            "font-weight: bold; font-size: 10pt; color: #0078d4; "
            "background: #e8f0fe; border-radius: 4px; padding: 3px 8px; margin-left: 12px;"
        )

        # --- Barra di stato fissa in alto (unica riga: PSU + BLE + Step) ---
        status_row = QtWidgets.QHBoxLayout()
        status_row.setSpacing(16)
        self.psu_status_bar = PSUStatusBar()
        self.psu_status_bar.reconnect_btn.clicked.connect(self._on_psu_reconnect_clicked)
        status_row.addWidget(self.psu_status_bar)
        self.ble_status_bar = BLEStatusBar()
        self.ble_status_bar.reconnect_btn.clicked.connect(self._on_ble_reconnect_clicked)
        status_row.addWidget(self.ble_status_bar)
        status_row.addWidget(self._step_interval_label)
        status_row.addStretch()

        # Layout verticale globale: status_row + contenuto
        outer_layout = QtWidgets.QVBoxLayout()
        outer_layout.setSpacing(12)
        outer_layout.setContentsMargins(20, 14, 20, 20)
        outer_layout.addLayout(status_row)

        # Layout principale orizzontale (sotto la barra di stato)
        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setSpacing(20)
        outer_layout.addLayout(self.main_layout)

        # BLE Monitor nella colonna destra con dimensioni fisse (no stretch)
        self.ble_group.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )

        # Result label e quit
        self.result_label = ResultLabel()
        self.left_col.addWidget(self.result_label)

        # Tracker stato test
        self.test_tracker = TestTrackerWidget()
        self.left_col.addWidget(self.test_tracker)

        self.left_col.addStretch()

        self.quit_btn = QtWidgets.QPushButton("Esci")
        self.quit_btn.setObjectName("quit_btn")
        self.quit_btn.clicked.connect(self.close)
        self.left_col.addWidget(self.quit_btn)

        # Stretch in fondo alla colonna destra per evitare che i widget si espandano
        self.right_col.addStretch()

        # Unisci colonne nel layout principale
        self.main_layout.addLayout(self.left_col, stretch=3)
        self.main_layout.addLayout(self.right_col, stretch=2)

        # Widget centrale
        central = QtWidgets.QWidget()
        central.setLayout(outer_layout)
        self.setCentralWidget(central)

        # SOLO ORA crea la barra menu impostazioni (dopo il central widget)
        self.menu_bar = self.menuBar()
        settings_menu = self.menu_bar.addMenu("Impostazioni")
        step_menu = settings_menu.addMenu("Tempo step tensione")
        # Azioni step
        self._step_actions = {}
        for ms in [100, 50, 25, 10]:
            action = QtWidgets.QAction(f"{ms} ms", self)
            action.setCheckable(True)
            if ms == self._step_interval_ms:
                action.setChecked(True)
            def make_handler(val):
                return lambda: self._on_step_interval_selected(val)
            action.triggered.connect(make_handler(ms))
            step_menu.addAction(action)
            self._step_actions[ms] = action

        # Log tempi notifica BLE
        self._ble_log = []  # lista di stringhe
        self._ble_log_window = None
        self._log_action = QtWidgets.QAction("Mostra log BLE", self)
        self._log_action.triggered.connect(self._show_ble_log_window)
        settings_menu.addAction(self._log_action)


    def log_ble_notification(self, msg):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self._ble_log.append(f"[{timestamp}] {msg}")
        # Limita la lunghezza del log per evitare overflow
        if len(self._ble_log) > 1000:
            self._ble_log = self._ble_log[-1000:]

    def _show_ble_log_window(self):
        if self._ble_log_window is None:
            self._ble_log_window = BLELogWindow(self)
        self._ble_log_window.set_log(self._ble_log)
        self._ble_log_window.show()

    def _on_step_interval_selected(self, ms):
        for val, action in self._step_actions.items():
            action.setChecked(val == ms)
        self._step_interval_ms = ms
        self._step_interval_label.setText(f"Step: {ms} ms")
        self._ad_timer_interval_ms = ms
        self._at_al_timer_interval_ms = ms
        # innesco è fisso a 100 ms indipendentemente dalla selezione

    def _on_ble_state_update_with_log(self, *args, **kwargs):
        # Logga il tempo di ricezione della notifica BLE
        self.log_ble_notification("Notifica BLE ricevuta: " + str(args))
        # Chiama il gestore originale
        self.ble_handlers.on_ble_state_update(*args, **kwargs)

    def _start_ble_scan_with_status(self):
        self.ble_status_bar.set_status('connecting')
        self.ble_worker.scan_ble()
    def _on_ble_reconnect_clicked(self):
        self.ble_handlers.on_ble_reconnect_clicked()

    def _start_psu_connect(self):
        if hasattr(self, '_psu_worker') and self._psu_worker is not None and self._psu_worker.isRunning():
            return
        self._psu_attempt = 0
        self._set_psu_status('connecting')
        self._update_psu_attempts()
        self._psu_worker = PSUConnectWorker(DEFAULT_HOST)
        self._psu_worker.status.connect(self._on_psu_connect_status)
        self._psu_worker.attempt.connect(self._on_psu_attempt)
        self._psu_worker.start()

    def _on_psu_attempt(self, attempt):
        self._psu_attempt = attempt
        self._update_psu_attempts()

    def _set_psu_status(self, state):
        self.psu_status_bar.set_status(state)

    def _update_psu_attempts(self):
        self.psu_status_bar.set_attempts(self._psu_attempt)

    def _on_psu_connect_status(self, status, conn, ctrl):
        if status == 'success':
            self.conn = conn
            self.ctrl = ctrl
            self._connection_lost = False
            self._set_psu_status('ok')
            self._update_status("Pronto", "ok")
            self._heartbeat_timer.start(HEARTBEAT_INTERVAL_MS)
        else:
            if self._psu_attempt < 3:
                self._set_psu_status('connecting')
            else:
                self._set_psu_status('fail')
            self._connection_lost = True
            self._update_status("Errore: impossibile connettersi all'alimentatore", "error")
            self._heartbeat_timer.start(HEARTBEAT_INTERVAL_MS)

    def _heartbeat_check(self):
        """Periodic check: verify the connection is alive.

        If the connection is lost (e.g. after PC hibernation), attempt
        to reconnect automatically and update the status bar.
        """
        if self._closing or self.conn is None:
            return
        try:
            alive = self.conn.ping()
        except Exception:
            alive = False

        if alive:
            if self._connection_lost:
                # Connection was lost and is now restored
                self._connection_lost = False
                self.ctrl = PowerSupplyController(self.conn)
                self._update_status("Connessione ripristinata", "ok")
        else:
            # Connection is dead — attempt reconnection
            self._connection_lost = True
            self._update_status("Connessione persa — riconnessione...", "working")
            try:
                self.conn.reconnect()
                self.ctrl = PowerSupplyController(self.conn)
                self._connection_lost = False
                self._update_status("Connessione ripristinata", "ok")
            except Exception:
                self.ctrl = None
                self._update_status(
                    "Connessione persa — riprovo tra "
                    f"{HEARTBEAT_INTERVAL_MS // 1000}s",
                    "error",
                )

    def _browse_excel(self):
        """Open a file dialog to select the Excel workbook."""
        import os
        default_dir = r"Y:\Projects\Produzione\9453 - VLD RFI"
        if not os.path.isdir(default_dir):
            default_dir = "C:\\"
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Seleziona file Excel", default_dir,
            "File Excel (*.xlsx *.xls);;Tutti i file (*)"
        )
        if path:
            self.excel_path_edit.setText(path)

    def _matricola_increment(self):
        """Increase the matricola number by 1."""
        text = self.matricola_edit.text().strip()
        try:
            value = int(text)
        except (ValueError, TypeError):
            value = 0
        self.matricola_edit.setText(str(value + 1))

    def _matricola_decrement(self):
        """Decrease the matricola number by 1 (minimum 0)."""
        text = self.matricola_edit.text().strip()
        try:
            value = int(text)
        except (ValueError, TypeError):
            value = 1
        self.matricola_edit.setText(str(max(0, value - 1)))

    def _update_status(self, text: str, level: str = "info"):
        self.result_label.set_status(text, level)

    def _refresh_tracker(self):
        """Rilegge l'Excel e aggiorna il tracker per la matricola corrente."""
        excel_path = self.excel_path_edit.text()
        matricola  = self.matricola_edit.text().strip()
        if not excel_path or not matricola:
            self.test_tracker.set_unknown()
            return
        try:
            handler = ExcelHandler(excel_path)
            row = handler.find_row_by_matricola(matricola)
            if row is None:
                handler.close()
                self.test_tracker.set_unknown()
                return
            status = handler.get_test_status(row)
            handler.close()
            self.test_tracker.update_status(status)
        except Exception:
            self.test_tracker.set_unknown()

    def _safe_power_off(self):
        """Turn off power supply output and switch to local mode.

        Called as a safety fallback whenever a test finishes (success or
        failure) to guarantee the operator is never exposed to live voltage
        when a test is not actively running.
        """
        if self.ctrl:
            try:
                self.ctrl.output_off()
            except Exception:
                pass
            try:
                self.ctrl.local_mode()
            except Exception:
                pass
        # Test terminato — riattiviamo il controllo connessione
        self._resume_heartbeat()

    def _pause_heartbeat(self):
        """Stop the heartbeat timer during active tests.

        While a test is running, the device is busy executing SCPI commands;
        sending a blocking ``*IDN?`` query from the heartbeat would freeze
        the GUI until the device responds (up to the socket timeout).
        """
        self._heartbeat_timer.stop()

    def _resume_heartbeat(self):
        """Restart the heartbeat timer after a test completes."""
        if not self._heartbeat_timer.isActive():
            self._heartbeat_timer.start(HEARTBEAT_INTERVAL_MS)

    def _write_to_excel(self, write_func, summary="", popup_to_close=None,
                        next_test_label=None, next_test_callback=None):
        """Validate inputs, open the workbook, find the matricola row,
        call *write_func(handler, row)* and show success/error dialogs.

        *summary*            — human-readable description of written data.
        *popup_to_close*     — QDialog to close automatically when the test is finished.
        *next_test_label*    — label for the "Prosegui" button (None = no button).
        *next_test_callback* — callable invoked when the user clicks "Prosegui".
        """
        # --- Spegnimento immediato: il test è terminato ---
        self._safe_power_off()

        # --- Chiudi il popup del test: il test è finito ---
        if popup_to_close is not None:
            try:
                popup_to_close.close()
            except Exception:
                pass

        excel_path = self.excel_path_edit.text()
        matricola = self.matricola_edit.text().strip()

        if not excel_path:
            QtWidgets.QMessageBox.warning(
                self, "Attenzione", "Nessun file Excel selezionato."
            )
            return
        if not matricola:
            QtWidgets.QMessageBox.warning(
                self, "Attenzione", "Inserire una matricola."
            )
            return

        try:
            handler = ExcelHandler(excel_path)
            row = handler.find_row_by_matricola(matricola)
            if row is None:
                handler.close()
                QtWidgets.QMessageBox.warning(
                    self, "Errore",
                    f"Matricola '{matricola}' non trovata "
                    f"nella colonna A del file Excel."
                )
                return

            errors = write_func(handler, row)
            handler.close()

            if errors:
                QtWidgets.QMessageBox.warning(
                    self, "Errore — valori fuori range",
                    "\n".join(errors)
                )
            else:
                self._refresh_tracker()
                msg = "Dati salvati correttamente nel file Excel."
                if summary:
                    msg += f"\n\n{summary}"
                # Dialog con pulsante "Prosegui" opzionale
                dlg = QtWidgets.QDialog(self)
                dlg.setWindowTitle("Salvataggio completato")
                vbox = QtWidgets.QVBoxLayout(dlg)
                vbox.setContentsMargins(20, 20, 20, 20)
                vbox.setSpacing(12)
                lbl = QtWidgets.QLabel(msg)
                lbl.setWordWrap(True)
                vbox.addWidget(lbl)
                btn_row = QtWidgets.QHBoxLayout()
                ok_btn = QtWidgets.QPushButton("OK")
                ok_btn.clicked.connect(dlg.accept)
                btn_row.addWidget(ok_btn)
                if next_test_label and next_test_callback:
                    next_btn = QtWidgets.QPushButton(next_test_label)
                    next_btn.setDefault(True)
                    next_btn.setAutoDefault(True)
                    next_btn.clicked.connect(dlg.accept)
                    next_btn.clicked.connect(next_test_callback)
                    btn_row.addWidget(next_btn)
                    next_btn.setFocus()
                else:
                    ok_btn.setDefault(True)
                    ok_btn.setFocus()
                vbox.addLayout(btn_row)
                dlg.exec_()
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Errore",
                f"Errore durante la scrittura del file Excel:\n{e}"
            )

    def _stop_existing_timer(self, attr_name: str):
        """Ferma e cancella un QTimer salvato in attr_name, se esiste."""
        timer = getattr(self, attr_name, None)
        if timer is not None:
            timer.stop()
            timer.deleteLater()
            setattr(self, attr_name, None)

    # ==================================================================
    # Prova 100 V
    # ==================================================================

    def on_test_100v(self):
        from .widgets.test_100v_dialog import Test100VDialog
        Test100VDialog(
            self, self.ctrl,
            self._write_to_excel, self._update_status, self._safe_power_off,
        ).exec_()

    # ==================================================================
    # Prova 500 V
    # ==================================================================

    def on_test_500v(self):
        from .widgets.test_500v_dialog import Test500VDialog
        Test500VDialog(
            self, self.ctrl,
            self._write_to_excel, self._update_status, self._safe_power_off,
        ).exec_()

    # ------------------------------------------------------------------
    # Helper condiviso: ferma tutti i test prima di avviarne uno nuovo
    # ------------------------------------------------------------------

    def _stop_all_tests(self):
        """Resetta tutti i flag test, ferma i timer e spegne l'uscita PSU."""
        self._ad_test_active = False
        self._at_al_test_active = False
        self._innesco_test_active = False
        self.ble_handlers.reset_all_relay_timers_and_flags()
        self._safe_power_off()

    def _close_test(self, flag_attr, dialog_attr, finished_handler):
        """Cleanup generico per qualsiasi test dialog-based.

        1. Resetta il flag attivo del test.
        2. Ferma tutti i timer anomalia BLE.
        3. Spegne il PSU.
        4. Chiude la dialog se ancora aperta.
        5. Aggiorna la status bar.
        """
        setattr(self, flag_attr, False)
        self.ble_handlers.reset_all_relay_timers_and_flags()
        self._safe_power_off()
        dlg = getattr(self, dialog_attr, None)
        if dlg is not None:
            try:
                dlg.finished.disconnect(finished_handler)
            except (TypeError, RuntimeError):
                pass
            try:
                dlg.close()
            except Exception:
                pass
            setattr(self, dialog_attr, None)
        self._update_status("Pronto", "ok")

    def on_test_anomalia_diodo(self):
        """Apre la finestra del test Anomalia Diodo (AD)."""
        self._stop_all_tests()
        self._start_ad_test()

    def _start_ad_test(self):
        from .widgets.test_ad_dialog import TestADDialog
        self._ad_dialog = TestADDialog(
            self,
            self.ctrl,
            self._write_to_excel,
            self._update_status,
            self._safe_power_off,
            timer_step_ms=self._ad_timer_interval_ms,
            next_test_callback=self._start_at_al_test,
        )
        self._ad_test_active = True
        self._ad_dialog.finished.connect(self._close_ad_test)
        self._ad_dialog.exec_()
        self._ad_dialog = None
    def _close_innesco_test(self):
        self._close_test('_innesco_test_active', '_innesco_dialog', self._close_innesco_test)

    def _start_at_al_test(self):
        self._stop_all_tests()
        from .widgets.test_atal_dialog import TestATALDialog
        self._at_al_dialog = TestATALDialog(
            self,
            self.ctrl,
            self._write_to_excel,
            self._update_status,
            self._safe_power_off,
            timer_step_ms=self._at_al_timer_interval_ms,
            next_test_callback=self.on_test_innesco_tiristore,
        )
        self._at_al_test_active = True
        self._at_al_dialog.finished.connect(self._close_at_al_test)
        self._at_al_dialog.exec_()
        self._at_al_dialog = None

    def _close_at_al_test(self):
        self._close_test('_at_al_test_active', '_at_al_dialog', self._close_at_al_test)

    def on_test_innesco_tiristore(self):
        """Apre la finestra del test Innesco Tiristore."""
        self._stop_all_tests()
        from .widgets.test_innesco_dialog import TestInnescoDialog
        self._innesco_dialog = TestInnescoDialog(
            self,
            self.ctrl,
            self._write_to_excel,
            self._update_status,
            self._safe_power_off,
            timer_step_ms=self._innesco_timer_interval_ms
        )
        self._innesco_test_active = True
        self._innesco_dialog.finished.connect(self._close_innesco_test)
        self._innesco_dialog.exec_()
        self._innesco_dialog = None
