@echo off
setlocal
cd /d "%~dp0"
if not exist ".env" copy ".env.example" ".env" >nul
echo Escribe tu clave en GEMINI_API_KEY dentro del archivo que se abrira.
echo Guarda el archivo y vuelve a abrir el chatbot.
notepad ".env"
