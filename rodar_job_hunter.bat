
@echo off
cd /d "%~dp0"

if not exist "logs" mkdir "logs"

echo =============================== >> "logs\agendador_windows.log"
echo Iniciando Job Hunter IA em %date% %time% >> "logs\agendador_windows.log"

py scripts\rotacionar_log_agendador.py
py main.py >> "logs\agendador_windows.log" 2>&1
set "JHI_EXIT_CODE=%ERRORLEVEL%"
echo Codigo de saida do Python: %JHI_EXIT_CODE% >> "logs\agendador_windows.log"

echo Finalizado em %date% %time% >> "logs\agendador_windows.log"
echo =============================== >> "logs\agendador_windows.log"
exit /b %JHI_EXIT_CODE%
