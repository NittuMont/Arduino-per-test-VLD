
"""GUI implementation using PyQt5."""
from PyQt5 import QtWidgets, QtCore
from .widgets import ExcelGroup, ManualGroup, TestGroup, BleGroup, PSUStatusBar, ResultLabel, BLEStatusBar, AsyncBLEWorker
from .handlers.ble_handlers import BLEHandlers
import time
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
        print(f"[DEBUG][PSUConnectWorker] run() avviato per host {self.host}")
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            self.attempt.emit(attempt)
            print(f"[DEBUG][PSUConnectWorker] Tentativo {attempt} di connessione...")
            try:
                conn = ITechConnection(self.host)
                print("[DEBUG][PSUConnectWorker] ITechConnection creato")
                conn.connect()
                print("[DEBUG][PSUConnectWorker] conn.connect() OK")
                ctrl = PowerSupplyController(conn)
                print("[DEBUG][PSUConnectWorker] PowerSupplyController creato")
                self.status.emit('success', conn, ctrl)
                print("[DEBUG][PSUConnectWorker] status.emit('success', ...) inviato")
                return
            except Exception as e:
                print(f"[DEBUG][PSUConnectWorker] Eccezione al tentativo {attempt}: {e}")
        self.status.emit('fail', None, None)
        print("[DEBUG][PSUConnectWorker] status.emit('fail', ...) inviato dopo 3 tentativi")

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

class MeasurementWorker(QtCore.QThread):
    """Background thread to perform voltage measurement only.

    The signal includes voltage and elapsed seconds for the query operation.
    """
    result = QtCore.pyqtSignal(float, float)

    def __init__(self, controller: PowerSupplyController):
        super().__init__()
        self.ctrl = controller

    def run(self):
        # perform voltage query only
        start = time.monotonic()
        v = self.ctrl.measure_voltage()
        elapsed = time.monotonic() - start
        self.result.emit(v, elapsed)


class MainWindow(QtWidgets.QMainWindow):
    AT_AL_TIMER_INTERVAL_MS = 1000  # ms
    INNESCO_TIMER_INTERVAL_MS = 500  # ms
    AD_TIMER_INTERVAL_MS = 1000  # Imposta qui il valore di default desiderato

    def _on_ble_connect_clicked(self):
        # Solo gestione BLE, mai ricostruire la GUI qui!
        self.ble_handlers.on_ble_connect_clicked()

    _MAINWINDOW_STYLESHEET = """
        QMainWindow {
            background-color: #f0f2f5;
        }
        QMainWindow * {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 15pt;
        }
        QPushButton {
            min-height: 46px;
            padding: 8px 18px;
            background-color: #0078d4;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 15pt;
        }
        QPushButton:hover {
            background-color: #106ebe;
        }
        QPushButton:pressed {
            background-color: #005a9e;
        }
        QPushButton:disabled {
            background-color: #b0b0b0;
            color: #e0e0e0;
        }
        QPushButton#quit_btn {
            background-color: #d13438;
        }
        QPushButton#quit_btn:hover {
            background-color: #a4262c;
        }
    """

    def __init__(self):
        print("[DEBUG] Costruttore MainWindow chiamato")
        super().__init__()
        # Applica subito lo stylesheet globale (restaurato stile originale)
        self.setStyleSheet(self._MAINWINDOW_STYLESHEET)
        self.setWindowTitle("Test dei VLD RFI - Interfaccia Operatore")
        # Handler BLE (deve essere pronto prima di _setup_ui)
        self.ble_handlers = BLEHandlers(self)
        # CHIAMARE _setup_ui SOLO QUI! Mai da handler/eventi!
        self._setup_ui()
        print("[DEBUG] _setup_ui() ok")
        self.conn = None
        self.ctrl = None
        self._measure_worker = None
        self._heartbeat_timer = QtCore.QTimer(self)
        self._heartbeat_timer.timeout.connect(self._heartbeat_check)
        self._connection_lost = False
        self._closing = False
        self._psu_attempt = 0

    def _on_psu_reconnect_clicked(self):
        self._start_psu_connect()


    # ------------------------------------------------------------------
    # Window close – stop all timers and disconnect immediately
    # ------------------------------------------------------------------
    def closeEvent(self, event):           # noqa: N802 (Qt naming)
        """Ensure a clean shutdown: stop timers, kill socket, accept close."""
        self._closing = True

        # 1. Stop every timer that might trigger network I/O
        self._heartbeat_timer.stop()
        for attr in ("_ad_timer", "_at_al_timer", "_innesco_timer"):
            self._stop_existing_timer(attr)
        self._innesco_running = False

        # 2. Disconnect without blocking (just close the raw socket)
        if self.conn is not None:
            try:
                self.conn.disconnect()
            except Exception:
                pass
        self.ctrl = None

        event.accept()       # let Qt close the window



    def _setup_ui(self):
        # WARNING: Questa funzione DEVE essere chiamata SOLO dal costruttore!
        # NON chiamare mai _setup_ui dopo la creazione della finestra!

        # Layout principale orizzontale
        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setSpacing(24)
        self.main_layout.setContentsMargins(24, 24, 24, 24)

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

        # ManualGroup
        self.manual_group = ManualGroup()
        self.left_col.addWidget(self.manual_group)
        self.voltage_100_btn = self.manual_group.voltage_100_btn
        self.voltage_500_btn = self.manual_group.voltage_500_btn
        self.voltage_100_btn.clicked.connect(self.on_test_100v)
        self.voltage_500_btn.clicked.connect(self.on_test_500v)

        # TestGroup
        self.test_group = TestGroup()
        self.left_col.addWidget(self.test_group)
        self.ad_btn = self.test_group.ad_btn
        self.ad_al_btn = self.test_group.ad_al_btn
        self.innesco_btn = self.test_group.innesco_btn
        self.ad_btn.clicked.connect(self.on_test_anomalia_diodo)
        self.ad_al_btn.clicked.connect(self.on_test_anomalia_tiristore_limiti)
        self.innesco_btn.clicked.connect(self.on_test_innesco_tiristore)

        # BLE Monitor
        self.ble_group = BleGroup()
        self.right_col.addWidget(self.ble_group)
        self.ble_scan_btn = self.ble_group.ble_scan_btn
        self.ble_connect_btn = self.ble_group.ble_connect_btn
        self.ble_connect_btn.clicked.connect(self._on_ble_connect_clicked)
        self.ble_bypass_btn = self.ble_group.ble_bypass_btn
        self.ble_device_combo = self.ble_group.ble_device_combo
        self.ble_circuit_labels = self.ble_group.ble_circuit_labels

        # Barra di stato alimentatore e BLE (in alto)
        status_bars = QtWidgets.QHBoxLayout()
        self.psu_status_bar = PSUStatusBar()
        self.psu_status_bar.reconnect_btn.clicked.connect(self._on_psu_reconnect_clicked)
        status_bars.addWidget(self.psu_status_bar)
        self.ble_status_bar = BLEStatusBar()
        self.ble_status_bar.reconnect_btn.clicked.connect(self._on_ble_reconnect_clicked)
        status_bars.addWidget(self.ble_status_bar)
        status_bars.addStretch()
        self.left_col.insertLayout(0, status_bars)

        # Result label e quit
        self.result_label = ResultLabel()
        self.left_col.addWidget(self.result_label)
        self.left_col.addStretch()
        self.quit_btn = QtWidgets.QPushButton("Esci")
        self.quit_btn.setObjectName("quit_btn")
        self.quit_btn.clicked.connect(self.close)
        self.left_col.addWidget(self.quit_btn)

        # Unisci colonne nel layout principale
        self.main_layout.addLayout(self.left_col, stretch=3)
        self.main_layout.addLayout(self.right_col, stretch=2)

        # Widget centrale
        central = QtWidgets.QWidget()
        central.setLayout(self.main_layout)
        self.setCentralWidget(central)

        # Worker BLE (dopo che tutti i riferimenti sono pronti)
        self.ble_worker = AsyncBLEWorker()
        self.ble_worker.devices_found.connect(self.ble_handlers.on_ble_devices_found)
        self.ble_worker.error.connect(self.ble_handlers.on_ble_error)
        self.ble_worker.state_update.connect(self.ble_handlers.on_ble_state_update)
        self.ble_worker.connected.connect(self.ble_handlers.on_ble_connected)
        self.ble_worker.disconnected.connect(self.ble_handlers.on_ble_disconnected)
        self.ble_worker.start()
        self._ble_connected_flag = False
        # Timer dinamici per test (default = 100%)
        self._ad_timer_interval_ms = AD_TIMER_INTERVAL_MS
        self._at_al_timer_interval_ms = AT_AL_TIMER_INTERVAL_MS
        self._innesco_timer_interval_ms = INNESCO_TIMER_INTERVAL_MS

        # Avvio parallelo BLE scan e PSU connect appena la GUI è pronta
        def _start_auto_connects():
            print("[DEBUG] Avvio parallelo: ble_worker.scan_ble e _start_psu_connect")
            self._start_ble_scan_with_status()
            self._start_psu_connect()
        QtCore.QTimer.singleShot(0, _start_auto_connects)

    def _start_ble_scan_with_status(self):
        self.ble_status_bar.set_status('connecting')
        self.ble_worker.scan_ble()
    def _on_ble_reconnect_clicked(self):
        # Solo gestione BLE, mai ricostruire la GUI qui!
        self.ble_handlers.on_ble_reconnect_clicked()
        print("[DEBUG] QTimer.singleShot(0, self._start_psu_connect) chiamato")

        # ----------------------------------------------------------------
        # [VISUAL] Global stylesheet — può essere rimosso/modificato per
        # tornare allo stile di default Qt.
        # ----------------------------------------------------------------

        # [VISUAL] Dimensione minima finestra
        self.setMinimumWidth(700)




    def on_measure(self):
        # retained for possible future use but no UI button triggers it
        if not self.ctrl:
            return
        # disable button to prevent multiple concurrent requests
        self.measure_btn.setEnabled(False)
        self.result_label.setText("Measuring...")
        # start background thread
        self._measure_worker = MeasurementWorker(self.ctrl)
        self._measure_worker.result.connect(self._on_measure_complete)
        self._measure_worker.start()

    def _update_status(self, text: str, level: str = "info"):
        self.result_label.set_status(text, level)

    def _start_psu_connect(self):
        print("[DEBUG] _start_psu_connect() chiamato")
        if hasattr(self, '_psu_worker') and self._psu_worker is not None and self._psu_worker.isRunning():
            print("[DEBUG] Worker già in esecuzione, skip.")
            return
        print("[DEBUG] Creo e avvio PSUConnectWorker...")
        self._psu_attempt = 0
        self._set_psu_status('connecting')
        self._update_psu_attempts()
        self._psu_worker = PSUConnectWorker(DEFAULT_HOST)
        self._psu_worker.status.connect(self._on_psu_connect_status)
        self._psu_worker.attempt.connect(self._on_psu_attempt)
        self._psu_worker.start()
        print("[DEBUG] PSUConnectWorker avviato.")

    def _on_psu_attempt(self, attempt):
        self._psu_attempt = attempt
        self._update_psu_attempts()

    def _set_psu_status(self, state):
        self.psu_status_bar.set_status(state)

    def _update_psu_attempts(self):
        self.psu_status_bar.set_attempts(self._psu_attempt)

    def _on_psu_connect_status(self, status, conn, ctrl):
        print(f"[DEBUG] _on_psu_connect_status(status={status}, conn={conn}, ctrl={ctrl})")
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

    def _write_to_excel(self, write_func, summary="", popup_to_close=None):
        """Validate inputs, open the workbook, find the matricola row,
        call *write_func(handler, row)* and show success/error dialogs.

        *summary*          — human-readable description of written data,
                             shown in the success dialog.
        *popup_to_close*   — QDialog to close automatically when the test
                             is finished (regardless of write outcome).

        The power supply is always switched off at the beginning of this
        method because any caller has already completed its measurement;
        keeping it on while writing / showing dialogs is a safety risk.
        """
        # --- Spegnimento immediato: il test è terminato ---
        self._safe_power_off()

        # --- Chiudi il popup del test: il test è finito ---
        if popup_to_close is not None:
            self._close_popup_safely(popup_to_close)

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
                msg = "Dati salvati correttamente nel file Excel."
                if summary:
                    msg += f"\n\n{summary}"
                QtWidgets.QMessageBox.information(
                    self, "Salvataggio completato", msg
                )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Errore",
                f"Errore durante la scrittura del file Excel:\n{e}"
            )

    # placeholders for future test routines
    def _stop_existing_timer(self, attr_name: str):
        """Stop and delete a QTimer stored in *attr_name* if it exists."""
        timer = getattr(self, attr_name, None)
        if timer is not None:
            timer.stop()
            timer.deleteLater()
            setattr(self, attr_name, None)

    def _close_popup_safely(self, popup):
        """Disconnect the finished signal and close a test popup."""
        if popup is None:
            return
        # Disconnect finished signal to prevent double-cleanup
        for handler in (
            self._close_100v_test, self._close_500v_test,
            self._close_ad_test, self._close_at_al_test,
        ):
            try:
                popup.finished.disconnect(handler)
            except (TypeError, RuntimeError):
                pass
        popup.close()
        # Null out known popup attributes
        for attr in ('_100v_popup', '_500v_popup', '_ad_popup',
                     '_at_al_popup', '_innesco_popup'):
            if getattr(self, attr, None) is popup:
                setattr(self, attr, None)

    # ==================================================================
    # Prova 100 V
    # ==================================================================

    def on_test_100v(self):
        from .widgets.test_100v_dialog import Test100VDialog
        dlg = Test100VDialog(
            self,
            self.ctrl,
            self.excel_path_edit,
            self.matricola_edit,
            self._write_to_excel,
            self._update_status,
            self._safe_power_off
        )
        dlg.exec_()

    def _close_100v_test(self):
        """Clean up 100 V test: turn off output, close popup."""
        if self.ctrl:
            try:
                self.ctrl.output_off()
            except Exception:
                pass
            try:
                self.ctrl.local_mode()
            except Exception:
                pass
        if hasattr(self, '_100v_popup') and self._100v_popup is not None:
            try:
                self._100v_popup.finished.disconnect(self._close_100v_test)
            except (TypeError, RuntimeError):
                pass
            self._100v_popup.close()
            self._100v_popup = None
        self._update_status("Pronto", "ok")

    def _start_100v_test(self):
        """Set 100 V, output on, then measure current after delay."""
        if not self.ctrl:
            QtWidgets.QMessageBox.warning(
                self, "Errore", "Collegare l'alimentatore prima di avviare la prova 100 V."
            )
            return
        self._pause_heartbeat()
        self._update_status("Prova 100 V in corso...", "working")
        self._100v_result_label.setText("Test in corso...")
        self.ctrl.set_voltage(TEST_100V_VOLTAGE)
        self.ctrl.set_current(ISOLATION_CURRENT_A)
        self.ctrl.output_on()
        # Wait before reading current
        QtCore.QTimer.singleShot(
            ISOLATION_MEASURE_DELAY_MS, self._measure_100v
        )

    def _measure_100v(self):
        """Read current and evaluate 100 V test result."""
        if not hasattr(self, '_100v_popup') or self._100v_popup is None:
            return  # popup was closed / test aborted
        try:
            current = self.ctrl.measure_current()
        except Exception as e:
            self._100v_result_label.setText(f"Errore lettura corrente: {e}")
            self._safe_power_off()
            self._update_status("Prova 100 V — errore lettura", "error")
            return

        if current > PASS_CURRENT_100V:
            self._100v_result_label.setText(
                f"Corrente misurata: {current:.3f} A — TEST SUPERATO"
            )
            summary = (
                f"Prova 100 V\n"
                f"Corrente misurata: {current:.3f} A\n"
                f"Colonne: B=OK, C=POS., D=OK, E=POS."
            )
            self._write_to_excel(
                lambda handler, row: handler.write_100v_results(row, current),
                summary=summary,
                popup_to_close=getattr(self, '_100v_popup', None),
            )
            self._update_status("Prova 100 V superata", "ok")
        else:
            self._100v_result_label.setText(
                f"Corrente misurata: {current:.3f} A — TEST NON SUPERATO "
                f"(soglia > {PASS_CURRENT_100V} A)"
            )
            self._safe_power_off()
            self._update_status("Prova 100 V NON superata", "error")

    # ==================================================================
    # Prova 500 V
    # ==================================================================

    def on_test_500v(self):
        from .widgets.test_500v_dialog import Test500VDialog
        dlg = Test500VDialog(
            self,
            self.ctrl,
            self.excel_path_edit,
            self.matricola_edit,
            self._write_to_excel,
            self._update_status,
            self._safe_power_off
        )
        dlg.exec_()

    def _close_500v_test(self):
        """Clean up 500 V test: turn off output, close popup."""
        if self.ctrl:
            try:
                self.ctrl.output_off()
            except Exception:
                pass
            try:
                self.ctrl.local_mode()
            except Exception:
                pass
        if hasattr(self, '_500v_popup') and self._500v_popup is not None:
            try:
                self._500v_popup.finished.disconnect(self._close_500v_test)
            except (TypeError, RuntimeError):
                pass
            self._500v_popup.close()
            self._500v_popup = None
        self._update_status("Pronto", "ok")

    def _start_500v_test(self):
        """Set 500 V, output on, then measure current after delay."""
        if not self.ctrl:
            QtWidgets.QMessageBox.warning(
                self, "Errore", "Collegare l'alimentatore prima di avviare la prova 500 V."
            )
            return
        self._pause_heartbeat()
        self._update_status("Prova 500 V in corso...", "working")
        self._500v_result_label.setText("Test in corso...")
        self.ctrl.set_voltage(TEST_500V_VOLTAGE)
        self.ctrl.set_current(ISOLATION_CURRENT_A)
        self.ctrl.output_on()
        # Wait before reading current
        QtCore.QTimer.singleShot(
            ISOLATION_500V_DELAY_MS, self._measure_500v
        )

    def _measure_500v(self):
        """Read current and evaluate 500 V test result."""
        if not hasattr(self, '_500v_popup') or self._500v_popup is None:
            return  # popup was closed / test aborted
        try:
            current = self.ctrl.measure_current()
        except Exception as e:
            self._500v_result_label.setText(f"Errore lettura corrente: {e}")
            self._safe_power_off()
            self._update_status("Prova 500 V — errore lettura", "error")
            return

        if current <= PASS_CURRENT_500V:
            self._500v_result_label.setText(
                f"Corrente misurata: {current:.3f} A — TEST SUPERATO"
            )
            summary = (
                f"Prova 500 V\n"
                f"Corrente misurata: {current:.3f} A\n"
                f"Colonne: F=OK, G=POS."
            )
            self._write_to_excel(
                lambda handler, row: handler.write_500v_results(row, current),
                summary=summary,
                popup_to_close=getattr(self, '_500v_popup', None),
            )
            self._update_status("Prova 500 V superata", "ok")
        else:
            self._500v_result_label.setText(
                f"Corrente misurata: {current:.3f} A — Problema al Tiristore"
            )
            self._safe_power_off()
            self._update_status("Prova 500 V — Problema al Tiristore", "error")

    # [VISUAL] Stile condiviso per tutti i popup di test.
    # Rimuovere questo metodo (e le relative chiamate) per tornare
    # allo stile di default Qt.
    _POPUP_STYLESHEET = """
        /* [VISUAL] Sfondo popup */
        QDialog {
            background-color: #f0f2f5;
        }
        /* [VISUAL] Font popup */
        QDialog * {
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 15pt;
        }
        /* [VISUAL] Pulsanti standard nel popup */
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
        /* [VISUAL] Pulsante INIZIO TEST — verde */
        QDialog QPushButton#start_btn {
            background-color: #107c10;
            font-weight: bold;
        }
        QDialog QPushButton#start_btn:hover {
            background-color: #0b6a0b;
        }
        /* [VISUAL] Pulsante Chiudi / Esci — rosso */
        QDialog QPushButton#close_btn {
            background-color: #d13438;
        }
        QDialog QPushButton#close_btn:hover {
            background-color: #a4262c;
        }
        /* [VISUAL] Pulsanti cartellino — doppia altezza */
        QDialog QPushButton#cart_btn {
            min-height: 92px;
        }
        /* [VISUAL] Label istruzioni */
        QDialog QLabel#instructions {
            background-color: #e8f4fd;
            border: 1px solid #b3d7f0;
            border-radius: 6px;
            padding: 12px;
            color: #004578;
            font-size: 14pt;
        }
        /* [VISUAL] Label tensione live */
        QDialog QLabel#voltage_live {
            background-color: #fff4ce;
            border: 1px solid #f0d060;
            border-radius: 6px;
            padding: 10px;
            font-size: 16pt;
            font-weight: bold;
            color: #8a6d00;
        }
        /* [VISUAL] Label risultato cartellino */
        QDialog QLabel#cart_label {
            background-color: white;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            padding: 6px 10px;
            color: #333;
        }
        /* [VISUAL] Labels generiche nel popup */
        QDialog QLabel {
            padding: 4px 0px;
            color: #333;
        }
    """

    def _style_popup(self, popup: QtWidgets.QDialog, min_width: int = 550):
        """[VISUAL] Apply professional styling to a test popup."""
        popup.setStyleSheet(self._POPUP_STYLESHEET)
        popup.setMinimumWidth(min_width)

    def on_test_anomalia_diodo(self):
        from .widgets.test_ad_dialog import TestADDialog
        dlg = TestADDialog(
            self,
            self.ctrl,
            self._write_to_excel,
            self._update_status,
            self._safe_power_off
        )
        dlg.exec_()

    def _close_ad_test(self):
        """Clean up AD test: stop timer, turn off output, close popup."""
        self._stop_existing_timer('_ad_timer')
        if self.ctrl:
            try:
                self.ctrl.output_off()
            except Exception:
                pass
            try:
                self.ctrl.local_mode()
            except Exception:
                pass
        if hasattr(self, '_ad_popup') and self._ad_popup is not None:
            # Disconnect finished signal to prevent double cleanup
            try:
                self._ad_popup.finished.disconnect(self._close_ad_test)
            except (TypeError, RuntimeError):
                pass
            self._ad_popup.close()
            self._ad_popup = None
        self._update_status("Pronto", "ok")

    def _start_ad_test(self):
        # start the AD test sequence
        if not self.ctrl:
            QtWidgets.QMessageBox.warning(
                self, "Errore", "Collegare l'alimentatore prima di avviare il test Anomalia Diodo (AD)."
            )
            return
        # Stop any leftover timer from a previous run
        self._stop_existing_timer('_ad_timer')
        self._pause_heartbeat()
        self._update_status("Test AD in corso...", "working")
        self.ctrl.set_voltage(AD_START_VOLTAGE)
        self.ctrl.set_current(TEST_CURRENT_A)
        self.ctrl.output_on()
        self._ad_voltage = AD_START_VOLTAGE
        # enable trip button now
        self._ad_trip_btn.setEnabled(True)
        # update label
        self._ad_status_label.setText(f"Tensione applicata: {self._ad_voltage} V")
        # timer to increase voltage
        self._ad_timer = QtCore.QTimer(self)
        self._ad_timer.timeout.connect(self._ad_step)
        self._ad_timer.start(self._ad_timer_interval_ms)

    def _ad_step(self):
        if self._ad_voltage >= TEST_MAX_VOLTAGE:
            self._ad_timer.stop()
            # tensione massima raggiunta — spegnere e mettere in local
            if self.ctrl:
                try:
                    self.ctrl.output_off()
                except Exception:
                    pass
                try:
                    self.ctrl.local_mode()
                except Exception:
                    pass
            self._ad_status_label.setText(
                f"Tensione massima ({TEST_MAX_VOLTAGE} V) raggiunta senza scatto."
            )
            self._update_status("Test AD completato", "ok")
            return
        self._ad_voltage += 1
        self.ctrl.set_voltage(self._ad_voltage)
        self._ad_status_label.setText(f"Tensione applicata: {self._ad_voltage} V")

    def _ad_tripped(self):
        # user clicked trip button; show voltage and stop timer
        if hasattr(self, "_ad_timer") and self._ad_timer.isActive():
            self._ad_timer.stop()
        self._ad_status_label.setText(f"Cartellino scattato a {self._ad_voltage} V")
        summary = (
            f"Anomalia Diodo (AD)\n"
            f"Tensione di scatto: {self._ad_voltage} V\n"
            f"Colonne: T={self._ad_voltage}, V=POS.\n\n"
            f"Riarmare i cartellini."
        )
        self._write_to_excel(
            lambda handler, row: handler.write_ad_results(row, self._ad_voltage),
            summary=summary,
            popup_to_close=getattr(self, '_ad_popup', None),
        )
        self._update_status("Test AD completato", "ok")

    def on_test_anomalia_tiristore_limiti(self):
        from .widgets.test_atal_dialog import TestATALDialog
        dlg = TestATALDialog(
            self,
            self.ctrl,
            self._write_to_excel,
            self._update_status,
            self._safe_power_off
        )
        dlg.exec_()

    def _close_at_al_test(self):
        """Clean up AT+AL test: stop timer, turn off output, close popup."""
        self._stop_existing_timer('_at_al_timer')
        if self.ctrl:
            try:
                self.ctrl.output_off()
            except Exception:
                pass
            try:
                self.ctrl.local_mode()
            except Exception:
                pass
        if hasattr(self, '_at_al_popup') and self._at_al_popup is not None:
            # Disconnect finished signal to prevent double cleanup
            try:
                self._at_al_popup.finished.disconnect(self._close_at_al_test)
            except (TypeError, RuntimeError):
                pass
            self._at_al_popup.close()
            self._at_al_popup = None
        self._update_status("Pronto", "ok")

    def _start_at_al_test(self):
        if not self.ctrl:
            QtWidgets.QMessageBox.warning(
                self, "Errore", "Collegare l'alimentatore prima di avviare il test AT+AL."
            )
            return
        # Stop any leftover timer from a previous run
        self._stop_existing_timer('_at_al_timer')
        self._pause_heartbeat()
        self._update_status("Test AT+AL in corso...", "working")
        # Reset stale values from previous tests
        if hasattr(self, '_at_al_cart1_value'):
            del self._at_al_cart1_value
        if hasattr(self, '_at_al_cart2_value'):
            del self._at_al_cart2_value
        self._at_al_cart1_label.setText("Cartellino1: - V")
        self._at_al_cart2_label.setText("Cartellino2: - V")
        self.ctrl.set_voltage(AT_AL_START_VOLTAGE)
        self.ctrl.set_current(TEST_CURRENT_A)
        self.ctrl.output_on()
        self._at_al_voltage = AT_AL_START_VOLTAGE
        # enable first cartellino button
        self._at_al_cart1_btn.setEnabled(True)
        # update live status
        self._at_al_status_label.setText(f"Tensione applicata: {self._at_al_voltage} V")
        # timer for increments
        self._at_al_timer = QtCore.QTimer(self)
        self._at_al_timer.timeout.connect(self._at_al_step)
        self._at_al_timer.start(self._at_al_timer_interval_ms)

    def _at_al_step(self):
        if self._at_al_voltage >= TEST_MAX_VOLTAGE:
            self._at_al_timer.stop()
            # tensione massima raggiunta — spegnere e mettere in local
            if self.ctrl:
                try:
                    self.ctrl.output_off()
                except Exception:
                    pass
                try:
                    self.ctrl.local_mode()
                except Exception:
                    pass
            self._at_al_status_label.setText(
                f"Tensione massima ({TEST_MAX_VOLTAGE} V) raggiunta."
            )
            self._update_status("Test AT+AL completato", "ok")
            return
        # continue incrementing until both buttons pressed
        self._at_al_voltage += 1
        self.ctrl.set_voltage(self._at_al_voltage)
        # update live voltage monitor
        self._at_al_status_label.setText(f"Tensione applicata: {self._at_al_voltage} V")

    def _at_al_cart1(self):
        # record voltage and enable second button
        self._at_al_cart1_value = self._at_al_voltage
        self._at_al_cart1_label.setText(f"Cartellino1: {self._at_al_cart1_value} V")
        self._at_al_cart2_btn.setEnabled(True)

    def _at_al_cart2(self):
        # record second voltage and end test
        self._at_al_cart2_value = self._at_al_voltage
        self._at_al_cart2_label.setText(f"Cartellino2: {self._at_al_cart2_value} V")
        if hasattr(self, '_at_al_timer') and self._at_al_timer.isActive():
            self._at_al_timer.stop()
        summary = (
            f"Anomalia Tiristore e Limiti (AT+AL)\n"
            f"Tensione Cartellino 1: {self._at_al_cart1_value} V\n"
            f"Tensione Cartellino 2: {self._at_al_cart2_value} V\n"
            f"Colonne: O={self._at_al_cart1_value}, Q=OK, R=OK, S=POS.\n\n"
            f"Riarmare i cartellini."
        )
        self._write_to_excel(
            lambda handler, row: handler.write_at_al_results(
                row, self._at_al_cart1_value
            ),
            summary=summary,
            popup_to_close=getattr(self, '_at_al_popup', None),
        )
        self._update_status("Test AT+AL completato", "ok")

    def _ad_al_step(self):
        # called each second by timer
        if self._ad_al_voltage >= TEST_MAX_VOLTAGE:
            self._ad_al_timer.stop()
            return
        self._ad_al_voltage += 1
        self.ctrl.set_voltage(self._ad_al_voltage)

    def _stop_ad_al_test(self):
        # triggered by popup button
        if hasattr(self, "_ad_al_timer"):
            self._ad_al_timer.stop()
        if self.ctrl:
            self.ctrl.output_off()
        if hasattr(self, "_ad_al_popup"):
            self._ad_al_popup.close()
            del self._ad_al_popup

    def on_test_innesco_tiristore(self):
        from .widgets.test_innesco_dialog import TestInnescoDialog
        dlg = TestInnescoDialog(
            self,
            self.ctrl,
            self._write_to_excel,
            self._update_status,
            self._safe_power_off
        )
        dlg.exec_()

    def _begin_innesco(self):
        # actual test sequence after initial instruction
        self._pause_heartbeat()
        self._update_status("Test Innesco in corso...", "working")
        self._innesco_aborted = False
        # Stop any leftover timers from a previous run
        self._stop_existing_timer('_innesco_timer')
        self._stop_existing_timer('_shutdown_timer')
        if not self.ctrl:
            return
        # setup initial output
        self.ctrl.set_voltage(INNESCO_START_VOLTAGE)
        self.ctrl.set_current(TEST_CURRENT_A)
        self.ctrl.output_on()
        self._innesco_voltage = INNESCO_START_VOLTAGE
        self._innesco_history = []

        # create popup with exit button
        popup = QtWidgets.QDialog(self)
        popup.setWindowTitle("Innesco Tiristore")
        self._style_popup(popup, min_width=500)
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        # Live voltage monitor
        voltage_label = QtWidgets.QLabel(
            f"Tensione applicata: {INNESCO_START_VOLTAGE} V"
        )
        voltage_label.setObjectName("voltage_live")  # [VISUAL]
        layout.addWidget(voltage_label)
        label = QtWidgets.QLabel(
            "Test Innesco: Attendere il completamento del test"
        )
        label.setObjectName("instructions")  # [VISUAL]
        label.setWordWrap(True)
        layout.addWidget(label)
        exit_btn = QtWidgets.QPushButton("Esci dal test")
        exit_btn.setObjectName("close_btn")  # [VISUAL]
        exit_btn.clicked.connect(self._exit_innesco_test)
        layout.addWidget(exit_btn)
        popup.setLayout(layout)
        self._innesco_popup = popup
        self._innesco_label = label  # keep reference for updates
        self._innesco_voltage_label = voltage_label  # live voltage display
        popup.adjustSize()
        popup.show()

        # timer for increment and measurement — use singleShot chaining
        # so that each step waits for the previous one to complete,
        # ensuring uniform intervals regardless of SCPI latency.
        self._innesco_running = True
        self._schedule_innesco_step()

    def _schedule_innesco_step(self):
        """Schedule the next innesco step after INNESCO_TIMER_INTERVAL_MS."""
        if not self._innesco_running:
            return
        # Store a reference so _stop_existing_timer can cancel it
        self._innesco_timer = QtCore.QTimer(self)
        self._innesco_timer.setSingleShot(True)
        self._innesco_timer.timeout.connect(self._innesco_step)
        self._innesco_timer.start(self._innesco_timer_interval_ms)

    def _innesco_step(self):
        # increment until measurement drops or max reached
        if not self._innesco_running:
            return
        if self._innesco_voltage >= TEST_MAX_VOLTAGE:
            self._innesco_running = False
            # tensione massima raggiunta — spegnere e mettere in local
            if self.ctrl:
                try:
                    self.ctrl.output_off()
                except Exception:
                    pass
                try:
                    self.ctrl.local_mode()
                except Exception:
                    pass
            return
        # increase voltage
        self._innesco_voltage += 1
        self.ctrl.set_voltage(self._innesco_voltage)
        # update live voltage label
        if hasattr(self, '_innesco_voltage_label'):
            self._innesco_voltage_label.setText(
                f"Tensione applicata: {self._innesco_voltage} V"
            )
        # measure and record
        try:
            measured = self.ctrl.measure_voltage()
        except Exception:
            measured = None
        if measured is not None:
            self._innesco_history.append(measured)
            # check drop compared to previous
            if len(self._innesco_history) >= 2 and measured < self._innesco_history[-2]:
                # stop the increments
                self._innesco_running = False
                # find highest recorded value during test (including drop)
                highest = max(self._innesco_history)
                # schedule raw diode drop measurement after 1 second
                QtCore.QTimer.singleShot(
                    INNESCO_DIODE_DELAY_MS,
                    lambda: self._calculate_diode_drop(highest),
                )
                return
        # schedule next step — interval starts AFTER this step completes
        self._schedule_innesco_step()
    def _calculate_diode_drop(self, highest: float):
        # if the test was aborted, do nothing
        if getattr(self, '_innesco_aborted', False):
            return
        # measure voltage again for diode drop
        try:
            raw = self.ctrl.measure_voltage()
        except Exception:
            raw = None
        if raw is not None:
            adjusted = raw - INNESCO_DIODE_OFFSET_V
            summary = (
                f"Innesco Tiristore\n"
                f"Valore massimo raggiunto: {highest} V\n"
                f"Caduta diodo: {adjusted:.2f} V\n"
                f"Colonne: H={adjusted:.2f}, J=POS., "
                f"K={int(round(highest))}, M=OK, N=POS."
            )
            # Write Innesco results to Excel and close popup
            self._write_to_excel(
                lambda handler, row: handler.write_innesco_results(
                    row, round(adjusted, 2), highest
                ),
                summary=summary,
                popup_to_close=getattr(self, '_innesco_popup', None),
            )
            self._update_status("Test Innesco completato", "ok")
        else:
            # Impossibile misurare — spegnere per sicurezza
            self._safe_power_off()
            if hasattr(self, '_innesco_label'):
                self._innesco_label.setText(
                    f"Valore massimo raggiunto: {highest} V\n"
                    "Errore: impossibile leggere la caduta di tensione."
                )
            self._update_status("Test Innesco — errore lettura", "error")

    def _exit_innesco_test(self):
        # mark test as aborted so pending singleShot callbacks are ignored
        self._innesco_aborted = True
        self._innesco_running = False
        self._stop_existing_timer('_innesco_timer')
        self._stop_existing_timer('_shutdown_timer')
        if self.ctrl:
            try:
                self.ctrl.output_off()
            except Exception:
                pass
            try:
                self.ctrl.local_mode()
            except Exception:
                pass
        if hasattr(self, "_innesco_popup") and self._innesco_popup is not None:
            self._innesco_popup.close()
            self._innesco_popup = None
        if hasattr(self, "_innesco_label"):
            del self._innesco_label
        if hasattr(self, "_innesco_voltage_label"):
            del self._innesco_voltage_label
        # Reset status label on main window
        self._update_status("Pronto", "ok")


    def _on_measure_complete(self, voltage: float, elapsed: float):
        self.result_label.setText(
            f"V: {voltage} V (took {elapsed:.3f}s)"
        )
        self.measure_btn.setEnabled(True)
        # cleanup worker reference
        self._measure_worker = None
