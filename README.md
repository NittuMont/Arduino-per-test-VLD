# Arduino per test VLD

Questo progetto contiene:
- **Firmware PlatformIO** per Arduino Nano ESP32 che espone un servizio BLE custom per il monitoraggio di 6 circuiti tramite protocollo READY+STATE.
- **GUI Python (PyQt5 + bleak)** per PC che si connette via BLE, invia il comando READY e riceve notifiche di stato in tempo reale.

## Funzionalità principali
- Protocollo minimale: la GUI invia READY, Arduino risponde con lo stato dei circuiti.
- Notifiche BLE affidabili e sincronizzazione all'avvio.
- Codice pulito, facilmente estendibile.

## Struttura
- `src/` : Firmware PlatformIO per Arduino Nano ESP32
- `itech_interface/` : GUI Python per monitoraggio BLE

## Come usare
1. Carica il firmware su Arduino Nano ESP32 tramite PlatformIO.
2. Avvia la GUI Python (`ble_monitor_gui.py`) su PC.
3. Connetti via BLE, invia READY, ricevi lo stato dei circuiti.

## Badge
Il badge è un piccolo "bollino" visuale che mostra lo stato del progetto (ad esempio: build passing, versione, licenza, ecc.) direttamente nel README. Aiuta a capire a colpo d'occhio se il progetto è attivamente mantenuto, se la build è stabile, ecc.

Esempio di badge build (GitHub Actions):

![Build Status](https://github.com/NittuMont/Arduino-per-test-VLD/actions/workflows/main.yml/badge.svg)

> Per attivare il badge build, aggiungi un workflow GitHub Actions (ad esempio per PlatformIO o Python).

