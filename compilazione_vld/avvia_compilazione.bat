@echo off
REM ============================================================
REM   Avvia Compilazione Componenti VLD
REM ============================================================
cd /d "%~dp0"

REM Usa il venv del progetto principale se disponibile
if exist "..\\.venv\\Scripts\\python.exe" (
    "..\.venv\Scripts\python.exe" compilazione.py
) else (
    python compilazione.py
)

if %errorlevel% neq 0 pause
