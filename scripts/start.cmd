@echo off
setlocal
cd /d "%~dp0.."
set OLLAMA_NO_CLOUD=1
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m kiki
  goto :result
)
py -3 -m kiki
:result
if errorlevel 1 (
  echo Instale Python 3 com Tcl/Tk. Consulte docs/SETUP.md.
  pause
)
