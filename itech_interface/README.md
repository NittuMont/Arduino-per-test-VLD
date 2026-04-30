# ITECH IT6018C-1500-30 GUI Interface

This project provides a Python-based graphical application for controlling the ITECH IT6018C-1500-30 industrial power supply over a LAN connection. Users can perform scheduled tests by clicking buttons in the GUI.

## Features

* Connect to the device via TCP/IP directly on the local network
* Issue SCPI commands to set voltage/current, read measurements, and run automated sequences
* Simple PyQt5-based interface with programmable test buttons

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
