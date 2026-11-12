@echo off
setlocal
cd /d "%~dp0.."
set OLLAMA_NO_CLOUD=1
py -3 -m kiki
if errorlevel 1 (
  echo Instale Python 3 com Tcl/Tk. Consulte docs/SETUP.md.
  pause
)
