import subprocess
import time
import socket
import requests
import json
import struct

# ============================================================
# CONFIGURAR ESTOS VALORES
# ============================================================
WIFI_CASA = "FAMILIA MUNOS"          # Nombre de tu WiFi de casa
CONTRASENA_CASA = "41777932"                  # Contraseña de tu WiFi (edítala aquí)
IP_SERVIDOR = "192.168.0.102"         # IP de tu PC en la red de casa
PUERTO_SERVIDOR = 8080
# ============================================================

SAINLOGIC_SSID = "Sainlogic-3A2357"
IPS_POSIBLES = ["192.168.4.1", "192.168.1.1", "192.168.0.1", "10.0.0.1"]


def conectar_wifi(ssid):
    """Conecta la PC a una red WiFi usando netsh"""
    print(f"[+] Conectando a '{ssid}'...")
    result = subprocess.run(
        ["netsh", "wlan", "connect", f"name={ssid}"],
        capture_output=True, text=True
    )
    if "correctamente" in result.stdout or "successfully" in result.stdout:
        print(f"[OK] Conectado a {ssid}")
        return True
    print(f"[!] Resultado: {result.stdout.strip()}")
    time.sleep(3)
    return True  # Intentar de todos modos


def obtener_ip_gateway():
    """Obtiene la IP del gateway cuando está conectado al hotspot"""
    result = subprocess.run(
        ["ipconfig"], capture_output=True, text=True, encoding="cp1252"
    )
    lines = result.stdout.split("\n")
    for i, line in enumerate(lines):
        if "Puerta de enlace" in line or "Default Gateway" in line:
            parts = line.split(":")
            if len(parts) > 1:
                ip = parts[-1].strip()
                if ip and ip != "":
                    print(f"[OK] Gateway encontrado: {ip}")
                    return ip
    return None


def escanear_estacion():
    """Busca la estación en IPs comunes"""
    print("\n[+] Buscando la estación climática...")

    # Primero intenta con el gateway
    gateway = obtener_ip_gateway()
    if gateway:
        IPS_POSIBLES.insert(0, gateway)

    for ip in IPS_POSIBLES:
        print(f"    Probando {ip}...")
        try:
            r = requests.get(f"http://{ip}", timeout=3)
            print(f"[OK] Estación encontrada en {ip} (código {r.status_code})")
            return ip
        except Exception:
            pass
        try:
            r = requests.get(f"http://{ip}/get_livedata_info", timeout=3)
            if r.status_code == 200:
                print(f"[OK] API encontrada en {ip}/get_livedata_info")
                return ip
        except Exception:
            pass

    print("[!] No se encontró interfaz HTTP. Intentando UDP...")
    return None


def leer_datos_http(ip):
    """Lee datos de la estación via HTTP si tiene API local"""
    endpoints = [
        "/get_livedata_info",
        "/livedata.htm",
        "/weather_data",
        "/api/data",
        "/data",
    ]
    for endpoint in endpoints:
        try:
            r = requests.get(f"http://{ip}{endpoint}", timeout=5)
            if r.status_code == 200:
                print(f"[OK] Datos obtenidos desde {endpoint}")
                return r.text
        except Exception:
            pass
    return None


def configurar_wifi_udp(ssid_casa, password_casa, servidor_ip, servidor_puerto):
    """
    Envía configuración WiFi a la estación via UDP broadcast.
    Protocolo compatible con Fine Offset / Ecowitt.
    """
    print(f"\n[+] Enviando configuración WiFi via UDP...")
    print(f"    Red destino: {ssid_casa}")
    print(f"    Servidor: {servidor_ip}:{servidor_puerto}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(5)

    # Paquete de configuración Ecowitt
    cmd = 0x11  # CMD_WRITE_SSID
    ssid_bytes = ssid_casa.encode('utf-8')
    pass_bytes = password_casa.encode('utf-8')
    srv_bytes = servidor_ip.encode('utf-8')

    payload = (
        bytes([len(ssid_bytes)]) + ssid_bytes +
        bytes([len(pass_bytes)]) + pass_bytes +
        bytes([len(srv_bytes)]) + srv_bytes +
        struct.pack('>H', servidor_puerto)
    )

    size = len(payload) + 3
    checksum = (cmd + size + sum(payload)) & 0xFF
    packet = bytes([0xFF, 0xFF, cmd, size]) + payload + bytes([checksum])

    puertos_udp = [46000, 45000, 4210]
    for puerto in puertos_udp:
        try:
            sock.sendto(packet, ('255.255.255.255', puerto))
            sock.sendto(packet, ('192.168.4.255', puerto))
            print(f"[OK] Paquete UDP enviado al puerto {puerto}")
        except Exception as e:
            print(f"[!] Error en puerto {puerto}: {e}")

    sock.close()


def configurar_via_http(ip, ssid_casa, password_casa, servidor_ip, servidor_puerto):
    """Configura la estación via HTTP si tiene interfaz web"""
    print(f"\n[+] Intentando configurar via HTTP en {ip}...")

    # Datos de configuración
    config = {
        'ssid': ssid_casa,
        'password': password_casa,
        'server_ip': servidor_ip,
        'server_port': str(servidor_puerto),
        'path': '/data/report/',
        'protocol': 'ecowitt',
        'interval': '60'
    }

    endpoints_config = [
        '/set_wifi',
        '/wifi_config',
        '/config',
        '/setup',
    ]

    for endpoint in endpoints_config:
        try:
            r = requests.post(f"http://{ip}{endpoint}", data=config, timeout=5)
            if r.status_code in [200, 302]:
                print(f"[OK] Configuración enviada via {endpoint}")
                return True
        except Exception:
            pass
        try:
            r = requests.get(
                f"http://{ip}{endpoint}",
                params=config, timeout=5
            )
            if r.status_code in [200, 302]:
                print(f"[OK] Configuración enviada via GET {endpoint}")
                return True
        except Exception:
            pass

    return False


def main():
    print("=" * 55)
    print("  CONFIGURADOR DE ESTACIÓN CLIMÁTICA SAINLOGIC")
    print("=" * 55)

    if not CONTRASENA_CASA:
        contrasena = input(f"\nIngresa la contraseña de '{WIFI_CASA}': ").strip()
    else:
        contrasena = CONTRASENA_CASA

    print(f"\n[1] Conectando al hotspot de la estación...")
    conectar_wifi(SAINLOGIC_SSID)
    time.sleep(5)  # Esperar a que se establezca la conexión

    print(f"\n[2] Buscando la estación en la red...")
    ip_estacion = escanear_estacion()

    if ip_estacion:
        print(f"\n[3] Leyendo datos actuales...")
        datos = leer_datos_http(ip_estacion)
        if datos:
            print(f"    Datos: {datos[:200]}...")

        print(f"\n[4] Configurando WiFi y servidor...")
        configurar_via_http(ip_estacion, WIFI_CASA, contrasena, IP_SERVIDOR, PUERTO_SERVIDOR)
    else:
        print(f"\n[3] Usando configuración UDP (broadcast)...")

    # Siempre envía UDP como respaldo
    configurar_wifi_udp(WIFI_CASA, contrasena, IP_SERVIDOR, PUERTO_SERVIDOR)

    print(f"\n[5] Esperando que la estación se configure (15 seg)...")
    time.sleep(15)

    print(f"\n[6] Reconectando a tu WiFi de casa...")
    conectar_wifi(WIFI_CASA)
    time.sleep(5)

    print("\n" + "=" * 55)
    print("  PROCESO COMPLETADO")
    print("=" * 55)
    print(f"\nLa estación debería estar enviando datos a:")
    print(f"  http://{IP_SERVIDOR}:{PUERTO_SERVIDOR}/data/report/")
    print(f"\nAhora ejecuta: python app.py")
    print(f"Y abre: http://localhost:{PUERTO_SERVIDOR}")


if __name__ == "__main__":
    main()
