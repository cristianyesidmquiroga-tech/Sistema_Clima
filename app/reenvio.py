import os
import threading

import requests


def _destino():
    url = os.environ.get('PILOTO_INGESTA_URL', '').strip()
    clave = os.environ.get('PILOTO_PASSKEY', '').strip()
    if not url or not clave:
        return None, None
    return url, clave


def _enviar(url, datos):
    try:
        requests.post(url, data=datos, timeout=5)
    except requests.RequestException:
        # El piloto es secundario: si falla, la ingesta de produccion sigue.
        pass


def reenviar_al_piloto(datos):
    url, clave = _destino()
    if not url:
        return False
    copia = dict(datos)
    copia['PASSKEY'] = clave
    threading.Thread(target=_enviar, args=(url, copia), daemon=True).start()
    return True
