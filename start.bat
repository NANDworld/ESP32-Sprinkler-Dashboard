@echo off
REM Script de inicialização do backend ESP32 Sprinkler (Windows)
cd /d "%~dp0"

echo Iniciando cliente serial/WebSocket...
start "ESP32 Client" cmd /c python esp32_ble_client.py
echo.
echo Iniciando backend FastAPI...
start "ESP32 API" cmd /c python main.py
echo.
echo ============================================
echo Backend iniciado! 
echo   - API REST:    http://localhost:8000
echo   - Dashboard:   http://localhost:8000
echo   - WebSocket:   ws://localhost:8765
echo   - Docs:        http://localhost:8000/docs
echo ============================================
echo.
echo Pressione Ctrl+C para encerrar.