"""
Envia por correo, de forma automatica, un Excel con los datos de la
semana (u otro periodo). Corre en su propio contenedor, revisando
cada hora si ya toca enviar segun REPORT_FREQUENCY.
"""
import os
import time
import smtplib
from datetime import datetime, date
from email.message import EmailMessage

import requests

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
EMAIL_TO = os.environ.get("EMAIL_TO", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", SMTP_USER)

REPORT_FREQUENCY = os.environ.get("REPORT_FREQUENCY", "weekly")  # weekly|monthly|daily
REPORT_DIAS = {"daily": 1, "weekly": 7, "monthly": 30}.get(REPORT_FREQUENCY, 7)
REPORT_HOUR_UTC = int(os.environ.get("REPORT_HOUR_UTC", "12"))  # ~7am Colombia (UTC-5)
EXPORT_URL = os.environ.get("EXPORT_URL", f"http://app:8080/api/exportar?dias={REPORT_DIAS}")


def debe_enviar_hoy(ahora):
    if ahora.hour != REPORT_HOUR_UTC:
        return False
    if REPORT_FREQUENCY == "daily":
        return True
    if REPORT_FREQUENCY == "weekly":
        return ahora.weekday() == 0  # lunes
    if REPORT_FREQUENCY == "monthly":
        return ahora.day == 1
    return False


def descargar_excel():
    r = requests.get(EXPORT_URL, timeout=30)
    r.raise_for_status()
    return r.content


def enviar_correo(adjunto_bytes, nombre_archivo):
    msg = EmailMessage()
    msg["Subject"] = f"Reporte Sistema Clima - Finca Lagunitas ({date.today().isoformat()})"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg.set_content(
        "Adjunto el reporte automatico con los datos de la estacion climatica de Finca Lagunitas.\n\n"
        "Este correo se genera y envia automaticamente, no es necesario responder."
    )
    msg.add_attachment(
        adjunto_bytes,
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=nombre_archivo,
    )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(msg)


def run():
    if not (SMTP_USER and SMTP_PASS and EMAIL_TO):
        print("[REPORTER] Faltan SMTP_USER / SMTP_PASS / EMAIL_TO, el reporter no se ejecuta.")
        return

    print(f"[REPORTER] Iniciado. Frecuencia={REPORT_FREQUENCY} hora_utc={REPORT_HOUR_UTC} destino={EMAIL_TO}")
    ultimo_envio = None
    while True:
        try:
            ahora = datetime.utcnow()
            hoy = ahora.date()
            if debe_enviar_hoy(ahora) and ultimo_envio != hoy:
                excel = descargar_excel()
                nombre = f"clima_finca_lagunitas_{hoy.isoformat()}.xlsx"
                enviar_correo(excel, nombre)
                ultimo_envio = hoy
                print(f"[REPORTER] Correo enviado a {EMAIL_TO} ({nombre})")
        except Exception as e:
            print(f"[REPORTER] Error: {e}")
        time.sleep(3600)


if __name__ == "__main__":
    run()
