@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" verificar_llm.py
    goto fin
)
call _python_windows.bat
if errorlevel 1 goto fin
"%PICME_PY%" %PICME_PY_ARGS% verificar_llm.py
:fin
echo.
pause
