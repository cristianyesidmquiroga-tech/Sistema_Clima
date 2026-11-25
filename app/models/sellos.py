from datetime import timedelta

from app.models.models import Lectura

# Orden fijo: si cambia, las huellas ya selladas dejan de poder verificarse.
CAMPOS_SELLADOS = (
    "temp_exterior", "humedad_exterior", "velocidad_viento", "rafaga_viento",
    "direccion_viento", "lluvia_hora", "lluvia_dia", "lluvia_evento",
    "presion_relativa", "presion_absoluta", "uv_index", "radiacion_solar",
    "punto_rocio", "sensacion_termica",
)


def _valor(v):
    return "" if v is None else repr(v)


def texto_de_hora(lecturas):
    lineas = []
    for lec in sorted(lecturas, key=lambda x: (x.timestamp, x.id)):
        campos = [str(lec.id), lec.timestamp.isoformat()]
        campos += [_valor(getattr(lec, c)) for c in CAMPOS_SELLADOS]
        lineas.append("|".join(campos))
    return "\n".join(lineas)


def lecturas_de_hora(inicio):
    return Lectura.query.filter(
        Lectura.timestamp >= inicio, Lectura.timestamp < inicio + timedelta(hours=1)
    ).all()
