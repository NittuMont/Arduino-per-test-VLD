# Test VLD RFI

Questo progetto contiene:
- **Firmware PlatformIO** per Arduino Nano ESP32 che espone un servizio BLE custom per il monitoraggio di 6 circuiti (relè ON/OFF).
- **GUI Python (PyQt5 + bleak)** per operatore che gestisce test automatizzati dei VLD (alimentatore ITech via SCPI + monitoraggio relè via BLE).

## Struttura
- `platformio.ini` : Configurazione PlatformIO, ambiente `nanoesp32`
- `src/ble_heartbeat.ino` : Firmware attivo Arduino Nano ESP32, monitor BLE a 6 circuiti
- `src/backup/` : Copie storiche del firmware e prova seriale, conservate ma escluse dalla build
- `include/` : Header locali del firmware
- `itech_interface/` : Pacchetto Python — GUI operatore, comunicazione SCPI/BLE, gestione Excel
- `compilazione_vld/` : Programma di compilazione componenti VLD su Excel
- `ArduinoNanoESP32.code-workspace` : Workspace VS Code portabile con firmware e GUI
- `start_ble_monitor_gui.bat` : Avvio GUI/BLE su Windows con percorsi relativi al repository

## Firmware e repository completo

Firmware e GUI sono ora versionati nello stesso repository. Aprire questa cartella
o `ArduinoNanoESP32.code-workspace` in VS Code: PlatformIO riconosce il progetto
tramite `platformio.ini`. Usare **Project Tasks → nanoesp32 → Build** per compilare
senza programmare la scheda. L'upload è un'operazione distinta e non viene eseguito
dal commit o dal push.

Il firmware attivo e le quattro copie storiche sono stati importati dal progetto
locale ArduinoNanoESP32 senza modificarne la logica. Perché le modifiche future al
firmware siano incluse nei commit, lavorare sui file `src/` di questo repository,
non sulla vecchia cartella PlatformIO esterna.

Il dispositivo BLE si chiama **NanoESP32-RelayMonitor**. L'ordine dei bit è
AT ON, AL ON, AD ON, AT OFF, AL OFF, AD OFF; i pin Arduino sono rispettivamente
D12, D7, D3, D11, D6, D2. Gli ingressi usano pull-up e un livello LOW indica
circuito chiuso. Questi stati non certificano l'assenza di tensione sul banco.

Cache, ambienti virtuali e risultati di build (`.pio/`, `.venv/`, `build/`, `dist/`,
`__pycache__/`) non vengono aggiunti ai nuovi commit. I pacchetti portabili già
presenti nel repository restano disponibili, ma non vengono ricompilati
automaticamente quando si aggiornano i sorgenti. La ricetta e lo script di build
della GUI sono in `itech_interface/VLD_Test.spec` e `itech_interface/build_exe.bat`.

## Come usare
1. Carica il firmware su Arduino Nano ESP32 tramite PlatformIO.
2. Installa le dipendenze Python: `pip install -r itech_interface/requirements.txt`
3. Avvia la GUI: `python -m itech_interface.main` (dalla cartella `itech_interface/src`)
4. La GUI si connette automaticamente all'alimentatore (192.168.1.100) e al dispositivo BLE.

In alternativa, su Windows avviare `start_ble_monitor_gui.bat`: viene usato
l'interprete di `.venv` se presente nella radice, altrimenti quello disponibile
come `python`. Installare le dipendenze nello stesso ambiente prima dell'avvio;
`bleak` è necessario per il collegamento BLE.

## Versione portabile
Vedere `Portabile/LEGGIMI.txt` per istruzioni sulla versione standalone (.exe).

