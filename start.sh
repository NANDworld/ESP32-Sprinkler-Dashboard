#!/bin/bash
# Script de inicialização do backend ESP32 Sprinkler (Linux/macOS)
# Inicia o cliente serial/WebSocket e o servidor FastAPI simultaneamente

cd "$(dirname "$0")"

echo "Verificando ambiente virtual..."
if [ ! -f ".venv/bin/python" ]; then
    echo "ERRO: Ambiente virtual não encontrado."
    echo "Execute: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Configurar porta COM
export ESP32_COM_PORT=${ESP32_COM_PORT:-COM4}
echo "Porta COM definida: $ESP32_COM_PORT"

# Inicia o cliente serial (WebSocket bridge)
.venv/bin/python esp32_ble_client.py &
CLIENT_PID=$!
echo "Cliente serial/WS iniciado (PID: $CLIENT_PID)"

sleep 2

# Inicia o servidor FastAPI
.venv/bin/python main.py &
API_PID=$!
echo "Backend FastAPI iniciado (PID: $API_PID)"

sleep 3

echo ""
echo "============================================"
echo "Backend iniciado com sucesso!"
echo ""
echo "   - Dashboard:   http://localhost:8005"
echo "   - API REST:    http://localhost:8005/api/data"
echo "   - Documentação: http://localhost:8005/docs"
echo "   - WebSocket:   ws://localhost:8765"
echo ""
echo "============================================"
echo ""
echo "Abrindo dashboard no navegador..."
xdg-open "http://localhost:8005" || open "http://localhost:8005" 2>/dev/null || echo "Abra manualmente: http://localhost:8005"
echo ""
echo "Para encerrar os serviços, pressione Ctrl+C ou feche os terminais dos processos."
echo "Pressione Enter para sair..."
read

# Captura interrupção para limpar processos
trap "kill $CLIENT_PID $API_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait
