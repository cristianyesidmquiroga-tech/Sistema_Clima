from datetime import datetime, timedelta

from app.models.models import HistorialEstacion

COLOMBIA = timedelta(hours=-5)


def a_hora_local(momento):
    return momento + COLOMBIA


def _extremo(filas, campo, mayor):
    elegido = None
    for fila in filas:
        valor = getattr(fila, campo)
        if valor is None:
            continue
        if elegido is None or (valor > elegido[0] if mayor else valor < elegido[0]):
            elegido = (valor, fila.timestamp)
    if elegido is None:
        return None
    local = a_hora_local(elegido[1])
    return {'valor': round(elegido[0], 1), 'dia': local.date().isoformat(),
            'hora': local.strftime('%H:%M')}


def _por_dia(filas):
    dias = {}
    for fila in filas:
        dias.setdefault(a_hora_local(fila.timestamp).date().isoformat(), []).append(fila)

    resultado = []
    for dia in sorted(dias):
        grupo = dias[dia]
        maxima = _extremo(grupo, 'temp_max', True)
        minima = _extremo(grupo, 'temp_min', False)
        humedad_max = _extremo(grupo, 'humedad_max', True)
        humedad_min = _extremo(grupo, 'humedad_min', False)
        rafaga = _extremo(grupo, 'rafaga_max', True)
        resultado.append({
            'dia': dia,
            'horas': len(grupo),
            'temp_max': maxima and maxima['valor'],
            'temp_min': minima and minima['valor'],
            'humedad_max': humedad_max and humedad_max['valor'],
            'humedad_min': humedad_min and humedad_min['valor'],
            'rafaga_max': rafaga and rafaga['valor'],
            'lluvia_mm': round(sum(f.lluvia_mm or 0 for f in grupo), 1),
        })
    return resultado


def resumen_semanal(filas):
    filas = sorted(filas, key=lambda f: f.timestamp)
    if not filas:
        return {'disponible': False}

    por_dia = _por_dia(filas)
    lluvioso = max(por_dia, key=lambda d: d['lluvia_mm'])
    total_lluvia = round(sum(d['lluvia_mm'] for d in por_dia), 1)

    return {
        'disponible': True,
        'desde': por_dia[0]['dia'],
        'hasta': por_dia[-1]['dia'],
        'por_dia': por_dia,
        'extremos': {
            'temperatura': {'max': _extremo(filas, 'temp_max', True),
                            'min': _extremo(filas, 'temp_min', False)},
            'humedad': {'max': _extremo(filas, 'humedad_max', True),
                        'min': _extremo(filas, 'humedad_min', False)},
            'rafaga': {'max': _extremo(filas, 'rafaga_max', True)},
            'presion': {'max': _extremo(filas, 'presion_max', True),
                        'min': _extremo(filas, 'presion_min', False)},
            'uv': {'max': _extremo(filas, 'uv_max', True)},
            'lluvia': {'total': total_lluvia,
                       'dia_mas_lluvioso': ({'valor': lluvioso['lluvia_mm'], 'dia': lluvioso['dia']}
                                            if lluvioso['lluvia_mm'] > 0 else None)},
        },
    }


def obtener_resumen_semanal(station_id, dias=7):
    limite = datetime.utcnow() - timedelta(days=dias)
    filas = HistorialEstacion.query.filter(
        HistorialEstacion.station_id == station_id,
        HistorialEstacion.timestamp >= limite,
    ).all()
    return resumen_semanal(filas)
