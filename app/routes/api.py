from flask import Blueprint, request, jsonify, render_template
from app.models.models import (
    guardar_lectura, obtener_ultima_lectura, 
    obtener_historial, obtener_stats_dia, obtener_stats_agrupadas,
    obtener_analisis_historico
)
import json
from datetime import datetime

bp = Blueprint('api', __name__)

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
def recibir_datos():
    """La estación envía datos aquí cada 60 segundos"""
    if request.method == 'POST':
        datos = request.form.to_dict()
    else:
        datos = request.args.to_dict()

    if not datos:
        return "No data", 400

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Datos recibidos de la estación:")
    for k, v in datos.items():
        print(f"  {k}: {v}")

    guardar_lectura(datos)
    return "OK", 200

@bp.route('/api/actual')
def api_actual():
    datos = obtener_ultima_lectura()
    if not datos:
        return jsonify({"error": "Sin datos aún. Esperando la estación..."}), 404
        
    datos["fase_lunar"] = get_moon_phase(datetime.now())
    return jsonify(datos)

@bp.route('/api/historial')
def api_historial():
    horas = request.args.get('horas', 24, type=int)
    datos = obtener_historial(horas)
    return jsonify(datos)

@bp.route('/api/stats')
def api_stats():
    return jsonify(obtener_stats_dia())

@bp.route('/api/stats/comparative')
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
def api_test():
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

@bp.route('/api/analisis')
def api_analisis():
    tipo = request.args.get('tipo', 'dias')
    datos = obtener_analisis_historico(tipo)
    return jsonify(datos)
