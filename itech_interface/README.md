# ITECH IT6018C-1500-30 GUI Interface

This project provides a Python-based graphical application for controlling the ITECH IT6018C-1500-30 industrial power supply over a LAN connection. Users can perform scheduled tests by clicking buttons in the GUI.

## Features

* Connect to the device via TCP/IP directly on the local network
* Issue SCPI commands to set voltage/current, read measurements, and run automated sequences
* Simple PyQt5-based interface with programmable test buttons

## Guida operatore

- Il menu **Aiuto → Guida all'uso** (anche **F1**) descrive connessioni PSU/BLE,
	selezione Excel e matricola, prove, tempi di step, salvataggi e problemi comuni.
- Il campo **Caduta di tensione** in alto parte da **0,00 V** al primo utilizzo.
	Ogni valore inserito viene ricordato per i successivi avvii sullo stesso PC e
	con lo stesso utente. Il riferimento **SCR e iTech = 10,55 V** nella didascalia
	non è un valore applicato automaticamente.
- Il campo è modificabile anche nella finestra del test Innesco. Il risultato
	in colonna H del quarto foglio è la misura grezza meno il valore impostato,
	arrotondato a due decimali. Modificarlo non cambia la tensione dell'alimentatore
	e non modifica risultati già salvati.
- Usare il modello Excel previsto: matricole in colonna A del primo foglio e
	risultati nel quarto foglio. Chiudere il file in Excel prima del salvataggio.
- Le preferenze sono locali all'utente (QSettings); non sono incluse nel foglio
	Excel o nel repository. I test automatici usano preferenze e file temporanei.

**Sicurezza:** gli stati PSU/BLE e i comandi software non certificano l'assenza
di tensione. Seguire le procedure del banco e verificare le condizioni elettriche
prima di toccare il dispositivo o cambiare i collegamenti.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -e .
```

## Running

```bash
python -m itech_interface
```

## Testing

```bash
pytest
```
