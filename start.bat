@echo off
REM Script de inicialização do backend ESP32 Sprinkler (Windows)
cd /d "%~dp0"

echo Verificando ambiente virtual...
if not exist ".venv\Scripts\python.exe" (
    echo ERRO: Ambiente virtual não encontrado. Execute: python -m venv .venv && .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo Configurando variável COM_PORT (Padrão: COM4)...
set /p ESP32_COM_PORT="Digite a porta COM do ESP32 (ex: COM4) ou ENTER para usar COM4: "
if "%ESP32_COM_PORT%"=="" set ESP32_COM_PORT=COM4
echo Porta definida: %ESP32_COM_PORT%
set ESP32_COM_PORT=%ESP32_COM_PORT%

echo.
echo Iniciando cliente serial/WebSocket...
start "ESP32 Client" cmd /c "%~dp0.venv\Scripts\python.exe esp32_ble_client.py"
timeout /t 2 /nobreak >nul

echo.
echo Iniciando backend FastAPI...
start "ESP32 API" cmd /c "%~dp0.venv\Scripts\python.exe main.py"
timeout /t 3 /nobreak >nul

echo.
echo ============================================
echo Backend iniciado com sucesso!
echo.
echo   - Dashboard:   http://localhost:8005
echo   - API REST:    http://localhost:8005/api/data
echo   - Documentação: http://localhost:8005/docs
echo   - WebSocket:   ws://localhost:8765
echo.
echo ============================================
echo.
echo Abrindo dashboard no navegador...
start "" "http://localhost:8005"
echo.
echo Para encerrar os serviços, feche as janelas "ESP32 Client" e "ESP32 API" ou pressione Ctrl+C nelas.
echo Pressione qualquer tecla para sair deste terminal...
pause >nul
