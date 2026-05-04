from PyQt5 import QtWidgets, QtCore


class BLEHandlers:
    """Gestisce tutti gli eventi BLE per MainWindow.

    Architettura:
      - on_ble_state_update:  aggiorna GUI, poi dispatcha al gestore del test attivo.
      - _process_ad_relay:    logica relè test AD  (idx=0, bit_off=5).
      - _process_atal_relays: logica relè test AT+AL (AL idx=1 bit_off=4,
                               AT idx=2 bit_off=3). Rileva primo e secondo scatto
                               separatamente, chiama dialog.on_relay_tripped().
      - Test Innesco:         nessuna logica relay (test autonomo).
      - _check_anomaly:       avvia/cancella timer anomalia per ogni relè.
      - reset_all_relay_timers_and_flags: pulizia completa, chiamabile da gui.py.
    """

    def __init__(self, main_window):
        self.main = main_window
        self._prev_state = 0
        # Il primo aggiornamento BLE non genera transizioni (prev_state=0 è arbitrario)
        self._first_state_received = False
        # Timer anomalia per ogni relè [AD=0, AL=1, AT=2]
        self._anomaly_timers = [None] * 3
        self._relay_anomaly = [False] * 3
        # (bit_ON, bit_OFF, nome) — indici: 0=AD, 1=AL, 2=AT
        self._relay_map = [
            (2, 5, "AD"),
            (1, 4, "AL"),
            (0, 3, "AT"),
        ]

    # ------------------------------------------------------------------
    # Pulizia stato
    # ------------------------------------------------------------------

    def reset_all_relay_timers_and_flags(self):
        """Ferma tutti i timer anomalia e resetta i flag di stato relè."""
        for i in range(len(self._anomaly_timers)):
            if self._anomaly_timers[i] is not None:
                self._anomaly_timers[i].stop()
            self._anomaly_timers[i] = None
            self._relay_anomaly[i] = False

    # ------------------------------------------------------------------
    # BLE device discovery & connection
    # ------------------------------------------------------------------

    def on_ble_reconnect_clicked(self):
        self.main.ble_status_bar.set_status('connecting')
        self.main.ble_worker.scan_ble()

    def on_ble_devices_found(self, found):
        self.main.ble_device_combo.clear()
        self.main._ble_devices = []
        arduino_name = "NanoESP32-RelayMonitor"
        arduino_device = None
        for d in found:
            name = d.name if d.name else "<No Name>"
            if name == arduino_name:
                arduino_device = d
                self.main.ble_device_combo.addItem(f"{name} [{d.address}]", d)
                self.main._ble_devices.append(d)
                break
        self.main.ble_connect_btn.setEnabled(bool(self.main._ble_devices))
        if arduino_device:
            self.main.ble_device_combo.setCurrentIndex(0)
            self.on_ble_connect_clicked()  # Connessione automatica
        else:
            QtCore.QTimer.singleShot(500, self.main.ble_worker.scan_ble)
        self.main.ble_status_bar.set_status(
            'fail' if not self.main._ble_devices else 'connecting'
        )

    def on_ble_error(self, msg):
        self.main.ble_status_bar.set_status('fail')

    def on_ble_connect_clicked(self):
        idx = self.main.ble_device_combo.currentIndex()
        if hasattr(self.main, '_ble_devices') and self.main._ble_devices and 0 <= idx < len(self.main._ble_devices):
            device = self.main._ble_devices[idx]
            self.main.ble_status_bar.set_status('connecting')
            self.main.ble_worker.connect_device(device)
        else:
            QtWidgets.QMessageBox.warning(self.main, "BLE", "Nessun dispositivo selezionato.")

    # ------------------------------------------------------------------
    # BLE state update — entry point principale
    # ------------------------------------------------------------------

    def on_ble_state_update(self, state_byte):
        # 1. Aggiorna sempre le label GUI (indipendentemente dal test attivo)
        for i in range(6):
            closed = (state_byte >> i) & 1
            label = self.main.ble_circuit_labels[i]
            style_common = "font-size:18px; border-radius:8px; padding:6px;"
            if closed:
                label.setText(self.main.ble_group.circuit_names[i] + ": CHIUSO")
                label.setStyleSheet(f"background:#8f8; {style_common}")
            else:
                label.setText(self.main.ble_group.circuit_names[i] + ": APERTO")
                label.setStyleSheet(f"background:#f88; {style_common}")

        # 2. Solo se BLE è connesso (modalità automatica)
        if not getattr(self.main, '_ble_connected_flag', False):
            self._prev_state = state_byte
            return

        # 3. Primo aggiornamento dopo la connessione: inizializza prev_state senza
        #    generare transizioni (altrimenti ogni rele' chiuso sembrerebbe uno scatto)
        if not self._first_state_received:
            self._first_state_received = True
            self._prev_state = state_byte
            return

        # 4. Dispatch al gestore del test attivo
        if self.main._ad_test_active:
            self._process_ad_relay(state_byte)
        elif self.main._at_al_test_active:
            self._process_atal_relays(state_byte)
        # _innesco_test_active: nessuna logica relay, il test è gestito autonomamente

        self._prev_state = state_byte

    # ------------------------------------------------------------------
    # Helpers interni
    # ------------------------------------------------------------------

    def _check_anomaly(self, relay_idx, curr_on, curr_off):
        """Avvia o cancella il timer anomalia per il relè dato.

        Anomalia = entrambi i circuiti (ON e OFF) aperti per più di 300 ms.
        """
        nome = self._relay_map[relay_idx][2]
        if not curr_on and not curr_off:
            if not self._relay_anomaly[relay_idx] and self._anomaly_timers[relay_idx] is None:
                timer = QtCore.QTimer()
                timer.setSingleShot(True)
                timer.timeout.connect(
                    lambda ri=relay_idx, n=nome: self._handle_anomaly(ri, n)
                )
                timer.start(300)
                self._anomaly_timers[relay_idx] = timer
        else:
            if self._anomaly_timers[relay_idx] is not None:
                self._anomaly_timers[relay_idx].stop()
                self._anomaly_timers[relay_idx] = None
            self._relay_anomaly[relay_idx] = False

    def _handle_anomaly(self, relay_idx, nome):
        """Gestisce un'anomalia relè persistente (entrambi aperti > 300 ms)."""
        self._anomaly_timers[relay_idx] = None
        bit_on, bit_off, _ = self._relay_map[relay_idx]
        curr_on = (self._prev_state >> bit_on) & 1
        curr_off = (self._prev_state >> bit_off) & 1
        if curr_on or curr_off:
            return  # Anomalia rientrata prima del timeout
        test_active = (
            (relay_idx == 0 and self.main._ad_test_active) or
            (relay_idx in (1, 2) and self.main._at_al_test_active)
        )
        if not test_active:
            return
        self._relay_anomaly[relay_idx] = True
        stop_fn = self.main._close_ad_test if relay_idx == 0 else self.main._close_at_al_test
        QtWidgets.QMessageBox.critical(
            self.main,
            f"Anomalia relè {nome}",
            f"Entrambi i circuiti (ON/OFF) del relè {nome} sono aperti da oltre 300 ms!\n"
            f"Test interrotto senza salvare risultati."
        )
        stop_fn()

    # ------------------------------------------------------------------
    # Test AD — relè idx=0 (bit_ON=2, bit_OFF=5)
    # ------------------------------------------------------------------

    def _process_ad_relay(self, state_byte):
        relay_idx = 0
        bit_on, bit_off, _ = self._relay_map[relay_idx]
        prev_off = (self._prev_state >> bit_off) & 1
        curr_on  = (state_byte >> bit_on)  & 1
        curr_off = (state_byte >> bit_off) & 1

        self._check_anomaly(relay_idx, curr_on, curr_off)

        # Scatto: transizione OFF APERTO→CHIUSO
        if not prev_off and curr_off:
            dialog = getattr(self.main, '_ad_dialog', None)
            if dialog is not None:
                dialog.on_relay_tripped()

    # ------------------------------------------------------------------
    # Test AT+AL — AL idx=1 (bit_off=4) e AT idx=2 (bit_off=3)
    # ------------------------------------------------------------------

    def _process_atal_relays(self, state_byte):
        """Rileva il primo e il secondo scatto indipendentemente.

        Ogni volta che un relè OFF passa APERTO→CHIUSO viene chiamato
        dialog.on_relay_tripped(relay_name, voltage).
        La dialog tiene traccia dell'ordine (primo/secondo scatto).
        """
        dialog = getattr(self.main, '_at_al_dialog', None)

        for relay_idx in (1, 2):
            bit_on, bit_off, nome = self._relay_map[relay_idx]
            prev_off = (self._prev_state >> bit_off) & 1
            curr_on  = (state_byte >> bit_on)  & 1
            curr_off = (state_byte >> bit_off) & 1

            self._check_anomaly(relay_idx, curr_on, curr_off)

            # Scatto: transizione OFF APERTO→CHIUSO
            if not prev_off and curr_off:
                if dialog is not None:
                    dialog.on_relay_tripped(nome)

    # ------------------------------------------------------------------
    # Connection events
    # ------------------------------------------------------------------

    def on_ble_connected(self):
        self.main.ble_status_bar.set_status('ok')
        self.main._ble_connected_flag = True
        self._first_state_received = False
        # Con BLE attivo: step tensione veloci (100 ms)
        self.main._on_step_interval_selected(100)

    def on_ble_disconnected(self):
        self.main.ble_status_bar.set_status('fail')
        self.main._ble_connected_flag = False
        # Senza BLE: step tensione lenti (1000 ms)
        self.main._on_step_interval_selected(1000)
        QtWidgets.QMessageBox.warning(
            self.main, "Connessione BLE",
            "Connessione BLE persa! Tentativo di riconnessione..."
        )
        self.main._ble_devices = []
        self.main.ble_device_combo.clear()
        QtCore.QTimer.singleShot(500, self.main.ble_worker.scan_ble)
