@echo off
REM Start the ITECH GUI application.
REM If a virtual environment exists in the workspace root, activate it first.
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

REM Launch via module entry point; change directory to the package root to ensure imports work
cd /d "%~dp0\itech_interface"
REM run the GUI in a background window (minimized)
start "" /MIN python -m itech_interface.main
