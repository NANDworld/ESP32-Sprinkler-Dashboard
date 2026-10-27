# Documentação Completa - Projeto ESP32 Sprinkler Backend

---

## 1. Visão Geral

**Objetivo**: Criar um backend Python para receber dados de um ESP32 (rodando código Arduino) via Bluetooth Serial e exibi-los em dashboard web + API REST.

**Hardware**: ESP32 (wESP32 Silicognition) com sensores DHT11, MQ-2, relé, botão, LCD I2C.

**Comunicação**: Bluetooth clássico (SPP) via `BluetoothSerial.h` → porta COM virtual no Windows.

---

## 2. Código Arduino (ESP32)

### 2.1 Bibliotecas Necessárias

| Biblioteca | Como Instalar | Observação |
|------------|---------------|------------|
| `Wire.h` | Nativa (ESP32 core) | I2C para LCD |
| `BluetoothSerial.h` | Nativa (ESP32 core) | Bluetooth SPP |
| `DHT.h` | Library Manager → **DHT sensor library** (Adafruit) | Instalar também *Adafruit Unified Sensor* |
| `LiquidCrystal_I2C.h` | Library Manager → **LiquidCrystal I2C** (Frank de Brabander) | Warning "architecture" é normal |

### 2.2 Configuração no Arduino IDE (wESP32)

```ini
Placa: wESP32 (ou Silicognition wESP32)
Flash Size: 4 MB (32 Mb)          ← CRÍTICO: evita erro "Detected size(4096k) smaller than... 16384k"
Partition Scheme: Default 4MB with spiffs
PSRAM: Enabled                    ← wESP32 tem PSRAM
Upload Speed: 921600
Porta: COMx (USB-Serial CP210x)
```

### 2.3 Formato de Dados Enviados (BluetoothSerial)

O ESP32 envia a cada 2 segundos (`intervaloLeitura = 2000`):

```
Temperatura: 25.5 C
Umidade: 60.0 %

Bomba: LIGADA
Modo: AUTOMATICO
Fumaca: NAO_DETECTADA
Fumaca ADC: 1234
-------------------
```

**Campos parseados**:
| Campo | Tipo | Valores Possíveis |
|-------|------|-------------------|
| temperatura | float | °C (ex: 25.5) |
| umidade | float | % (ex: 60.0) |
| bomba | string | "LIGADA" / "DESLIGADA" |
| modo | string | "AUTOMATICO" / "MANUAL" / "AGUARDANDO" |
| fumaca | string | "AQUECENDO" / "DETECTADA" / "NAO_DETECTADA" |
| fumaca_adc | int | 0-4095 (leitura raw MQ-2) |

---

## 3. Backend Python - Arquitetura

```
┌─────────────────┐     Serial/Bluetooth      ┌──────────────────┐
│   ESP32         │ ─────────────────────────▶ │  esp32_ble_client.py  │
│  (Arduino)      │   Porta COM (115200)      │  - Lê porta serial   │
└─────────────────┘                            │  - Parseia mensagens │
                                               │  - WebSocket :8765   │
                                               └────────┬───────────┘
                                                        │ WebSocket (JSON)
                                               ┌────────▼───────────┐
                                               │    main.py         │
                                               │  - FastAPI :8000   │
                                               │  - Dashboard HTML  │
                                               │  - API REST        │
                                               └────────────────────┘
```

### 3.1 Arquivos do Projeto

| Arquivo | Função |
|---------|--------|
| `main.py` | Servidor FastAPI (porta 8000) - Dashboard + API |
| `esp32_ble_client.py` | Cliente Serial → WebSocket Bridge (porta 8765) |
| `requirements.txt` | Dependências Python |
| `start.bat` / `start.sh` | Scripts de inicialização |
| `README.md` | Documentação resumida |

---

## 4. Dependências Python

```txt
fastapi>=0.110.0
uvicorn>=0.27.0
websockets>=12.0
pyserial>=3.5
```

**Instalação**:
```cmd
pip install -r requirements.txt
```
> **Nota**: `bleak` (BLE) **não** foi usado — o ESP32 usa Bluetooth clássico (SPP), que aparece como porta COM serial. `pyserial` resolve.

---

## 5. Erros Encontrados e Soluções

### 5.1 Erro: `DHT.h: No such file or directory`
**Causa**: Biblioteca DHT não instalada.
**Solução**: Library Manager → "DHT sensor library" (Adafruit) + "Adafruit Unified Sensor".

### 5.2 Warning: `LiquidCrystal_I2C claims to run on all architecture(s)...`
**Causa**: Biblioteca não declara compatibilidade explícita com ESP32.
**Solução**: **Ignorar** — funciona normalmente no ESP32.

### 5.3 Erro: `Detected size(4096k) smaller than the size in the binary image header(16384k)`
**Causa**: Flash Size configurado para 16 MB mas o ESP32 tem 4 MB.
**Solução**: **Ferramentas → Flash Size → 4 MB (32 Mb)**.

### 5.4 Erro: `PermissionError(13, 'Acesso negado.')` na porta COM4
**Causa**: **Monitor Serial do Arduino IDE aberto** — trava a porta COM.
**Solução**: **Fechar a aba do Monitor Serial** antes de rodar o Python.

### 5.5 Erro: `AttributeError: 'WebSocketServerProtocol' object has no attribute 'remote'`
**Causa**: `websockets` v17+ mudou `websocket.remote` → `websocket.remote_address`.
**Solução**: Código corrigido com fallback:
```python
client_addr = getattr(websocket, "remote_address", getattr(websocket, "remote", "unknown"))
```

### 5.6 DeprecationWarning: `websockets.server.serve is deprecated`
**Causa**: Import antigo `from websockets.server import serve`.
**Solução**: Mudar para `from websockets import serve`.

### 5.7 Erro de compilação `winrt-runtime` ao tentar instalar `bleak`
**Causa**: `bleak` no Windows precisa Microsoft Visual C++ Build Tools.
**Solução**: **Não usar BLE** — usar `pyserial` para Bluetooth clássico (SPP).

---

## 6. Como Executar

### 6.1 Preparar ESP32
1. Carregar código Arduino (com Flash Size = 4 MB)
2. Abrir Monitor Serial (115200) → confirmar "Bluetooth iniciado / ESP32_SPRINKLER"
3. **FECHAR Monitor Serial**

### 6.2 Emparelhar Bluetooth (Windows)
1. Configurações → Bluetooth → "ESP32_SPRINKLER" → Emparelhar
2. Propriedades do dispositivo → Portas COM → anotar porta (ex: COM5, COM6)

### 6.3 Rodar Backend

**Opção A - Automática (Windows)**:
```cmd
set ESP32_COM_PORT=COM5   # sua porta Bluetooth SPP
start.bat
```

**Opção B - Manual (2 terminais)**:
```cmd
# Terminal 1 - WebSocket Bridge
python esp32_ble_client.py

# Terminal 2 - API + Dashboard
python main.py
```

### 6.4 Acessar
| URL | Descrição |
|-----|-----------|
| http://localhost:8000 | Dashboard tempo real |
| http://localhost:8000/api/data | JSON últimos dados |
| http://localhost:8000/api/health | Health check |
| http://localhost:8000/docs | Swagger UI |
| ws://localhost:8765 | WebSocket (dados brutos) |

---

## 7. Estrutura de Dados (JSON)

**`GET /api/data`** / WebSocket message:
```json
{
  "temperatura": 25.5,
  "umidade": 60.0,
  "bomba": "LIGADA",
  "modo": "AUTOMATICO",
  "fumaca": "NAO_DETECTADA",
  "fumaca_adc": 1234,
  "ultima_atualizacao": "2026-10-21T16:45:12.345678"
}
```

---

## 8. Troubleshooting Rápido

| Sintoma | Verificar |
|---------|-----------|
| Dashboard mostra "--" | ESP32 enviando dados? Monitor Serial fechado? |
| "Acesso negado" COMx | Fechar Monitor Serial Arduino IDE; verificar se outra app usa a porta |
| WebSocket não conecta | `esp32_ble_client.py` rodando? Porta 8765 livre? |
| Dados não atualizam | ESP32 emparelhado via Bluetooth? Porta COM correta no `ESP32_COM_PORT`? |
| Erro upload ESP32 | Segurar BOOT durante upload; Flash Size = 4 MB |

---

## 9. Próximos Passos (Sugestões)

- [ ] Adicionar autenticação na API
- [ ] Persistir dados em SQLite/InfluxDB
- [ ] Alertas (Telegram/Email) quando fumaca = DETECTADA
- [ ] Controle remoto da bomba via API (POST /api/bomba)
- [ ] Dockerfile para deploy fácil
- [ ] Migração para MQTT se múltiplos ESP32

---

## 10. Histórico de Versões

| Data | Versão | Alterações |
|------|--------|------------|
| 2026-10-21 | 1.0.0 | Criação inicial: FastAPI + Serial Bridge + Dashboard |
| 2026-10-21 | 1.0.1 | Fix WebSocket `remote_address` + import `websockets.serve` |

---

**Desenvolvido para**: Projeto SIDCI - Sistema de Irrigação e Detecção de Incêndio  
**Autor**: Assistente IA + Usuário  
**Data**: Outubro 2026