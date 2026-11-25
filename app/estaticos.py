import hashlib
import os
from functools import lru_cache

from flask import current_app, request, url_for

UN_ANIO = 31536000
UNA_HORA = 3600


@lru_cache(maxsize=None)
def _huella(ruta, modificado):
    with open(ruta, 'rb') as archivo:
        return hashlib.sha256(archivo.read()).hexdigest()[:10]


def url_estatico(archivo):
    # La version sale del contenido: si el archivo cambia, cambia la URL y el navegador lo baja de nuevo.
    ruta = os.path.join(current_app.static_folder, archivo)
    try:
        version = _huella(ruta, os.path.getmtime(ruta))
    except OSError:
        return url_for('static', filename=archivo)
    return url_for('static', filename=archivo, v=version)


def cache_de_estaticos(respuesta):
    if request.endpoint != 'static' or respuesta.status_code != 200:
        return respuesta
    if request.args.get('v'):
        respuesta.headers['Cache-Control'] = f'public, max-age={UN_ANIO}, immutable'
    else:
        respuesta.headers['Cache-Control'] = f'public, max-age={UNA_HORA}'
    return respuesta
