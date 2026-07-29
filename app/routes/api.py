import os
import io
import hmac
import requests
from flask import Blueprint, request, jsonify, render_template, send_file
from openpyxl import Workbook
from app import limiter, cache
from app.models.models import (
    guardar_lectura, obtener_ultima_lectura,
    obtener_historial, obtener_stats_dia, obtener_stats_agrupadas,
    obtener_analisis_historico, obtener_datos_por_fecha, obtener_lecturas_rango,
    obtener_rafaga_maxima_reciente, obtener_velocidad_viento_promedio_reciente,
    obtener_historial_estacion, obtener_resumen_semana
)
from datetime import datetime

bp = Blueprint('api', __name__)

STATION_PASSKEY = os.environ.get('STATION_PASSKEY', '')
ENABLE_TEST_ENDPOINT = os.environ.get('ENABLE_TEST_ENDPOINT', 'false').lower() == 'true'
WU_API_KEY = os.environ.get('WU_API_KEY', '')

FINCA_LAT = 5.96
FINCA_LON = -73.63

# Estaciones publicas de Wunderground para el mapa de lluvias de la region
# (Guavata, Velez, Barbosa, Puente Nacional). No requieren ser propias:
# la API de lectura de WU permite consultar cualquier estacion publica
# con una sola API Key.
ESTACIONES_MAPA_LLUVIAS = [
    {"id": "IGUAVA3",  "nombre": "Guavatá (nuestra)"},
    {"id": "IBARBO1",  "nombre": "Barbosa 1"},
    {"id": "IBARBO2",  "nombre": "Barbosa 2"},
    {"id": "IVLEZ2",   "nombre": "Vélez 1"},
    {"id": "IVLEZ7",   "nombre": "Vélez 2"},
    {"id": "IPUENT49", "nombre": "Puente Nacional"},
]

CACHE_MAPA_LLUVIAS_TTL = 90  # segundos, cacheado en Redis via @cache.cached


def _nivel_lluvia(mm_hr):
    """Clasifica segun la TASA de lluvia actual (mm/h), no el acumulado
    del dia: asi que en cuanto para de llover, la estacion vuelve a
    'sin_lluvia' sola, sin esperar a que pase la medianoche."""
    if mm_hr is None:
        return "sin_dato"
    if mm_hr <= 0:
        return "sin_lluvia"
    if mm_hr <= 2.5:
        return "bajo"
    if mm_hr <= 7.5:
        return "moderado"
    if mm_hr <= 15:
        return "alto"
    return "muy_alto"


def _consultar_estacion_wu(station_id):
    r = requests.get(
        "https://api.weather.com/v2/pws/observations/current",
        params={"stationId": station_id, "format": "json", "units": "m", "apiKey": WU_API_KEY},
        timeout=8,
    )
    r.raise_for_status()
    obs = (r.json().get("observations") or [None])[0]
    return obs
DATOS_DESACTUALIZADOS_MIN = 15


def obtener_estimado_open_meteo():
    """Clima actual aproximado (Open-Meteo) para usar cuando la estacion no reporta."""
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": FINCA_LAT,
                "longitude": FINCA_LON,
                "current": "temperature_2m,relative_humidity_2m,precipitation,"
                           "wind_speed_10m,wind_direction_10m,surface_pressure,uv_index",
                "timezone": "America/Bogota",
            },
            timeout=5,
        )
        r.raise_for_status()
        cur = r.json().get("current", {})
        return {
            "temp_exterior": cur.get("temperature_2m"),
            "humedad_exterior": cur.get("relative_humidity_2m"),
            "velocidad_viento": cur.get("wind_speed_10m"),
            "direccion_viento": cur.get("wind_direction_10m"),
            "presion_relativa": cur.get("surface_pressure"),
            "uv_index": cur.get("uv_index"),
            "lluvia_hora": cur.get("precipitation"),
        }
    except Exception:
        return None

def get_moon_phase(date):
    """Calcula la fase lunar aproximada (0-7)"""
    year = date.year
    month = date.month
    day = date.day
    if month < 3:
        year -= 1
        month += 12
    month += 1
    c = 365.25 * year
    e = 30.6 * month
    jd = c + e + day - 694039.09
    jd /= 29.5305882
    b = int(jd)
    jd -= b
    b = round(jd * 8)
    if b >= 8: b = 0
    return b

@bp.route('/data/report/', methods=['POST', 'GET'])
@limiter.limit("120 per hour")
def recibir_datos():
    """La estación envía datos aquí cada 60 segundos"""
    if request.method == 'POST':
        datos = request.form.to_dict()
    else:
        datos = request.args.to_dict()

    if not datos:
        return "No data", 400

    if STATION_PASSKEY and not hmac.compare_digest(str(datos.get('PASSKEY', '')), STATION_PASSKEY):
        return "Forbidden", 403

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Datos recibidos de la estación:")
    for k, v in datos.items():
        print(f"  {k}: {v}")

    guardar_lectura(datos)
    return "OK", 200

@bp.route('/api/actual')
@limiter.limit("300 per hour")
def api_actual():
    datos = obtener_ultima_lectura()
    if not datos:
        return jsonify({"error": "Sin datos aún. Esperando la estación..."}), 404

    datos["fase_lunar"] = get_moon_phase(datetime.now())

    timestamp = datos.get("timestamp")
    edad_min = None
    if timestamp:
        try:
            ts = timestamp[:-1] if timestamp.endswith("Z") else timestamp
            edad_min = (datetime.utcnow() - datetime.fromisoformat(ts)).total_seconds() / 60
        except Exception:
            edad_min = None

    if edad_min is not None and edad_min > DATOS_DESACTUALIZADOS_MIN:
        estimado = obtener_estimado_open_meteo()
        if estimado:
            datos.update(estimado)
            datos["fuente"] = "estimado"
            datos["ultimo_dato_real"] = timestamp
        else:
            datos["fuente"] = "real_desactualizado"
    else:
        datos["fuente"] = "real"
        rafaga_reciente = obtener_rafaga_maxima_reciente(15)
        if rafaga_reciente is not None:
            datos["rafaga_viento"] = max(rafaga_reciente, datos.get("rafaga_viento") or 0)
        velocidad_reciente = obtener_velocidad_viento_promedio_reciente(15)
        if velocidad_reciente is not None:
            datos["velocidad_viento"] = round(velocidad_reciente, 1)

    return jsonify(datos)

@bp.route('/api/historial')
@limiter.limit("150 per hour")
@cache.cached(timeout=60, query_string=True)
def api_historial():
    horas = request.args.get('horas', 24, type=int)
    horas = max(1, min(horas, 24 * 30))
    datos = obtener_historial(horas)
    return jsonify(datos)

@bp.route('/api/stats')
@limiter.limit("150 per hour")
@cache.cached(timeout=60)
def api_stats():
    return jsonify(obtener_stats_dia())

@bp.route('/api/stats/comparative')
@limiter.limit("150 per hour")
@cache.cached(timeout=300)
def api_stats_comparative():
    stats = obtener_stats_agrupadas()
    
    analisis_texto = []
    
    if len(stats["semanal"]) >= 2:
        lluvia_s1 = stats["semanal"][0]["lluvia_max_diaria"] or 0
        lluvia_s2 = stats["semanal"][1]["lluvia_max_diaria"] or 0
        
        if lluvia_s1 > lluvia_s2:
            analisis_texto.append(f"En esta semana (Semana {stats['semanal'][0]['semana'].split('-')[1]}) ha llovido más que en la semana pasada.")
        elif lluvia_s1 < lluvia_s2:
            analisis_texto.append(f"La semana pasada llovió más que esta semana.")
            
    if len(stats["mensual"]) >= 2:
        temp_m1 = stats["mensual"][0]["temp_max"] or 0
        temp_m2 = stats["mensual"][1]["temp_max"] or 0
        
        if temp_m1 > temp_m2:
            analisis_texto.append(f"Este mes ha sido más caluroso que el mes anterior (Max {temp_m1}°C vs {temp_m2}°C).")
        elif temp_m1 < temp_m2:
            analisis_texto.append(f"El mes anterior fue más caluroso que este mes.")

    return jsonify({
        "datos": stats,
        "analisis": analisis_texto
    })

@bp.route('/api/test')
@limiter.limit("30 per hour")
def api_test():
    if not ENABLE_TEST_ENDPOINT:
        return jsonify({"error": "Endpoint deshabilitado"}), 404

    datos_prueba = {
        'tempf': '82.5',
        'tempinf': '71.0',
        'humidity': '45',
        'humidityin': '63',
        'windspeedmph': '3.4',
        'windgustmph': '0.7',
        'winddir': '54',
        'rainratein': '0.0',
        'dailyrainin': '0.57',
        'eventrainin': '0.0',
        'baromrelin': '29.92',
        'baromabsin': '28.00',
        'uv': '8',
        'solarradiation': '940',
        'dewptf': '59.0',
        'feelslikef': '82.3',
        'PASSKEY': 'TEST-SAINLOGIC'
    }
    guardar_lectura(datos_prueba)
    return jsonify({"mensaje": "Datos de prueba guardados OK"})

@bp.route('/')
def dashboard():
    return render_template('index.html')

@bp.route('/api/mapa_lluvias')
@limiter.limit("60 per hour")
@cache.cached(timeout=CACHE_MAPA_LLUVIAS_TTL)
def api_mapa_lluvias():
    if not WU_API_KEY:
        return jsonify([])

    resultado = []
    for est in ESTACIONES_MAPA_LLUVIAS:
        try:
            obs = _consultar_estacion_wu(est["id"])
            if not obs:
                continue
            metric = obs.get("metric", {})
            lluvia_mm = metric.get("precipTotal")
            lluvia_rate = metric.get("precipRate")
            resultado.append({
                "id": est["id"],
                "nombre": est["nombre"],
                "lat": obs.get("lat"),
                "lon": obs.get("lon"),
                # lluvia_mm es el acumulado del dia (solo informativo, se
                # muestra en el popup). El color y el parpadeo del
                # triangulo dependen de lluvia_rate (cuanto esta
                # lloviendo AHORA), asi que en cuanto para de llover
                # vuelve solo a "sin_lluvia", sin esperar a medianoche.
                "lluvia_mm": lluvia_mm,
                "nivel": _nivel_lluvia(lluvia_rate),
                "lluvia_rate": lluvia_rate,
                "temp": metric.get("temp"),
                "humedad": obs.get("humidity"),
                "viento": metric.get("windSpeed"),
                "obs_local": obs.get("obsTimeLocal"),
            })
        except Exception as e:
            print(f"[MapaLluvias] Error consultando {est['id']}: {e}")

    return jsonify(resultado)

@bp.route('/api/estacion/<station_id>/historial')
@limiter.limit("80 per hour")
@cache.cached(timeout=180, query_string=True)
def api_estacion_historial(station_id):
    ids_validos = {e["id"] for e in ESTACIONES_MAPA_LLUVIAS}
    if station_id not in ids_validos:
        return jsonify({"error": "Estacion desconocida"}), 404
    # De cara al publico solo se muestra la ultima semana. El historial
    # completo (hasta 2 anos, traido por scripts/backfill_historial_wu.py)
    # queda guardado en la base de datos para uso interno/privado.
    dias = request.args.get('dias', 7, type=int)
    dias = max(1, min(dias, 7))
    datos = obtener_historial_estacion(station_id, dias)
    return jsonify(datos)

@bp.route('/api/analisis')
@limiter.limit("80 per hour")
@cache.cached(timeout=300, query_string=True)
def api_analisis():
    tipo = request.args.get('tipo', 'dias')
    if tipo not in ('dias', 'semanas', 'meses', 'años', 'anos'):
        return jsonify({"error": "tipo invalido"}), 400
    datos = obtener_analisis_historico(tipo)
    return jsonify(datos)

@bp.route('/api/analisis/semana')
@limiter.limit("80 per hour")
@cache.cached(timeout=300)
def api_analisis_semana():
    return jsonify(obtener_resumen_semana())

@bp.route('/api/fecha')
@limiter.limit("80 per hour")
def api_fecha():
    fecha = request.args.get('fecha')
    if not fecha:
        return jsonify({"error": "Falta el parametro 'fecha' (YYYY-MM-DD)"}), 400
    datos = obtener_datos_por_fecha(fecha)
    if datos is None:
        return jsonify({"error": "Formato de fecha invalido, usa YYYY-MM-DD"}), 400
    return jsonify(datos)

COLUMNAS_EXPORTAR = [
    ("timestamp", "Fecha/Hora (UTC)"),
    ("temp_exterior", "Temp. Exterior (C)"),
    ("humedad_exterior", "Humedad Exterior (%)"),
    ("velocidad_viento", "Viento (km/h)"),
    ("rafaga_viento", "Rafaga (km/h)"),
    ("direccion_viento", "Direccion Viento (grados)"),
    ("lluvia_hora", "Lluvia por hora (mm)"),
    ("lluvia_dia", "Lluvia del dia (mm)"),
    ("presion_relativa", "Presion Relativa (hPa)"),
    ("uv_index", "Indice UV"),
    ("radiacion_solar", "Radiacion Solar (W/m2)"),
    ("punto_rocio", "Punto de Rocio (C)"),
    ("sensacion_termica", "Sensacion Termica (C)"),
]

@bp.route('/api/exportar')
@limiter.limit("20 per hour")
def api_exportar():
    dias = request.args.get('dias', 7, type=int)
    dias = max(1, min(dias, 90))
    lecturas = obtener_lecturas_rango(dias)

    wb = Workbook()
    ws = wb.active
    ws.title = "Clima"
    ws.append([titulo for _, titulo in COLUMNAS_EXPORTAR])
    for l in lecturas:
        ws.append([l.get(campo) for campo, _ in COLUMNAS_EXPORTAR])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    nombre = f"clima_finca_lagunitas_{datetime.utcnow().strftime('%Y-%m-%d')}.xlsx"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=nombre,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
