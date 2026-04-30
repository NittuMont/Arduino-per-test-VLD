# ITECH Power Supply Controller

This project provides a Python interface to control an ITECH IT6018C-1500-30 power supply over LAN. The application lets users run scheduled tests via button clicks.

## Features

- Connect directly to the power supply over Ethernet
- Simple GUI for triggering tests
- Basic logging of results

## Getting Started

1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate the environment:
   - Windows: `venv\Scripts\activate`
   - Unix/Mac: `source venv/bin/activate`
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python -m src.main
   ```

## Structure

- `src/` contains application code
- `tests/` for unit tests

## TODO

- Implement Telnet/HTTP commands for ITECH supply
- Design GUI using Tkinter or PyQt

