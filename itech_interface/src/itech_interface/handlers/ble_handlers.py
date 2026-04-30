from PyQt5 import QtWidgets, QtCore

# Handler BLE per MainWindow
class BLEHandlers:
    def __init__(self, main_window):
        self.main = main_window
        # Stato precedente dei 6 circuiti (bitmask)
        self._prev_state = 0
        # Timer di tolleranza per ogni relè (None o QTimer)
        self._relay_timers = [None] * 3  # [AD, AL, AT]
        # Flag per anomalia già segnalata
        self._relay_anomaly = [False] * 3
        # Mappa: indice relè → (bit ON, bit OFF, nome, metodo_stop)
        self._relay_map = [
            # (bit_ON, bit_OFF, nome, metodo_stop)
            (2, 5, "AD", self.main._close_ad_test),
            (1, 4, "AL", self.main._close_at_al_test),
            (0, 3, "AT", self.main._begin_innesco),  # fix: era _close_innesco
        ]
        # Tensione da registrare per ogni relè (None o float)
        self._relay_voltage = [None] * 3

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
        self.main.ble_status_bar.set_status('fail' if not self.main._ble_devices else 'connecting')

    def on_ble_error(self, msg):
        import traceback
        self.main.ble_status_bar.set_status('fail')
        print(f"[BLE ERROR SUPPRESSED] {msg}")
        print("[BLE ERROR TRACE]")
        traceback.print_stack()

    def on_ble_state_update(self, state_byte):
        # Aggiorna GUI
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

        # Solo se BLE collegato (modalità automatica)
        if not getattr(self.main, '_ble_connected_flag', False):
            self._prev_state = state_byte
            return


        # Solo il test attivo può gestire la logica del proprio relè
        test_flags = [self.main._ad_test_active, self.main._at_al_test_active, self.main._innesco_test_active]
        if any(test_flags):
            idx = test_flags.index(True)
            bit_on, bit_off, nome, metodo_stop = self._relay_map[idx]
            prev_on = (self._prev_state >> bit_on) & 1
            prev_off = (self._prev_state >> bit_off) & 1
            curr_on = (state_byte >> bit_on) & 1
            curr_off = (state_byte >> bit_off) & 1

            # Se entrambi aperti > 300ms → anomalia SOLO se il test è attivo
            if not curr_on and not curr_off:
                # Avvia timer anomalia SOLO se il test è attivo
                if test_flags[idx]:
                    if not self._relay_anomaly[idx]:
                        # Avvia timer anomalia se non già attivo
                        if self._relay_timers[idx] is None:
                            print(f"[DEBUG] Avvio timer anomalia relè {nome} (idx={idx})")
                            timer = QtCore.QTimer()
                            timer.setSingleShot(True)
                            timer.timeout.connect(lambda idx=idx: self._handle_relay_anomaly(idx, nome, metodo_stop))
                            timer.start(300)
                            self._relay_timers[idx] = timer
                else:
                    # Se il test NON è attivo, assicura che nessun timer venga lasciato attivo
                    if self._relay_timers[idx] is not None:
                        print(f"[DEBUG] Stop timer anomalia relè {nome} (idx={idx}) fuori test")
                        self._relay_timers[idx].stop()
                        self._relay_timers[idx] = None
                    self._relay_anomaly[idx] = False
                self._prev_state = state_byte
                return
                def reset_all_relay_timers_and_flags(self):
                    for i in range(len(self._relay_timers)):
                        timer = self._relay_timers[i]
                        if timer is not None:
                            print(f"[DEBUG] Stop timer anomalia relè idx={i} (reset_all)")
                            timer.stop()
                        self._relay_timers[i] = None
                        self._relay_anomaly[i] = False
            else:
                # Se uno dei due è chiuso, cancella eventuale timer anomalia
                if self._relay_timers[idx] is not None and self._relay_anomaly[idx]:
                    self._relay_timers[idx].stop()
                    self._relay_timers[idx] = None
                    self._relay_anomaly[idx] = False

            # Transizione ON→APERTO: avvia timer tolleranza
            if prev_on and not curr_on:
                # Avvia timer tolleranza per attesa chiusura OFF
                if self._relay_timers[idx] is not None:
                    self._relay_timers[idx].stop()
                timer = QtCore.QTimer()
                timer.setSingleShot(True)
                timer.timeout.connect(lambda idx=idx, nome=nome, metodo_stop=metodo_stop: self._handle_relay_timeout(idx, nome, metodo_stop))
                timer.start(300)
                self._relay_timers[idx] = timer
            # Transizione OFF: APERTO→CHIUSO
            if not prev_off and curr_off:
                # Se timer tolleranza attivo, registra tensione e ferma test
                if self._relay_timers[idx] is not None:
                    self._relay_timers[idx].stop()
                    self._relay_timers[idx] = None
                    # Registra tensione impostata
                    try:
                        vset = self.main.ctrl.get_voltage_set() if self.main.ctrl else None
                    except Exception:
                        vset = None
                    self._relay_voltage[idx] = vset
                    # Simula pressione pulsante cartellino nel dialog attivo
                    if idx == 0 and hasattr(self.main, '_ad_dialog') and self.main._ad_dialog is not None:
                        # AD
                        self.main._ad_dialog._ad_tripped()
                    elif idx == 1 and hasattr(self.main, '_at_al_dialog') and self.main._at_al_dialog is not None:
                        # AT+AL: logica indipendente dall'ordine dei relè OFF
                        # Bit OFF: AL OFF = 4, AT OFF = 3
                        relays_off = [(3, 'AT'), (4, 'AL')]
                        # Stato precedente e attuale dei due relè OFF
                        prev_offs = [(self._prev_state >> bit) & 1 for bit, _ in relays_off]
                        curr_offs = [(state_byte >> bit) & 1 for bit, _ in relays_off]
                        # Conta quanti sono chiusi ora
                        num_closed = sum(curr_offs)
                        print(f"[DEBUG][BLE] AT+AL: prev_offs={prev_offs}, curr_offs={curr_offs}, num_closed={num_closed}")
                        # Se entrambi risultano chiusi, chiudi test e salva (indipendentemente dall'ordine)
                        if num_closed == 2:
                            print(f"[DEBUG][BLE] Entrambi i relè AT+AL OFF chiusi. Chiamo _cart1/_cart2.")
                            # Se non già fatto, chiama _cart1() per il primo scatto
                            if not hasattr(self.main._at_al_dialog, '_at_al_cart1_value') or self.main._at_al_dialog._at_al_cart1_value is None:
                                print(f"[DEBUG][BLE] Chiamo _cart1() su dialog AT+AL")
                                self.main._at_al_dialog._cart1()
                            # Blocca chiamate multiple a _cart2
                            if not hasattr(self.main._at_al_dialog, '_at_al_cart2_value') or self.main._at_al_dialog._at_al_cart2_value is None:
                                print(f"[DEBUG][BLE] Chiamo _cart2() su dialog AT+AL")
                                self.main._at_al_dialog._cart2()
                    elif idx == 2 and hasattr(self.main, '_innesco_dialog') and self.main._innesco_dialog is not None:
                        # Innesco: chiudi dialog
                        self.main._innesco_dialog.accept()
            # Reset anomalia se tutto ok
            if curr_on or curr_off:
                self._relay_anomaly[idx] = False
        self._prev_state = state_byte

        self._prev_state = state_byte

    def _handle_relay_timeout(self, idx, nome, metodo_stop):
        # Blocca se il test non è più attivo
        test_flags = [self.main._ad_test_active, self.main._at_al_test_active, self.main._innesco_test_active]
        if not test_flags[idx]:
            self._relay_timers[idx] = None
            return
        # Dopo 300ms: se entrambi aperti, segnala anomalia
        state_byte = self._prev_state
        bit_on, bit_off, _, _ = self._relay_map[idx]
        curr_on = (state_byte >> bit_on) & 1
        curr_off = (state_byte >> bit_off) & 1
        if not curr_on and not curr_off:
            self._relay_anomaly[idx] = True
            QtWidgets.QMessageBox.critical(self.main, f"Anomalia relè {nome}", f"Entrambi i circuiti (ON/OFF) del relè {nome} sono aperti da oltre 300ms! Test interrotto senza salvare risultati.")
            metodo_stop()
        self._relay_timers[idx] = None

    def _handle_relay_anomaly(self, idx, nome, metodo_stop):
        # Blocca se il test non è più attivo
        test_flags = [self.main._ad_test_active, self.main._at_al_test_active, self.main._innesco_test_active]
        if not test_flags[idx]:
            self._relay_timers[idx] = None
            return
        # Anomalia persistente: popup e stop test
        self._relay_anomaly[idx] = True
        QtWidgets.QMessageBox.critical(self.main, f"Anomalia relè {nome}", f"Entrambi i circuiti (ON/OFF) del relè {nome} sono aperti da oltre 300ms! Test interrotto senza salvare risultati.")
        metodo_stop()
        self._relay_timers[idx] = None

    def on_ble_connected(self):
        print(f"[DEBUG] on_ble_connected: setting self.main._ble_connected_flag = True (was {self.main._ble_connected_flag})")
        self.main.ble_status_bar.set_status('ok')
        self.main._ble_connected_flag = True
        self.main._ad_timer_interval_ms = max(1, int(self.main.AD_TIMER_INTERVAL_MS * 0.1))
        self.main._at_al_timer_interval_ms = max(1, int(self.main.AT_AL_TIMER_INTERVAL_MS * 0.1))
        self.main._innesco_timer_interval_ms = max(1, int(self.main.INNESCO_TIMER_INTERVAL_MS * 0.1))

    def on_ble_disconnected(self):
        print(f"[DEBUG] on_ble_disconnected: setting self.main._ble_connected_flag = False (was {self.main._ble_connected_flag})")
        self.main.ble_status_bar.set_status('fail')
        self.main._ble_connected_flag = False
        self.main._ad_timer_interval_ms = self.main.AD_TIMER_INTERVAL_MS
        self.main._at_al_timer_interval_ms = self.main.AT_AL_TIMER_INTERVAL_MS
        self.main._innesco_timer_interval_ms = self.main.INNESCO_TIMER_INTERVAL_MS
        QtWidgets.QMessageBox.warning(self.main, "Connessione BLE", "Connessione BLE persa! Tentativo di riconnessione...")
        self.main._ble_devices = []
        self.main.ble_device_combo.clear()
        QtCore.QTimer.singleShot(500, self.main.ble_worker.scan_ble)

    def on_ble_connect_clicked(self):
        idx = self.main.ble_device_combo.currentIndex()
        print(f"[DEBUG] on_ble_connect_clicked: _ble_connected_flag is {self.main._ble_connected_flag}")
        if hasattr(self.main, '_ble_devices') and self.main._ble_devices and 0 <= idx < len(self.main._ble_devices):
            device = self.main._ble_devices[idx]
            self.main.ble_status_bar.set_status('connecting')
            self.main.ble_worker.connect_device(device)
        else:
            QtWidgets.QMessageBox.warning(self.main, "BLE", "Nessun dispositivo selezionato.")
