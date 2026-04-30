@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

title Installazione e avvio - Test VLD RFI
echo ============================================================
echo   Installazione e avvio - Test VLD RFI
echo ============================================================
echo.

REM ---------------------------------------------------------------
REM 1. Verifica se Python e' gia' installato
REM ---------------------------------------------------------------
echo [1/4] Verifica installazione Python...

where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
    echo       Trovato: !PY_VER!
    goto :python_ok
)

REM Controlla anche py launcher (installato di default con Python su Windows)
where py >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%v in ('py --version 2^>^&1') do set "PY_VER=%%v"
    echo       Trovato tramite py launcher: !PY_VER!
    goto :python_ok
)

echo       Python NON trovato. Avvio installazione automatica...
echo.

REM ---------------------------------------------------------------
REM 2. Scarica e installa Python automaticamente
REM ---------------------------------------------------------------
echo [2/4] Download installer Python 3.12...

set "PY_INSTALLER=%TEMP%\python-installer.exe"
set "PY_URL=https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"

REM Usa PowerShell per scaricare (disponibile su Windows 10+)
powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PY_URL%' -OutFile '%PY_INSTALLER%' }" 2>nul

if not exist "%PY_INSTALLER%" (
    echo.
    echo ERRORE: impossibile scaricare Python.
    echo Verificare la connessione a Internet oppure installare Python manualmente da:
    echo   https://www.python.org/downloads/
    echo Selezionare "Add Python to PATH" durante l'installazione.
    echo.
    pause
    exit /b 1
)

echo       Download completato. Avvio installazione silenziosa...

REM Installazione silenziosa: aggiunge a PATH, include pip, per tutti gli utenti
"%PY_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_test=0

if %errorlevel% neq 0 (
    echo.
    echo ERRORE: installazione Python fallita (codice %errorlevel%).
    echo Provare a installare Python manualmente da:
    echo   https://www.python.org/downloads/
    echo.
    del /f "%PY_INSTALLER%" >nul 2>&1
    pause
    exit /b 1
)

echo       Python installato con successo.
del /f "%PY_INSTALLER%" >nul 2>&1

REM Aggiorna il PATH nella sessione corrente
set "LOCALAPPDATA_PY=%LOCALAPPDATA%\Programs\Python\Python312"
if exist "!LOCALAPPDATA_PY!\python.exe" (
    set "PATH=!LOCALAPPDATA_PY!;!LOCALAPPDATA_PY!\Scripts;!PATH!"
)

REM Verifica che Python sia ora raggiungibile
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ATTENZIONE: Python installato ma non trovato nel PATH corrente.
    echo Chiudere e riaprire questo script, oppure riavviare il PC.
    echo.
    pause
    exit /b 1
)

:python_ok
echo.

REM ---------------------------------------------------------------
REM 3. Verifica e installa dipendenze (requirements.txt)
REM ---------------------------------------------------------------
echo [3/4] Verifica dipendenze Python...

set "ALL_OK=1"
for /f "usebackq tokens=1 delims=>#; " %%p in ("requirements.txt") do (
    python -c "import importlib; importlib.import_module('%%p'.replace('-','_').lower())" >nul 2>&1
    if errorlevel 1 (
        echo       Pacchetto mancante: %%p
        set "ALL_OK=0"
    )
)

if "!ALL_OK!"=="1" (
    echo       Tutte le dipendenze sono gia' installate.
) else (
    echo       Installazione dipendenze in corso...
    python -m pip install --upgrade pip >nul 2>&1
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ERRORE durante l'installazione delle dipendenze.
        echo Verificare la connessione a Internet e riprovare.
        echo.
        pause
        exit /b 1
    )
    echo       Dipendenze installate con successo.
)
echo.

REM ---------------------------------------------------------------
REM 4. Avvio del programma
REM ---------------------------------------------------------------
echo [4/4] Avvio programma...
echo.
python -m itech_interface.main

if %errorlevel% neq 0 (
    echo.
    echo Il programma si e' chiuso con un errore.
    pause
)
endlocal
