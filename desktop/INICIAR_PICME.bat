@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Primero ejecuta INSTALAR_WINDOWS.bat.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" run.py
if errorlevel 1 (
    echo.
    echo Revisa data\picme.log o ejecuta DIAGNOSTICAR_WINDOWS.bat.
    pause
)
