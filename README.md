# ESP32 Sprinkler Backend

Backend Python para receber dados do ESP32 Sprinkler via Bluetooth Serial e exibi-los em tempo real.

## 📋 O que os dados do ESP32 contêm

O ESP32 envia a seguinte informação (via `SerialBT.println`):

| Campo            | Exemplo de valor                | Origem no código Arduino |
|-----------------|---------------------------------|--------------------------|
| `Temperatura`   | `Temperatura: 25.5 C`           | `dht.readTemperature()`  |
| `Umidade`       | `Umidade: 60.0 %`               | `dht.readHumidity()`     |
| `Bomba`         | `Bomba: LIGADA` / `DESLIGADA`  | Variável `bombaLigada`   |
| `Modo`          | `Modo: AUTOMATICO` / `MANUAL` / `AGUARDANDO` | Variáveis de controle |
| `Fumaca`        | `Fumaca: DETECTADA` / `NAO_DETECTADA` / `AQUECENDO` | Lógica do MQ-2 |
| `Fumaca ADC`    | `Fumaca ADC: 1234`              | `analogRead(PINO_SENSOR_FUMACA)` |

Formato da mensagem completa:
```
Temperatura: 25.5 C
Umidade: 60.0 %

Bomba: DESLIGADA
Modo: AGUARDANDO
Fumaca: NAO_DETECTADA
Fumaca ADC: 1234
-------------------
```

## 🚀 Como executar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar Bluetooth do ESP32
- O ESP32 usa `BluetoothSerial.h` → Bluetooth **clássico** (SPP)
- Emparelhe o dispositivo `ESP32_SPRINKLER` no Windows
- Anote a **porta COM** criada (ex: COM3)
- Configure via variável de ambiente:
  ```cmd
  set ESP32_COM_PORT=COM3
  ```

### 3. Iniciar o sistema
```bash
# Automático (inicia tudo):
start.bat        (Windows)
./start.sh       (Linux/macOS)

# Manual:
python esp32_ble_client.py   # Cliente serial -> WebSocket (porta 8765)
python main.py               # API FastAPI + Dashboard (porta 8000)
```

## 🌐 Endpoints

| Rota              | Descrição                           |
|-------------------|-------------------------------------|
| `GET /`           | Dashboard HTML com dados em tempo real |
| `GET /api/data`   | Últimos dados do ESP32 (JSON)       |
| `GET /api/health` | Verifica status da conexão         |
| `GET /docs`       | Documentação Swagger da API         |

## ⚙️ Arquivos

| Arquivo                  | Função                                      |
|--------------------------|---------------------------------------------|
| `main.py`               | Backend FastAPI (API + Dashboard)          |
| `esp32_ble_client.py`   | Cliente serial BLE → WebSocket bridge      |
| `requirements.txt`      | Dependências Python                         |
| `start.bat` / `start.sh` | Script de inicialização                    |