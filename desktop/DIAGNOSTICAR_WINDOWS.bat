@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" diagnosticar.py
    goto fin
)
call _python_windows.bat
if errorlevel 1 goto fin
"%PICME_PY%" %PICME_PY_ARGS% diagnosticar.py
:fin
echo.
pause
