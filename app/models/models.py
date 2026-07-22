from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from datetime import datetime, timedelta

db = SQLAlchemy()

class Lectura(db.Model):
    __tablename__ = 'lecturas'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    temp_exterior = db.Column(db.Float)
    temp_interior = db.Column(db.Float)
    humedad_exterior = db.Column(db.Float)
    humedad_interior = db.Column(db.Float)
    velocidad_viento = db.Column(db.Float)
    rafaga_viento = db.Column(db.Float)
    direccion_viento = db.Column(db.Integer)
    lluvia_hora = db.Column(db.Float)
    lluvia_dia = db.Column(db.Float)
    lluvia_evento = db.Column(db.Float)
    presion_relativa = db.Column(db.Float)
    presion_absoluta = db.Column(db.Float)
    uv_index = db.Column(db.Integer)
    radiacion_solar = db.Column(db.Float)
    punto_rocio = db.Column(db.Float)
    sensacion_termica = db.Column(db.Float)
    passkey = db.Column(db.String(100))

    def __init__(self, temp_exterior=None, temp_interior=None, humedad_exterior=None,
                 humedad_interior=None, velocidad_viento=None, rafaga_viento=None,
                 direccion_viento=None, lluvia_hora=None, lluvia_dia=None,
                 lluvia_evento=None, presion_relativa=None, presion_absoluta=None,
                 uv_index=None, radiacion_solar=None, punto_rocio=None,
                 sensacion_termica=None, passkey=None):
        self.temp_exterior = temp_exterior
        self.temp_interior = temp_interior
        self.humedad_exterior = humedad_exterior
        self.humedad_interior = humedad_interior
        self.velocidad_viento = velocidad_viento
        self.rafaga_viento = rafaga_viento
        self.direccion_viento = direccion_viento
        self.lluvia_hora = lluvia_hora
        self.lluvia_dia = lluvia_dia
        self.lluvia_evento = lluvia_evento
        self.presion_relativa = presion_relativa
        self.presion_absoluta = presion_absoluta
        self.uv_index = uv_index
        self.radiacion_solar = radiacion_solar
        self.punto_rocio = punto_rocio
        self.sensacion_termica = sensacion_termica
        self.passkey = passkey

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() + "Z" if self.timestamp else None,
            'temp_exterior': self.temp_exterior,
            'temp_interior': self.temp_interior,
            'humedad_exterior': self.humedad_exterior,
            'humedad_interior': self.humedad_interior,
            'velocidad_viento': self.velocidad_viento,
            'rafaga_viento': self.rafaga_viento,
            'direccion_viento': self.direccion_viento,
            'lluvia_hora': self.lluvia_hora,
            'lluvia_dia': self.lluvia_dia,
            'lluvia_evento': self.lluvia_evento,
            'presion_relativa': self.presion_relativa,
            'presion_absoluta': self.presion_absoluta,
            'uv_index': self.uv_index,
            'radiacion_solar': self.radiacion_solar,
            'punto_rocio': self.punto_rocio,
            'sensacion_termica': self.sensacion_termica,
            'passkey': self.passkey
        }


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
    if temp_c is None or radiacion is None or viento_kmh is None:
        return temp_c
    
    try:
        rad = float(radiacion)
        viento = float(viento_kmh)
        temp = float(temp_c)
        
        offset = 0.0
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
    try:
        temp_ext_raw = fahrenheit_a_celsius(datos_raw.get('tempf'))
        radiacion_solar = datos_raw.get('solarradiation')
        viento_vel = mph_a_kmh(datos_raw.get('windspeedmph'))
        sensacion_raw = fahrenheit_a_celsius(datos_raw.get('feelslikef'))
        
        temp_ext_calibrada = aplicar_compensacion_termica(temp_ext_raw, radiacion_solar, viento_vel)
        
        offset_aplicado = (temp_ext_raw - temp_ext_calibrada) if (temp_ext_raw and temp_ext_calibrada) else 0
        sensacion_calibrada = round(sensacion_raw - offset_aplicado, 1) if sensacion_raw else None
        
        nueva_lectura = Lectura(
            temp_exterior=temp_ext_calibrada,
            temp_interior=fahrenheit_a_celsius(datos_raw.get('tempinf')),
            humedad_exterior=datos_raw.get('humidity'),
            humedad_interior=datos_raw.get('humidityin'),
            velocidad_viento=viento_vel,
            rafaga_viento=mph_a_kmh(datos_raw.get('windgustmph')),
            direccion_viento=datos_raw.get('winddir'),
            lluvia_hora=pulgadas_a_mm(datos_raw.get('rainratein')),
            lluvia_dia=pulgadas_a_mm(datos_raw.get('dailyrainin')),
            lluvia_evento=pulgadas_a_mm(datos_raw.get('eventrainin')),
            presion_relativa=inhg_a_hpa(datos_raw.get('baromrelin')),
            presion_absoluta=inhg_a_hpa(datos_raw.get('baromabsin')),
            uv_index=datos_raw.get('uv'),
            radiacion_solar=radiacion_solar,
            punto_rocio=fahrenheit_a_celsius(datos_raw.get('dewptf')),
            sensacion_termica=sensacion_calibrada,
            passkey=datos_raw.get('PASSKEY', 'desconocido')
        )
        
        db.session.add(nueva_lectura)
        db.session.commit()
        print(f"[DB] Lectura guardada OK")
    except Exception as e:
        db.session.rollback()
        print(f"[DB] Error guardando: {e}")


def obtener_ultima_lectura():
    lectura = Lectura.query.order_by(Lectura.timestamp.desc()).first()
    return lectura.to_dict() if lectura else None


def obtener_historial(horas=24):
    limite = datetime.utcnow() - timedelta(hours=horas)
    lecturas = Lectura.query.filter(Lectura.timestamp >= limite).order_by(Lectura.timestamp.asc()).all()
    return [l.to_dict() for l in lecturas]


def obtener_stats_dia():
    limite = datetime.utcnow() - timedelta(hours=24)
    stats = db.session.query(
        func.max(Lectura.temp_exterior).label('temp_max'),
        func.min(Lectura.temp_exterior).label('temp_min'),
        func.max(Lectura.humedad_exterior).label('hum_max'),
        func.min(Lectura.humedad_exterior).label('hum_min'),
        func.max(Lectura.velocidad_viento).label('viento_max'),
        func.max(Lectura.rafaga_viento).label('rafaga_max'),
        func.max(Lectura.lluvia_dia).label('lluvia_total'),
        func.max(Lectura.uv_index).label('uv_max')
    ).filter(Lectura.timestamp >= limite).first()
    
    if stats:
        return {
            'temp_max': stats.temp_max,
            'temp_min': stats.temp_min,
            'hum_max': stats.hum_max,
            'hum_min': stats.hum_min,
            'viento_max': stats.viento_max,
            'rafaga_max': stats.rafaga_max,
            'lluvia_total': stats.lluvia_total,
            'uv_max': stats.uv_max
        }
    return {}


def obtener_stats_agrupadas():
    """Obtiene agregaciones por semana y mes usando strftime en SQLite via func"""
    
    mensual = db.session.query(
        func.strftime('%Y-%m', Lectura.timestamp).label('mes'),
        func.max(Lectura.temp_exterior).label('temp_max'),
        func.min(Lectura.temp_exterior).label('temp_min'),
        func.max(Lectura.lluvia_dia).label('lluvia_max_diaria'),
        func.sum(Lectura.lluvia_hora).label('estimacion_lluvia_total')
    ).group_by('mes').order_by(func.strftime('%Y-%m', Lectura.timestamp).desc()).limit(12).all()
    
    semanal = db.session.query(
        func.strftime('%Y-%W', Lectura.timestamp).label('semana'),
        func.max(Lectura.temp_exterior).label('temp_max'),
        func.min(Lectura.temp_exterior).label('temp_min'),
        func.max(Lectura.lluvia_dia).label('lluvia_max_diaria')
    ).group_by('semana').order_by(func.strftime('%Y-%W', Lectura.timestamp).desc()).limit(12).all()
    
    return {
        "mensual": [
            {
                "mes": m.mes,
                "temp_max": m.temp_max,
                "temp_min": m.temp_min,
                "lluvia_max_diaria": m.lluvia_max_diaria,
                "estimacion_lluvia_total": m.estimacion_lluvia_total
            } for m in mensual
        ],
        "semanal": [
            {
                "semana": s.semana,
                "temp_max": s.temp_max,
                "temp_min": s.temp_min,
                "lluvia_max_diaria": s.lluvia_max_diaria
            } for s in semanal
        ]
    }


def obtener_analisis_historico(tipo="dias"):
    try:
        if tipo == "dias":
            query = db.session.query(
                func.strftime('%Y-%m-%d', Lectura.timestamp).label('fecha'),
                func.avg(Lectura.temp_exterior).label('temp_avg'),
                func.max(Lectura.lluvia_dia).label('lluvia_max')
            ).group_by('fecha').order_by(func.strftime('%Y-%m-%d', Lectura.timestamp).desc()).limit(30).all()
        elif tipo == "meses":
            query = db.session.query(
                func.strftime('%Y-%m', Lectura.timestamp).label('fecha'),
                func.avg(Lectura.temp_exterior).label('temp_avg'),
                func.max(Lectura.lluvia_dia).label('lluvia_max')
            ).group_by('fecha').order_by(func.strftime('%Y-%m', Lectura.timestamp).desc()).limit(12).all()
        elif tipo == "años":
            query = db.session.query(
                func.strftime('%Y', Lectura.timestamp).label('fecha'),
                func.avg(Lectura.temp_exterior).label('temp_avg'),
                func.max(Lectura.lluvia_dia).label('lluvia_max')
            ).group_by('fecha').order_by(func.strftime('%Y', Lectura.timestamp).desc()).limit(5).all()
        else:
            return []
            
        return [{"fecha": q.fecha, "temp_avg": round(q.temp_avg, 1) if q.temp_avg else 0, "lluvia": q.lluvia_max or 0} for q in query]
    except Exception as e:
        print(f"Error historico: {e}")
        return []
