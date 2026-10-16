@echo off
rem Devuelve PICME_PY y PICME_PY_ARGS. No modifica Python ni el PATH.
set "PICME_PY="
set "PICME_PY_ARGS="
for %%V in (3.10 3.11 3.12) do (
    py -%%V -c "import sys,struct;sys.exit(0 if struct.calcsize('P')==8 else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "PICME_PY=py"
        set "PICME_PY_ARGS=-%%V"
        exit /b 0
    )
)
python -c "import sys,struct;sys.exit(0 if (3,10)<=sys.version_info[:2]<=(3,12) and struct.calcsize('P')==8 else 1)" >nul 2>&1
if not errorlevel 1 (
    set "PICME_PY=python"
    exit /b 0
)
for %%P in ("C:\Program Files\Python310\python.exe" "%LocalAppData%\Programs\Python\Python310\python.exe" "%LocalAppData%\Programs\Python\Python311\python.exe" "%LocalAppData%\Programs\Python\Python312\python.exe") do (
    if exist "%%~P" (
        "%%~P" -c "import sys,struct;sys.exit(0 if (3,10)<=sys.version_info[:2]<=(3,12) and struct.calcsize('P')==8 else 1)" >nul 2>&1
        if not errorlevel 1 (
            set "PICME_PY=%%~P"
            exit /b 0
        )
    )
)
echo No se encontro Python 3.10, 3.11 o 3.12 de 64 bits.
echo Instalalo desde https://www.python.org/downloads/windows/
echo Incluye Tcl/Tk y el lanzador py.
exit /b 1
