@echo off
echo ========================================
echo   Build VLD_Test.exe (standalone)
echo ========================================
echo.

cd /d "%~dp0"

echo Pulizia cartelle build precedenti...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo Compilazione in corso...
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "VLD_Test" --paths "src" --collect-all "openpyxl" --collect-all "bleak" --hidden-import "PyQt5.sip" run.py

if exist dist\VLD_Test.exe (
    echo.
    echo ========================================
    echo   BUILD COMPLETATA CON SUCCESSO
    echo   Output: dist\VLD_Test.exe
    echo ========================================
) else (
    echo.
    echo ========================================
    echo   ERRORE: build fallita!
    echo ========================================
)

echo.
pause
