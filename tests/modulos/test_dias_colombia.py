from datetime import datetime

from app.models.models import (
    Lectura, Noticia, db, inicio_hoy_colombia_utc, obtener_analisis_historico, obtener_noticias_hoy,
)


def test_el_dia_empieza_a_medianoche_de_colombia():
    assert inicio_hoy_colombia_utc(datetime(2026, 11, 25, 3, 0)) == datetime(2026, 11, 24, 5, 0)
    assert inicio_hoy_colombia_utc(datetime(2026, 11, 25, 6, 0)) == datetime(2026, 11, 25, 5, 0)


def _lectura(momento_utc, lluvia_dia):
    fila = Lectura(temp_exterior=20, lluvia_dia=lluvia_dia)
    fila.timestamp = momento_utc
    db.session.add(fila)


def test_la_lluvia_de_la_noche_queda_en_su_dia_colombiano(client, sesion):
    _lectura(datetime(2026, 11, 25, 2, 0), 10)
    _lectura(datetime(2026, 11, 25, 7, 0), 1)
    db.session.commit()
    dias = {d['fecha']: d['lluvia'] for d in obtener_analisis_historico('dias')}
    assert dias == {'2026-11-24': 10, '2026-11-25': 1}


def test_una_noticia_de_las_6_de_la_tarde_sigue_siendo_de_hoy(client, sesion, monkeypatch):
    import app.models.models as modelos
    noticia = Noticia(tipo='alerta', titulo='Lluvia', texto='Fuerte')
    noticia.fecha_publicacion = datetime(2026, 11, 25, 23, 0)
    db.session.add(noticia)
    db.session.commit()
    monkeypatch.setattr(modelos, 'inicio_hoy_colombia_utc', lambda: datetime(2026, 11, 25, 5, 0))
    assert [n['titulo'] for n in obtener_noticias_hoy()] == ['Lluvia']
