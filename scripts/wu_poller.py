"""
Consulta periodicamente la API de Weather Underground (PWS Observations)
y reenvia los datos al endpoint /data/report/ de esta misma app, en
formato Ecowitt, para que se guarden en la base de datos como si la
estacion los hubiera enviado directamente.

Necesario porque la estacion (Sainlogic) solo soporta subir datos a
Wunderground/Weathercloud, no a un servidor propio.
"""
import os
import time
import requests

WU_STATION_ID = os.environ.get("WU_STATION_ID", "")
WU_API_KEY = os.environ.get("WU_API_KEY", "")
POLL_INTERVAL = int(os.environ.get("WU_POLL_INTERVAL", "60"))
TARGET_URL = os.environ.get("WU_TARGET_URL", "http://app:8080/data/report/")
STATION_PASSKEY = os.environ.get("STATION_PASSKEY", "")

WU_URL = "https://api.weather.com/v2/pws/observations/current"


def fetch_wu():
    params = {
        "stationId": WU_STATION_ID,
        "format": "json",
        "units": "e",
        "apiKey": WU_API_KEY,
    }
    r = requests.get(WU_URL, params=params, timeout=15)
    if r.status_code != 200:
        print(f"[WU] HTTP {r.status_code}: {r.text[:200]}")
        return None
    data = r.json()
    obs = data.get("observations") or []
    if not obs:
        return None
    return obs[0]


def to_ecowitt(obs):
    imp = obs.get("imperial", {})
    datos = {
        "tempf": imp.get("temp"),
        "humidity": obs.get("humidity"),
        "windspeedmph": imp.get("windSpeed"),
        "windgustmph": imp.get("windGust"),
        "winddir": obs.get("winddir"),
        "rainratein": imp.get("precipRate"),
        "dailyrainin": imp.get("precipTotal"),
        "baromrelin": imp.get("pressure"),
        "uv": obs.get("uv"),
        "solarradiation": obs.get("solarRadiation"),
        "dewptf": imp.get("dewpt"),
        "feelslikef": imp.get("heatIndex") or imp.get("windChill") or imp.get("temp"),
    }
    if STATION_PASSKEY:
        datos["PASSKEY"] = STATION_PASSKEY
    return {k: v for k, v in datos.items() if v is not None}


def run():
    if not WU_STATION_ID or not WU_API_KEY:
        print("[WU] Faltan WU_STATION_ID / WU_API_KEY, el poller no se ejecuta.")
        return

    print(f"[WU] Poller iniciado. Estacion={WU_STATION_ID} intervalo={POLL_INTERVAL}s destino={TARGET_URL}")
    while True:
        try:
            obs = fetch_wu()
            if obs:
                datos = to_ecowitt(obs)
                resp = requests.post(TARGET_URL, data=datos, timeout=10)
                print(f"[WU] Reenviado -> {resp.status_code}: {datos}")
            else:
                print("[WU] Sin observaciones disponibles todavia.")
        except Exception as e:
            print(f"[WU] Error: {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()
