"""
Backend FastAPI para ESP32_SPRINKLER.

Endpoints:
  GET /         -> Dashboard HTML (mostra os dados em tempo real)
  GET /api/data -> Últimos dados do ESP32 (JSON)
  GET /api/health -> Verifica se o backend está online
  GET /docs     -> Documentação da API (Swagger UI)

Funcionalidades:
  - Dashboard web em tempo real conecta via WebSocket ao esp32_ble_client
  - API REST para integração com outros sistemas
"""
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from esp32_ble_client import sensor_data

app = FastAPI(
    title="ESP32 Sprinkler Backend",
    description="Backend para receber e exibir dados do ESP32 via Bluetooth.",
    version="1.0.0"
)


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Dashboard HTML mostrando os dados do ESP32 em tempo real."""
    return HTMLResponse(content=DASHBOARD_HTML)


@app.get("/api/data")
async def get_data():
    """Retorna os últimos dados recebidos do ESP32."""
    return sensor_data


@app.get("/api/health")
async def health_check():
    """Verifica se o backend está online."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "esp32_conectado": sensor_data.get("ultima_atualizacao") is not None
    }


# --- Dashboard HTML ---

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ESP32 Sprinkler Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1a1a2e;
            color: #eee;
            min-height: 100vh;
            padding: 20px;
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            color: #00d4ff;
            text-shadow: 0 0 10px rgba(0,212,255,0.5);
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            max-width: 1000px;
            margin: 0 auto;
        }
        .card {
            background: #16213e;
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            border: 1px solid #0f3460;
            transition: transform 0.2s;
        }
        .card:hover { transform: translateY(-5px); }
        .card h3 {
            font-size: 14px;
            text-transform: uppercase;
            color: #888;
            margin-bottom: 10px;
        }
        .card .value {
            font-size: 28px;
            font-weight: bold;
        }
        .temp .value { color: #ff6b6b; }
        .humid .value { color: #4ecdc4; }
        .smoke .value { color: #f9a825; }
        .pump-on { color: #52b788; }
        .pump-off { color: #e63946; }
        .mode-auto { color: #00d4ff; }
        .mode-manual { color: #f77f01; }
        .mode-wait { color: #888; }
        .status-bar {
            text-align: center;
            margin-top: 30px;
            padding: 15px;
            background: #16213e;
            border-radius: 10px;
            max-width: 1000px;
            margin: 30px auto 0;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .connected { background: #52b788; box-shadow: 0 0 10px #52b788; }
        .disconnected { background: #e63946; box-shadow: 0 0 10px #e63946; }
        .error-msg { color: #e63946; font-weight: bold; }
    </style>
</head>
<body>
    <h1>🌡️ ESP32 Sprinkler Dashboard</h1>
    <div class="grid">
        <div class="card temp">
            <h3>Temperatura</h3>
            <div class="value" id="temp">-- °C</div>
        </div>
        <div class="card humid">
            <h3>Umidade</h3>
            <div class="value" id="humid">-- %</div>
        </div>
        <div class="card smoke">
            <h3>Fumaça ADC</h3>
            <div class="value" id="smoke_adc">--</div>
        </div>
        <div class="card">
            <h3>Fumaça</h3>
            <div class="value" id="smoke">--</div>
        </div>
        <div class="card">
            <h3>Bomba</h3>
            <div class="value" id="pump">--</div>
        </div>
        <div class="card">
            <h3>Modo</h3>
            <div class="value" id="mode">--</div>
        </div>
    </div>
    <div class="status-bar">
        <span class="status-indicator" id="indicator"></span>
        <span id="status-text">Conectando ao ESP32...</span>
    </div>

    <script>
        const ws = new WebSocket("ws://localhost:8765");
        let lastUpdate = Date.now();

        function updateIndicator(connected) {
            const ind = document.getElementById("indicator");
            const txt = document.getElementById("status-text");
            if (connected) {
                ind.className = "status-indicator connected";
                txt.textContent = "Conectado ao ESP32";
            } else {
                ind.className = "status-indicator disconnected";
                txt.textContent = "Aguardando ESP32...";
            }
        }

        ws.onopen = () => { updateIndicator(true); };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            // Temperatura
            const tempEl = document.getElementById("temp");
            if (data.temperatura !== null && data.temperatura !== undefined) {
                tempEl.textContent = data.temperatura.toFixed(1) + " °C";
                tempEl.classList.remove("error-msg");
            } else {
                tempEl.textContent = "Erro no DHT11";
                tempEl.classList.add("error-msg");
            }

            // Umidade
            const humidEl = document.getElementById("humid");
            humidEl.textContent = (data.umidade !== null && data.umidade !== undefined)
                ? Math.round(data.umidade) + " %"
                : "-- %";

            // Fumaça ADC
            document.getElementById("smoke_adc").textContent =
                (data.fumaca_adc !== null && data.fumaca_adc !== undefined)
                ? data.fumaca_adc
                : "--";

            // Fumaça
            document.getElementById("smoke").textContent = data.fumaca || "--";

            // Bomba
            const pumpEl = document.getElementById("pump");
            const bomba = data.bomba || "";
            pumpEl.textContent = bomba;
            pumpEl.className = "value " + (bomba === "LIGADA" ? "pump-on" : "pump-off");

            // Modo
            const modeEl = document.getElementById("mode");
            const modo = data.modo || "";
            modeEl.textContent = modo;
            modeEl.className = "value mode-" + (modo.toLowerCase() === "automatico" ? "auto" :
                                               modo.toLowerCase() === "manual" ? "manual" : "wait");

            lastUpdate = Date.now();
        };

        ws.onclose = () => { updateIndicator(false); };

        ws.onerror = (err) => {
            console.error("WebSocket error:", err);
            updateIndicator(false);
        };

        // Timeout: verifica se houve atualização nos últimos 10 segundos
        setInterval(() => {
            if (Date.now() - lastUpdate > 10000) {
                updateIndicator(false);
            }
        }, 3000);
    </script>
</body>
</html>"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)