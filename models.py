import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "clima.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lecturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            temp_exterior REAL,
            temp_interior REAL,
            humedad_exterior REAL,
            humedad_interior REAL,
            velocidad_viento REAL,
            rafaga_viento REAL,
            direccion_viento INTEGER,
            lluvia_hora REAL,
            lluvia_dia REAL,
            lluvia_evento REAL,
            presion_relativa REAL,
            presion_absoluta REAL,
            uv_index INTEGER,
            radiacion_solar REAL,
            punto_rocio REAL,
            sensacion_termica REAL,
            passkey TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("[DB] Base de datos inicializada correctamente")


def fahrenheit_a_celsius(f):
    if f is None:
        return None
    try:
        return round((float(f) - 32) * 5 / 9, 1)
    except Exception:
        return None


def mph_a_kmh(mph):
    if mph is None:
        return None
    try:
        return round(float(mph) * 1.60934, 1)
    except Exception:
        return None


def pulgadas_a_mm(pulgadas):
    if pulgadas is None:
        return None
    try:
        return round(float(pulgadas) * 25.4, 2)
    except Exception:
        return None


def inhg_a_hpa(inhg):
    if inhg is None:
        return None
    try:
        return round(float(inhg) * 33.8639, 1)
    except Exception:
        return None


def aplicar_compensacion_termica(temp_c, radiacion, viento_kmh):
    """
    Algoritmo de compensación térmica por calentamiento de la carcasa plástica.
    temp_c: Temperatura exterior en °C
    radiacion: Radiación solar en W/m²
    viento_kmh: Velocidad del viento en km/h
    """
    if temp_c is None or radiacion is None or viento_kmh is None:
        return temp_c
    
    try:
        rad = float(radiacion)
        viento = float(viento_kmh)
        temp = float(temp_c)
        
        offset = 0.0
        # Solo aplicar compensación si hay sol fuerte (radiación > 300 W/m²)
        if rad > 800:
            if viento < 3: offset = 2.0
            elif viento < 10: offset = 1.0
            else: offset = 0.5
        elif rad > 500:
            if viento < 5: offset = 1.0
            elif viento < 15: offset = 0.5
        elif rad > 300:
            if viento < 5: offset = 0.5
            
        return round(temp - offset, 1)
    except Exception:
        return temp_c


def guardar_lectura(datos_raw):
    """Convierte unidades, aplica calibración y guarda en la BD"""
    conn = get_db()
    try:
        # Conversiones base
        temp_ext_raw = fahrenheit_a_celsius(datos_raw.get('tempf'))
        radiacion_solar = datos_raw.get('solarradiation')
        viento_vel = mph_a_kmh(datos_raw.get('windspeedmph'))
        sensacion_raw = fahrenheit_a_celsius(datos_raw.get('feelslikef'))
        
        # Aplicar calibración térmica a la temperatura exterior
        temp_ext_calibrada = aplicar_compensacion_termica(temp_ext_raw, radiacion_solar, viento_vel)
        
        # También ajustamos la sensación térmica proporcionalmente al offset
        offset_aplicado = (temp_ext_raw - temp_ext_calibrada) if (temp_ext_raw and temp_ext_calibrada) else 0
        sensacion_calibrada = round(sensacion_raw - offset_aplicado, 1) if sensacion_raw else None
        conn.execute("""
            INSERT INTO lecturas (
                temp_exterior, temp_interior,
                humedad_exterior, humedad_interior,
                velocidad_viento, rafaga_viento, direccion_viento,
                lluvia_hora, lluvia_dia, lluvia_evento,
                presion_relativa, presion_absoluta,
                uv_index, radiacion_solar,
                punto_rocio, sensacion_termica,
                passkey
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            temp_ext_calibrada,
            fahrenheit_a_celsius(datos_raw.get('tempinf')),
            datos_raw.get('humidity'),
            datos_raw.get('humidityin'),
            viento_vel,
            mph_a_kmh(datos_raw.get('windgustmph')),
            datos_raw.get('winddir'),
            pulgadas_a_mm(datos_raw.get('rainratein')),
            pulgadas_a_mm(datos_raw.get('dailyrainin')),
            pulgadas_a_mm(datos_raw.get('eventrainin')),
            inhg_a_hpa(datos_raw.get('baromrelin')),
            inhg_a_hpa(datos_raw.get('baromabsin')),
            datos_raw.get('uv'),
            radiacion_solar,
            fahrenheit_a_celsius(datos_raw.get('dewptf')),
            sensacion_calibrada,
            datos_raw.get('PASSKEY', 'desconocido')
        ))
        conn.commit()
        print(f"[DB] Lectura guardada OK")
    except Exception as e:
        print(f"[DB] Error guardando: {e}")
    finally:
        conn.close()


def obtener_ultima_lectura():
    conn = get_db()
    row = conn.execute("""
        SELECT * FROM lecturas ORDER BY timestamp DESC LIMIT 1
    """).fetchone()
    conn.close()
    return dict(row) if row else None


def obtener_historial(horas=24):
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM lecturas
        WHERE timestamp >= datetime('now', ?)
        ORDER BY timestamp ASC
    """, (f'-{horas} hours',)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def obtener_stats_dia():
    conn = get_db()
    row = conn.execute("""
        SELECT
            MAX(temp_exterior) as temp_max,
            MIN(temp_exterior) as temp_min,
            MAX(humedad_exterior) as hum_max,
            MIN(humedad_exterior) as hum_min,
            MAX(velocidad_viento) as viento_max,
            MAX(rafaga_viento) as rafaga_max,
            MAX(lluvia_dia) as lluvia_total,
            MAX(uv_index) as uv_max
        FROM lecturas
        WHERE timestamp >= datetime('now', '-24 hours')
    """).fetchone()
    conn.close()
    return dict(row) if row else {}


def obtener_stats_agrupadas():
    """Obtiene agregaciones por semana y mes para análisis comparativo de texto"""
    conn = get_db()
    # Estadísticas por mes y año
    mensual = conn.execute("""
        SELECT 
            strftime('%Y-%m', timestamp) as mes,
            MAX(temp_exterior) as temp_max,
            MIN(temp_exterior) as temp_min,
            MAX(lluvia_dia) as lluvia_max_diaria,
            SUM(lluvia_hora) as estimacion_lluvia_total -- aproxima el acumulado si tomamos muestras por hora
        FROM lecturas
        GROUP BY mes
        ORDER BY mes DESC
        LIMIT 12
    """).fetchall()
    
    # Estadísticas por semana del año
    semanal = conn.execute("""
        SELECT 
            strftime('%Y-%W', timestamp) as semana,
            MAX(temp_exterior) as temp_max,
            MIN(temp_exterior) as temp_min,
            MAX(lluvia_dia) as lluvia_max_diaria
        FROM lecturas
        GROUP BY semana
        ORDER BY semana DESC
        LIMIT 12
    """).fetchall()
    
    conn.close()
    return {
        "mensual": [dict(r) for r in mensual],
        "semanal": [dict(r) for r in semanal]
    }
