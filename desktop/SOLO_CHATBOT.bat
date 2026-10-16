@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run.py --chatbot
    if errorlevel 1 pause
    exit /b
)
call _python_windows.bat
if errorlevel 1 goto fin
"%PICME_PY%" %PICME_PY_ARGS% run.py --chatbot
if not errorlevel 1 exit /b
:fin
pause
