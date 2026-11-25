"""
Sella cada hora en la red SNA una huella con todas las lecturas de la
estacion de esa hora, para poder probar despues que no se cambiaron.
Uso para verificar: python -m scripts.sellador_horas verificar 2026-11-25T14
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.latido import dormir, latir

APP = "clima"
INTERVALO = int(os.environ.get("SELLO_INTERVALO", "3600"))
HORAS_ATRAS = int(os.environ.get("SELLO_HORAS_ATRAS", "48"))
MARGEN = timedelta(minutes=10)
ABI = json.loads((Path(__file__).parent / "abi" / "RegistroHuellas.json").read_text(encoding="utf-8"))


def config():
    nombres = ("SNA_RPC_URL", "SNA_RPC_USUARIO", "SNA_RPC_CLAVE", "SNA_REGISTRO", "SNA_LLAVE_SELLADORA", "SELLO_SAL")
    valores = {n: os.environ.get(n, "") for n in nombres}
    faltan = [n for n, v in valores.items() if not v]
    return valores, faltan


def huella(texto, sal):
    from web3 import Web3
    sal = sal.encode("utf-8")
    if len(sal) < 32:
        raise ValueError("SELLO_SAL debe tener al menos 32 caracteres")
    return Web3.keccak(sal + texto.encode("utf-8"))


def horas_pendientes(ahora, horas_atras=HORAS_ATRAS):
    ultima = (ahora - MARGEN).replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
    return [ultima - timedelta(hours=i) for i in range(horas_atras - 1, -1, -1)]


class Registro:
    def __init__(self, cfg):
        from eth_account import Account
        from web3 import Web3
        self.w3 = Web3(Web3.HTTPProvider(cfg["SNA_RPC_URL"], request_kwargs={
            "auth": (cfg["SNA_RPC_USUARIO"], cfg["SNA_RPC_CLAVE"]), "timeout": 30}))
        self.contrato = self.w3.eth.contract(address=Web3.to_checksum_address(cfg["SNA_REGISTRO"]), abi=ABI)
        self.cuenta = Account.from_key(cfg["SNA_LLAVE_SELLADORA"])
        self.app = Web3.keccak(text=APP)

    def sellada(self, h):
        return self.contrato.functions.consultar(self.app, h).call()[1] != 0

    def sellar(self, h):
        tx = self.contrato.functions.sellar(self.app, h).build_transaction({
            "from": self.cuenta.address,
            "nonce": self.w3.eth.get_transaction_count(self.cuenta.address),
        })
        firmada = self.cuenta.sign_transaction(tx)
        recibo = self.w3.eth.wait_for_transaction_receipt(self.w3.eth.send_raw_transaction(firmada.raw_transaction))
        if recibo["status"] != 1:
            raise RuntimeError("la transaccion fue revertida")


def sellar_pendientes(registro, sal, horas, lecturas_de_hora, texto_de_hora):
    selladas = 0
    for inicio in horas:
        lecturas = lecturas_de_hora(inicio)
        if not lecturas:
            continue
        h = huella(texto_de_hora(lecturas), sal)
        if not registro.sellada(h):
            registro.sellar(h)
            selladas += 1
    return selladas


def run():
    cfg, faltan = config()
    if faltan:
        print(f"[Sello] Faltan {', '.join(faltan)}; no se sella nada.")
    from app import create_app
    from app.models.sellos import lecturas_de_hora, texto_de_hora
    app = create_app()
    registro = None
    while True:
        if not faltan:
            try:
                registro = registro or Registro(cfg)
                with app.app_context():
                    n = sellar_pendientes(registro, cfg["SELLO_SAL"], horas_pendientes(datetime.utcnow()),
                                          lecturas_de_hora, texto_de_hora)
                print(f"[Sello] {n} horas selladas")
                latir()
            except Exception as e:
                registro = None
                print(f"[Sello] Error: {e}")
        dormir(INTERVALO, latiendo=bool(faltan))


def verificar(hora):
    cfg, faltan = config()
    if faltan:
        sys.exit(f"Faltan {', '.join(faltan)}")
    from app import create_app
    from app.models.sellos import lecturas_de_hora, texto_de_hora
    inicio = datetime.strptime(hora, "%Y-%m-%dT%H")
    with create_app().app_context():
        lecturas = lecturas_de_hora(inicio)
    h = huella(texto_de_hora(lecturas), cfg["SELLO_SAL"])
    print("sellada e intacta" if Registro(cfg).sellada(h) else "sin sello o con datos cambiados")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "verificar":
        verificar(sys.argv[2])
    else:
        run()
