from datetime import datetime, timedelta
from app.models.models import db


# ─── MODELOS (tablas) ──────────────────────────────────────────
class ReportePublicado(db.Model):
    """
    Instantanea semanal del Reporte Provincia de Velez (clima, lluvia y
    alerta hidrologica). El publico siempre ve el ultimo registro de esta
    tabla, nunca un calculo en vivo (cadencia publica semanal). Cada fila
    queda guardada para siempre (no se sobreescribe ni se borra), asi se
    puede comparar como ha cambiado el reporte a lo largo del tiempo.
    """
    __tablename__ = 'reportes_publicados'
    id = db.Column(db.Integer, primary_key=True)
    region = db.Column(db.String(40), nullable=False, default='velez', index=True)
    fecha_publicacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    contenido = db.Column(db.JSON, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'region': self.region,
            'fecha_publicacion': self.fecha_publicacion.isoformat() + "Z" if self.fecha_publicacion else None,
            'contenido': self.contenido,
        }


class CapturaMapa(db.Model):
    """
    Archivo historico de capturas de mapas/capas (ej. satelite GOES
    GeoColor/Infrarrojo de la zona de Velez). Un registro por dia por
    capa. Pasados 3 meses, 'ruta_archivo' pasa a apuntar a un .zip
    mensual comprimido en vez del PNG individual (ver
    scripts/capturas_mapas_poller.py y docs/archivo_capturas_mapas.md) -
    los registros nunca se borran, solo cambia donde vive el archivo.
    """
    __tablename__ = 'capturas_mapas'
    id = db.Column(db.Integer, primary_key=True)
    mapa = db.Column(db.String(40), nullable=False, index=True)   # ej. 'reporte-velez'
    capa = db.Column(db.String(40), nullable=False, index=True)   # ej. 'satelite_geocolor'
    fecha_captura = db.Column(db.Date, nullable=False, index=True)
    ruta_archivo = db.Column(db.String(300), nullable=False)
    comprimido = db.Column(db.Boolean, nullable=False, default=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('mapa', 'capa', 'fecha_captura', name='uq_captura_mapa_dia'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'mapa': self.mapa,
            'capa': self.capa,
            'fecha_captura': self.fecha_captura.isoformat() if self.fecha_captura else None,
            'ruta_archivo': self.ruta_archivo,
            'comprimido': self.comprimido,
        }


class LecturaFewsDiaria(db.Model):
    """
    1 lectura por dia por estacion FEWS/IDEAM de la Provincia de Velez
    (nivel, caudal, lluvia, temp). Se guarda todos los dias (ver
    scripts/lecturas_fews_poller.py) para que el reporte semanal pueda
    calcular el minimo y el maximo real de cada municipio, con la fecha
    en que ocurrio cada uno - un solo dato en vivo no alcanza para eso.
    """
    __tablename__ = 'lecturas_fews_diarias'
    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.String(20), nullable=False, index=True)
    nombre_estacion = db.Column(db.String(80), nullable=False)
    municipio = db.Column(db.String(60), nullable=False, index=True)
    fecha = db.Column(db.Date, nullable=False, index=True)
    capturado_en = db.Column(db.DateTime, default=datetime.utcnow)
    nivel = db.Column(db.Float)
    caudal = db.Column(db.Float)
    lluvia = db.Column(db.Float)
    temp = db.Column(db.Float)

    __table_args__ = (
        db.UniqueConstraint('station_id', 'fecha', name='uq_lectura_fews_estacion_dia'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'station_id': self.station_id,
            'nombre_estacion': self.nombre_estacion,
            'municipio': self.municipio,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'nivel': self.nivel,
            'caudal': self.caudal,
            'lluvia': self.lluvia,
            'temp': self.temp,
        }


# ─── REPORTE VELEZ: ESCRITURA ────────────────────────────────────
def guardar_reporte_publicado(contenido, region='velez'):
    """Congela una instantania nueva del reporte semanal. No sobreescribe
    ni borra las anteriores (quedan como historico para comparar)."""
    reporte = ReportePublicado(region=region, contenido=contenido)
    db.session.add(reporte)
    db.session.commit()
    return reporte.to_dict()


# ─── REPORTE VELEZ: CONSULTA ─────────────────────────────────────
def obtener_ultimo_reporte_publicado(region='velez'):
    fila = ReportePublicado.query.filter_by(region=region) \
        .order_by(ReportePublicado.fecha_publicacion.desc()).first()
    return fila.to_dict() if fila else None


def obtener_historial_reportes_publicados(region='velez', limite=52):
    """Historico de reportes semanales ya publicados (uso interno, ej.
    para comparar como ha cambiado el reporte con el tiempo)."""
    filas = ReportePublicado.query.filter_by(region=region) \
        .order_by(ReportePublicado.fecha_publicacion.desc()).limit(limite).all()
    return [f.to_dict() for f in filas]


# ─── CAPTURAS DE MAPAS: ESCRITURA ─────────────────────────────────
def guardar_captura_mapa(mapa, capa, fecha_captura, ruta_archivo):
    """Registra una captura nueva del dia para ese mapa/capa. Si ya
    existe una captura ese mismo dia (ej. el poller se reinicio), se
    actualiza la ruta en vez de crear una fila duplicada."""
    existente = CapturaMapa.query.filter_by(
        mapa=mapa, capa=capa, fecha_captura=fecha_captura
    ).first()
    if existente:
        existente.ruta_archivo = ruta_archivo
        existente.comprimido = False
    else:
        existente = CapturaMapa(
            mapa=mapa, capa=capa, fecha_captura=fecha_captura, ruta_archivo=ruta_archivo
        )
        db.session.add(existente)
    db.session.commit()
    return existente.to_dict()


def marcar_capturas_comprimidas(mapa, capa, fechas, ruta_zip):
    """Tras comprimir un lote de capturas viejas en un .zip, actualiza sus
    filas para que apunten al zip en vez del PNG individual (ya borrado
    del disco). Los registros en si nunca se eliminan."""
    CapturaMapa.query.filter(
        CapturaMapa.mapa == mapa,
        CapturaMapa.capa == capa,
        CapturaMapa.fecha_captura.in_(fechas),
    ).update({'ruta_archivo': ruta_zip, 'comprimido': True}, synchronize_session=False)
    db.session.commit()


# ─── CAPTURAS DE MAPAS: CONSULTA ───────────────────────────────────
def obtener_capturas_recientes(mapa, capa, dias=90):
    """Capturas sin comprimir de los ultimos N dias (para armar el
    timelapse). Las comprimidas (>3 meses) se consultan aparte, extrayendo
    el zip correspondiente (ver docs/archivo_capturas_mapas.md)."""
    limite = (datetime.utcnow() - timedelta(days=dias)).date()
    filas = CapturaMapa.query.filter(
        CapturaMapa.mapa == mapa,
        CapturaMapa.capa == capa,
        CapturaMapa.fecha_captura >= limite,
        CapturaMapa.comprimido.is_(False),
    ).order_by(CapturaMapa.fecha_captura.asc()).all()
    return [f.to_dict() for f in filas]


def obtener_capturas_pendientes_de_comprimir(mapa, capa, dias=90):
    """Capturas sin comprimir con mas de N dias de antiguedad (candidatas
    para el proximo lote de compresion mensual)."""
    limite = (datetime.utcnow() - timedelta(days=dias)).date()
    filas = CapturaMapa.query.filter(
        CapturaMapa.mapa == mapa,
        CapturaMapa.capa == capa,
        CapturaMapa.fecha_captura < limite,
        CapturaMapa.comprimido.is_(False),
    ).order_by(CapturaMapa.fecha_captura.asc()).all()
    return [f.to_dict() for f in filas]


# ─── LECTURAS FEWS DIARIAS: ESCRITURA ──────────────────────────────
def guardar_lectura_fews_diaria(station_id, nombre_estacion, municipio, fecha, nivel, caudal, lluvia, temp):
    """1 fila por estacion por dia. Si el poller ya guardo hoy (ej. se
    reinicio), actualiza esa fila en vez de duplicarla."""
    existente = LecturaFewsDiaria.query.filter_by(station_id=station_id, fecha=fecha).first()
    if existente:
        existente.nivel = nivel
        existente.caudal = caudal
        existente.lluvia = lluvia
        existente.temp = temp
        existente.capturado_en = datetime.utcnow()
    else:
        existente = LecturaFewsDiaria(
            station_id=station_id, nombre_estacion=nombre_estacion, municipio=municipio,
            fecha=fecha, nivel=nivel, caudal=caudal, lluvia=lluvia, temp=temp,
        )
        db.session.add(existente)
    db.session.commit()
    return existente.to_dict()


# ─── LECTURAS FEWS DIARIAS: CONSULTA ────────────────────────────────
def obtener_lecturas_fews_semana(dias=7):
    limite = (datetime.utcnow() - timedelta(days=dias)).date()
    filas = LecturaFewsDiaria.query.filter(
        LecturaFewsDiaria.fecha >= limite
    ).order_by(LecturaFewsDiaria.fecha.asc()).all()
    return [f.to_dict() for f in filas]
