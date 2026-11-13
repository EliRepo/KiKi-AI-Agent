@echo off
setlocal
set "OLLAMA_NO_CLOUD=1"
set "OLLAMA_HOST=127.0.0.1:11434"
if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
  "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
) else (
  ollama serve
)
if errorlevel 1 (
  echo Nao foi possivel iniciar. Verifique se o Ollama esta instalado ou ja esta aberto.
  pause
)
