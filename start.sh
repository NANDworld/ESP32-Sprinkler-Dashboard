#!/bin/bash
# Script de inicialização do backend ESP32 Sprinkler
# Inicia o cliente serial/WebSocket e o servidor FastAPI simultaneamente

cd "$(dirname "$0")"

# Inicia o cliente serial (WebSocket bridge)
python esp32_ble_client.py &
CLIENT_PID=$!
echo "Cliente serial/WS iniciado (PID: $CLIENT_PID)"

# Inicia o servidor FastAPI
python main.py &
API_PID=$!
echo "Backend FastAPI iniciado (PID: $API_PID)"

# Captura interrupção para limpar processos
trap "kill $CLIENT_PID $API_PID 2>/dev/null" SIGINT SIGTERM
wait