// Configuração
const WS_URL = "ws://localhost:8765";
const MAX_HISTORY = 50;

// Estado
let ws = null;
let lastUpdate = Date.now();
let historyData = [];

// Elementos do DOM
const indicator = document.getElementById('indicator');
const statusText = document.getElementById('status-text');
const tempEl = document.getElementById('temp');
const humidEl = document.getElementById('humid');
const smokeAdcEl = document.getElementById('smoke_adc');
const smokeEl = document.getElementById('smoke');
const pumpEl = document.getElementById('pump');
const modeEl = document.getElementById('mode');
const historyBody = document.getElementById('history-body');

// Conectar ao WebSocket
function connect() {
    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
        updateIndicator(true);
        console.log('✅ Conectado ao WebSocket');
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            updateDashboard(data);
            addToHistory(data);
            lastUpdate = Date.now();
        } catch (e) {
            console.error('Erro ao parsear dados:', e);
        }
    };

    ws.onclose = () => {
        updateIndicator(false);
        console.log('❌ Conexão encerrada, reconectando...');
        setTimeout(connect, 3000);
    };

    ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        updateIndicator(false);
    };
}

// Atualizar indicador de status
function updateIndicator(connected) {
    if (connected) {
        indicator.classList.add('connected');
        statusText.textContent = 'Conectado ao ESP32';
    } else {
        indicator.classList.remove('connected');
        statusText.textContent = 'Aguardando conexão...';
    }
}

// Atualizar dashboard
function updateDashboard(data) {
    // Temperatura
    if (data.temperatura !== null && data.temperatura !== undefined) {
        tempEl.textContent = `${data.temperatura.toFixed(1)} °C`;
    } else {
        tempEl.textContent = 'Erro no DHT11';
        tempEl.style.color = '#e63946';
    }

    // Umidade
    if (data.umidade !== null && data.umidade !== undefined) {
        humidEl.textContent = `${Math.round(data.umidade)} %`;
    } else {
        humidEl.textContent = '-- %';
    }

    // Fumaça ADC
    smokeAdcEl.textContent = data.fumaca_adc !== null ? data.fumaca_adc : '--';

    // Fumaça
    smokeEl.textContent = data.fumaca || '--';

    // Bomba
    const bomba = data.bomba || '';
    pumpEl.textContent = bomba;
    pumpEl.className = 'value ' + (bomba === 'LIGADA' ? 'pump-on' : 'pump-off');

    // Modo
    const modo = data.modo || '';
    modeEl.textContent = modo;
    modeEl.className = 'value mode-' + (modo.toLowerCase() === 'automatico' ? 'auto' :
                                       modo.toLowerCase() === 'manual' ? 'manual' : 'wait');
}

// Adicionar ao histórico
function addToHistory(data) {
    const now = new Date();
    const time = now.toLocaleTimeString('pt-BR');
    
    historyData.push({
        time,
        temp: data.temperatura?.toFixed(1) || '--',
        humid: data.umidade?.toFixed(0) || '--',
        smokeAdc: data.fumaca_adc || '--',
        bomba: data.bomba || '--',
        modo: data.modo || '--'
    });

    // Manter apenas os últimos MAX_HISTORY registros
    if (historyData.length > MAX_HISTORY) {
        historyData.shift();
    }

    renderHistory();
}

// Renderizar histórico
function renderHistory() {
    historyBody.innerHTML = historyData.map(row => `
        <tr>
            <td>${row.time}</td>
            <td>${row.temp}</td>
            <td>${row.humid}</td>
            <td>${row.smokeAdc}</td>
            <td>${row.bomba}</td>
            <td>${row.modo}</td>
        </tr>
    `).reverse().join('');
}

// Timeout: verificar se há atualização
setInterval(() => {
    if (Date.now() - lastUpdate > 10000) {
        updateIndicator(false);
    }
}, 3000);

// Iniciar conexão
connect();
