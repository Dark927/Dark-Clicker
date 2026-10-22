@echo off
echo ==============================================
echo Building Dark-Clicker for Windows (PyInstaller)
echo ==============================================

python -m PyInstaller --onefile --noconsole --name "Dark-Clicker" main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Executable built at: dist\Dark-Clicker.exe
) else (
    echo.
    echo [ERROR] Build failed! Check dependencies.
)
pause
