# Test VLD RFI

Questo progetto contiene:
- **Firmware PlatformIO** per Arduino Nano ESP32 che espone un servizio BLE custom per il monitoraggio di 6 circuiti (relè ON/OFF).
- **GUI Python (PyQt5 + bleak)** per operatore che gestisce test automatizzati dei VLD (alimentatore ITech via SCPI + monitoraggio relè via BLE).

## Struttura
- `src/` : Firmware PlatformIO per Arduino Nano ESP32
- `itech_interface/` : Pacchetto Python — GUI operatore, comunicazione SCPI/BLE, gestione Excel
- `compilazione_vld/` : Programma di compilazione componenti VLD su Excel

## Come usare
1. Carica il firmware su Arduino Nano ESP32 tramite PlatformIO.
2. Installa le dipendenze Python: `pip install -r itech_interface/requirements.txt`
3. Avvia la GUI: `python -m itech_interface.main` (dalla cartella `itech_interface/src`)
4. La GUI si connette automaticamente all'alimentatore (192.168.1.100) e al dispositivo BLE.

## Versione portabile
Vedere `Portabile/LEGGIMI.txt` per istruzioni sulla versione standalone (.exe).

