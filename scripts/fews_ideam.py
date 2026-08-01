"""
Logica compartida de conexion a FEWS/IDEAM (Principio #1: siempre
server-side, nunca desde el navegador). La usan scripts/lecturas_fews_poller.py
(guarda 1 lectura diaria por estacion) y scripts/publicar_reporte_velez.py
(arma el reporte semanal a partir de esas lecturas + la alerta de rios en
vivo). Vive en un solo lugar para que ambos scripts no se desincronicen.

Los IDs de estacion, codigos SZH y nombres de rio son especificos de
Velez por ahora; se sacan a REGION_VELEZ para que agregar otra provincia
mas adelante sea llenar un diccionario nuevo, no reescribir esta logica
(ver seccion "Escalabilidad" del plan maestro).
"""
import os
import tempfile
import certifi
import requests

# fews.ideam.gov.co no envia el certificado intermedio de su cadena TLS
# (verificado en vivo: openssl s_client devuelve "unable to get local
# issuer certificate" / "unable to verify the first certificate" - el
# servidor solo manda su certificado hoja). El intermedio que falta
# ("Sectigo Public Server Authentication CA OV R36") se descargo una vez
# de forma manual desde la URL oficial publicada en la extension AIA del
# propio certificado (http://crt.sectigo.com/...) y se guardo en
# app/certs/ para no depender de que IDEAM arregle su servidor.
_CERT_INTERMEDIO_FEWS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app", "certs", "fews_ideam_intermedio_sectigo.pem",
)


def _bundle_ca_con_intermedio_fews():
    """Certifi + el intermedio faltante de FEWS, en un archivo temporal
    (verify= de requests necesita un archivo, no una lista en memoria)."""
    with open(certifi.where(), "rb") as f:
        base = f.read()
    with open(_CERT_INTERMEDIO_FEWS, "rb") as f:
        extra = f.read()
    tmp = tempfile.NamedTemporaryFile(prefix="ca_bundle_fews_", suffix=".pem", delete=False)
    tmp.write(base + b"\n" + extra)
    tmp.close()
    return tmp.name


FEWS_CA_BUNDLE = _bundle_ca_con_intermedio_fews()

FEWS_BASE = "https://fews.ideam.gov.co/visorfews/data/"
FEWS_SZH_URL = FEWS_BASE + "SZH_Alertas.json"

REGION_VELEZ = {
    "szh": {2401: "Río Suárez", 2312: "Río Carare (Minero)", 2314: "Río Opón"},
    "estaciones": {
        "24017590": {"nombre": "PTE NACIONAL", "municipio": "Puente Nacional"},
        "24017570": {"nombre": "SAN BENITO", "municipio": "San Benito"},
        "24017707": {"nombre": "SAN BENITO-24017707", "municipio": "San Benito"},
        "2401500052": {"nombre": "PUENTE GUILLERMO", "municipio": "Puente Nacional"},
        "23127020": {"nombre": "PTO ARAUJO AUTOMATICA", "municipio": "Cimitarra"},
        "23127060": {"nombre": "STA ROSA", "municipio": "Cimitarra"},
        "23127050": {"nombre": "BARREDERO FCA", "municipio": "Puerto Parra"},
        "23125120": {"nombre": "CIMITARRA", "municipio": "Cimitarra"},
        "23125040": {"nombre": "CAMPO CAPOTE", "municipio": "Puerto Parra"},
        "23125050": {"nombre": "CARARE", "municipio": "Puerto Parra"},
        "23125060": {"nombre": "ALBANIA", "municipio": "Albania"},
        "24010640": {"nombre": "BOLIVAR", "municipio": "Bolívar"},
        "24010670": {"nombre": "SUCRE", "municipio": "Sucre"},
        "24010820": {"nombre": "GUAVATA", "municipio": "Guavatá"},
        "0019682": {"nombre": "CARARE DESEMBOCADURA", "municipio": "Puerto Parra"},
        "008642": {"nombre": "DESPUES RIO CARARE", "municipio": "Puerto Parra"},
    },
}

FEWS_CAPAS = {
    "nivel": FEWS_BASE + "ReporteTablaEstaciones.json",
    "caudal": FEWS_BASE + "ReporteTablaEstacionesQ.json",
    "lluvia": FEWS_BASE + "ReporteTablaEstacionesPobs.json",
    "temp": FEWS_BASE + "ReporteTablaEstacionesTobs.json",
}


def id_normalizado(valor):
    return str(valor).lstrip("0") or "0"


def consultar_fews_capa(nombre_capa):
    try:
        r = requests.get(FEWS_CAPAS[nombre_capa], timeout=10, verify=FEWS_CA_BUNDLE)
        r.raise_for_status()
        features = r.json().get("features", [])
        ids_velez = {id_normalizado(i) for i in REGION_VELEZ["estaciones"]}
        return {
            id_normalizado(f["properties"].get("id", "")): f["properties"]
            for f in features
            if id_normalizado(f.get("properties", {}).get("id", "")) in ids_velez
        }
    except Exception as e:
        print(f"[FewsIdeam] Error consultando FEWS {nombre_capa}: {e}")
        return None


def consultar_fews_alertas():
    try:
        r = requests.get(FEWS_SZH_URL, timeout=10, verify=FEWS_CA_BUNDLE)
        r.raise_for_status()
        features = r.json().get("features", [])
        resultado = []
        for f in features:
            p = f.get("properties", {})
            if p.get("SZH") in REGION_VELEZ["szh"]:
                resultado.append({
                    "nombre": REGION_VELEZ["szh"][p["SZH"]],
                    "nivel": (p.get("umbralaler") or "Normal").lower(),
                })
        return resultado
    except Exception as e:
        print(f"[FewsIdeam] Error consultando FEWS SZH: {e}")
        return None


def valor_obs_o_sensor(props, campo_obs, campo_sen):
    """FEWS reporta 2 fuentes por dato: 'obs' (observador humano, mas
    confiable pero esporadico) y 'sen' (sensor automatico, continuo).
    Se prefiere el dato observado cuando existe; si no, se usa el del
    sensor (verificado en vivo contra el JSON real de FEWS, los nombres
    de campo no son 'valor' generico sino especificos por capa)."""
    if not props:
        return None
    return props.get(campo_obs) if props.get(campo_obs) is not None else props.get(campo_sen)


def consultar_lecturas_estaciones():
    """Trae la lectura actual (nivel/caudal/lluvia/temp) de las 16
    estaciones de Velez, tal como estan AHORA en FEWS. Se usa 1 vez al
    dia (scripts/lecturas_fews_poller.py) para ir acumulando el
    historial que el reporte semanal usa despues para calcular
    minimos/maximos con fecha."""
    capa_nivel = consultar_fews_capa("nivel") or {}
    capa_caudal = consultar_fews_capa("caudal") or {}
    capa_lluvia = consultar_fews_capa("lluvia") or {}
    capa_temp = consultar_fews_capa("temp") or {}

    filas = []
    for station_id, info in REGION_VELEZ["estaciones"].items():
        clave = id_normalizado(station_id)
        filas.append({
            "station_id": station_id,
            "municipio": info["municipio"],
            "nombre": info["nombre"],
            "nivel": valor_obs_o_sensor(capa_nivel.get(clave), "ultimonivelobs", "ultimonivelsen"),
            "caudal": valor_obs_o_sensor(capa_caudal.get(clave), "ultimoqobs", "ultimoqsen"),
            "lluvia": valor_obs_o_sensor(capa_lluvia.get(clave), "ultimodatoobs", "ultimodatosen"),
            "temp": valor_obs_o_sensor(capa_temp.get(clave), "ultimodatoobs", "ultimodatosen"),
        })
    return filas
