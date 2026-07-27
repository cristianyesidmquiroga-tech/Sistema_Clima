"""
Utilidades de seguridad: geolocalizacion de IP (para limites de peticiones
mas estrictos fuera de Colombia) y alerta por correo cuando alguien supera
esos limites, para que se pueda revisar si es un ataque o solo una
persona comun con mala suerte.
"""
import os
import time
import ipaddress
import smtplib
from email.message import EmailMessage

import requests

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
EMAIL_TO = os.environ.get("EMAIL_TO", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", SMTP_USER)

LIMITE_HORA_COLOMBIA = os.environ.get("LIMITE_HORA_COLOMBIA", "1000 per hour")
LIMITE_HORA_EXTRANJERO = os.environ.get("LIMITE_HORA_EXTRANJERO", "50 per hour")

# Cache de IP -> pais en memoria (el pais de una IP practicamente no
# cambia, no hace falta reconsultar todo el tiempo).
_CACHE_PAIS = {}
CACHE_PAIS_TTL = 24 * 3600

# Cooldown para no mandar un correo por cada peticion bloqueada durante
# un ataque: como mucho un correo por IP cada 30 minutos.
_ULTIMA_ALERTA_POR_IP = {}
ALERTA_COOLDOWN = 30 * 60


def _es_ip_privada(ip):
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return True  # si no se puede interpretar, tratarla como confiable


def obtener_pais(ip):
    """Devuelve el codigo de pais (ej 'CO') de una IP, o None si no se
    pudo determinar. IPs privadas/locales (red interna de Docker) se
    consideran de confianza y no se consultan."""
    if not ip or _es_ip_privada(ip):
        return "LOCAL"

    ahora = time.time()
    cacheado = _CACHE_PAIS.get(ip)
    if cacheado and ahora - cacheado[1] < CACHE_PAIS_TTL:
        return cacheado[0]

    try:
        r = requests.get(f"http://ip-api.com/json/{ip}", params={"fields": "countryCode"}, timeout=3)
        pais = r.json().get("countryCode") if r.status_code == 200 else None
    except Exception:
        pais = None

    _CACHE_PAIS[ip] = (pais, ahora)
    return pais


def es_colombia(ip):
    pais = obtener_pais(ip)
    return pais in ("CO", "LOCAL")


def limite_dinamico_por_pais(ip):
    return LIMITE_HORA_COLOMBIA if es_colombia(ip) else LIMITE_HORA_EXTRANJERO


def _enviar_correo(asunto, cuerpo):
    if not (SMTP_USER and SMTP_PASS and EMAIL_TO):
        print("[Seguridad] Faltan credenciales SMTP, no se pudo enviar la alerta.")
        return
    try:
        msg = EmailMessage()
        msg["Subject"] = asunto
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO
        msg.set_content(cuerpo)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
    except Exception as e:
        print(f"[Seguridad] Error enviando correo de alerta: {e}")


def alertar_limite_excedido(ip, ruta, limite):
    """Manda un correo de alerta cuando una IP supera su limite de
    peticiones, con cooldown para no saturar el correo durante un
    ataque real (muchos bloqueos seguidos de la misma IP)."""
    ahora = time.time()
    ultima = _ULTIMA_ALERTA_POR_IP.get(ip, 0)
    if ahora - ultima < ALERTA_COOLDOWN:
        return
    _ULTIMA_ALERTA_POR_IP[ip] = ahora

    pais = obtener_pais(ip) or "desconocido"
    cuerpo = (
        f"Se bloqueo una IP por superar el limite de peticiones en Sistema Clima.\n\n"
        f"IP: {ip}\n"
        f"Pais detectado: {pais}\n"
        f"Ruta solicitada: {ruta}\n"
        f"Limite configurado: {limite}\n\n"
        f"Revisa si parece un ataque (muchas peticiones seguidas, pais raro) "
        f"o simplemente una persona comun que tuvo un problema de conexion.\n"
        f"Si vuelve a pasar seguido desde la misma IP, puede ser un ataque real."
    )
    _enviar_correo(f"[Sistema Clima] IP bloqueada por exceso de peticiones ({ip})", cuerpo)
