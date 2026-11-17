@echo off
setlocal
cd /d "%~dp0"
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0main.py"
    goto :finished
)
py -3 -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
if not errorlevel 1 (
    py -3 "%~dp0main.py"
    goto :finished
)
python -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
if not errorlevel 1 (
    python "%~dp0main.py"
    goto :finished
)
echo No se encontro Python 3.10 o posterior.
echo Instala Python con Tcl/Tk y vuelve a abrir este archivo.
echo Consulta README.md para las instrucciones.
pause
exit /b 1
:finished
if errorlevel 1 (
    echo No se pudo iniciar PyWrap. Consulta el mensaje anterior y README.md.
    pause
    exit /b 1
)
exit /b 0
