@echo off
REM Avvia la GUI VLD/BLE dal repository, senza percorsi specifici del PC.
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "itech_interface\run.py"
) else (
    python "itech_interface\run.py"
)
pause
endlocal