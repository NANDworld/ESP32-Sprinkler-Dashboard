"""
Cliente Bluetooth Serial para ESP32_SPRINKLER.

O ESP32 usa BluetoothSerial.h (Bluetooth clássico SPP), que no Windows
cria uma porta COM virtual após o emparelhamento. Este módulo lê os
dados dessa porta COM e transmite via WebSocket para o frontend.

Configuração no Windows:
  1. Emparelhe o ESP32_SPRINKLER no Bluetooth do Windows
  2. Verifique a porta COM criada (Painel -> Bluetooth -> Propriedades -> Portas COM)
  3. Configure a porta COM no arquivo config.json ou via variável de ambiente ESP32_COM_PORT
"""
import asyncio
import json
import logging
import os
import re
from datetime import datetime
from serial import Serial, SerialException
from serial.tools import list_ports
from websockets import serve

# Configurações
DEFAULT_COM_PORT = os.environ.get("ESP32_COM_PORT", "COM4")
BAUD_RATE = 115200  # Deve ser 115200 (Serial.begin(115200) no Arduino)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Estado global dos sensores
sensor_data = {
    "temperatura": None,
    "umidade": None,
    "bomba": None,
    "modo": None,
    "fumaca": None,
    "fumaca_adc": None,
    "ultima_atualizacao": None
}

# Conexões WebSocket ativas
ws_clients = set()

# Buffer para mensagens incompletas
_message_buffer = ""


def detect_esp32_port() -> str:
    """Tenta detectar automaticamente a porta COM do ESP32."""
    com_port = os.environ.get("ESP32_COM_PORT")
    if com_port:
        return com_port

    known_patterns = [
        "CP210", "CH340", "CH341", "Silicon", "USB Serial",
        "ESP32", "U-Blox", "FTDI", "Prolific"
    ]

    ports = list_ports.comports()
    for port in ports:
        desc = (port.description or "").upper()
        for pattern in known_patterns:
            if pattern.upper() in desc:
                logger.info(f"Porta ESP32 detectada: {port.device} ({port.description})")
                return port.device

    logger.warning(f"Nenhuma porta ESP32 detectada. Usando padrão: {DEFAULT_COM_PORT}")
    return DEFAULT_COM_PORT


def parse_sensor_message(message: str) -> dict:
    """Parseia a mensagem texto do ESP32 e retorna um dicionário estruturado."""
    data = {}
    # Padrões atualizados para serem mais flexíveis (ex: aceitar 'nan', 'err', etc.)
    patterns = {
        "temperatura": r"Temperatura:\s*([^\r\n]+?)\s*C",
        "umidade": r"Umidade:\s*([^\r\n]+?)\s*%",
        "bomba": r"Bomba:\s*(LIGADA|DESLIGADA)",
        "modo": r"Modo:\s*(AUTOMATICO|MANUAL|AGUARDANDO)",
        "fumaca": r"Fumaca:\s*(AQUECENDO|DETECTADA|NAO_DETECTADA)",
        "fumaca_adc": r"Fumaca ADC:\s*(\d+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            
            # Tratamento especial para temperatura e umidade
            if key in ("temperatura", "umidade"):
                try:
                    # Tenta converter para float
                    float_val = float(value)
                    # Verifica se é um valor válido (não nan ou inf)
                    if not (float_val != float_val): # check for nan
                        data[key] = float_val
                    else:
                        logger.warning(f"Valor inválido ({key}): {value}")
                        data[key] = None
                except ValueError:
                    # Se não for número, mantém como None ou string de erro se preferir
                    logger.warning(f"Falha ao converter {key}: '{value}'")
                    data[key] = None
            elif key == "fumaca_adc":
                try:
                    data[key] = int(value)
                except ValueError:
                    data[key] = None
            else:
                data[key] = value

    return data


async def broadcast_to_websocket(data_dict: dict):
    """Envia dados atualizados para todos os clientes WebSocket conectados."""
    if ws_clients:
        payload = json.dumps(data_dict)
        await asyncio.gather(
            *[client.send(payload) for client in ws_clients],
            return_exceptions=True
        )


async def process_complete_message(message: str):
    """Processa uma mensagem completa (bloco inteiro do ESP32)."""
    logger.info(f"Mensagem completa recebida:\n{message}")
    parsed = parse_sensor_message(message)

    if parsed:
        sensor_data.update(parsed)
        sensor_data["ultima_atualizacao"] = datetime.now().isoformat()
        await broadcast_to_websocket(sensor_data)


async def serial_reader_loop():
    """Loop principal: conecta/reconecta à porta serial e lê dados continuamente."""
    global _message_buffer
    _message_buffer = ""

    while True:
        port = detect_esp32_port()
        serial_conn = None

        try:
            logger.info(f"Tentando conectar à {port} na velocidade {BAUD_RATE}")
            serial_conn = Serial(port, BAUD_RATE, timeout=1)
            logger.info(f"Conectado à {port} com sucesso!")

            while serial_conn and serial_conn.is_open:
                if serial_conn.in_waiting > 0:
                    try:
                        raw = serial_conn.readline()
                        message = raw.decode("utf-8", errors="replace").strip()

                        if not message:
                            continue

                        if message == "-------------------":
                            _message_buffer += message + "\n"
                            await process_complete_message(_message_buffer)
                            _message_buffer = ""
                        else:
                            _message_buffer += message + "\n"

                    except (SerialException, UnicodeDecodeError) as e:
                        logger.error(f"Erro na leitura: {e}")
                        break

                await asyncio.sleep(0.05)

        except (SerialException, OSError) as e:
            logger.error(f"Não foi possível conectar à {port}: {e}")

        finally:
            if serial_conn and serial_conn.is_open:
                serial_conn.close()
                logger.info(f"Conexão serial com {port} encerrada")

        await asyncio.sleep(3)


async def websocket_handler(websocket, path=None):
    """Gerencia conexões WebSocket para o frontend."""
    client_addr = getattr(websocket, "remote_address", getattr(websocket, "remote", "unknown"))
    logger.info(f"Cliente WebSocket conectado: {client_addr}")
    ws_clients.add(websocket)
    try:
        await websocket.send(json.dumps(sensor_data))
        async for _ in websocket:
            pass
    except Exception as e:
        logger.error(f"Erro no WebSocket: {e}")
    finally:
        ws_clients.discard(websocket)
        logger.info("Cliente WebSocket desconectado")


async def start_websocket_server(host: str = "0.0.0.0", port: int = 8765):
    """Inicia o servidor WebSocket para broadcast dos dados."""
    server = await serve(websocket_handler, host, port)
    logger.info(f"Servidor WebSocket rodando em ws://{host}:{port}")
    return server


async def main():
    """Ponto de entrada: inicia WebSocket + leitor serial em paralelo."""
    ws_server = await start_websocket_server()
    serial_task = asyncio.create_task(serial_reader_loop())

    try:
        await ws_server.wait_closed()
    finally:
        serial_task.cancel()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Encerrado pelo usuário")