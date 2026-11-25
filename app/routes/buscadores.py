from flask import Blueprint, Response

bp = Blueprint('buscadores', __name__)

SITIO = 'https://www.nuestroclima.co'
PAGINAS = ['/', '/inicio', '/reporte-velez', '/privacidad']

LLMS = f"""# Nuestro Clima

> Clima en vivo de Guavatá y la provincia de Vélez (Santander, Colombia), con una estación meteorológica propia y estaciones publicas de la región.

## Qué muestra

- Temperatura, humedad, viento, lluvia, presión, radiación solar e índice UV de la estación de Guavatá, actualizados cada minuto.
- Mapa de lluvias con estaciones publicas de Guavatá, Barbosa, Vélez y Puente Nacional.
- Nubes del satélite GOES de la NASA (color natural e infrarrojo).
- Reporte semanal de la provincia de Vélez con niveles de ríos del IDEAM (FEWS).

## Páginas

- [Tablero en vivo]({SITIO}/)
- [Inicio]({SITIO}/inicio)
- [Reporte semanal Vélez]({SITIO}/reporte-velez)
- [Política de privacidad]({SITIO}/privacidad)

## Datos en JSON

- [Lectura actual]({SITIO}/api/actual)
- [Últimas 24 horas]({SITIO}/api/historial)
- [Reporte semanal]({SITIO}/api/reporte_velez)
"""


@bp.route('/robots.txt')
def robots():
    texto = f"User-agent: *\nDisallow: /admin/\nAllow: /\n\nSitemap: {SITIO}/sitemap.xml\n"
    return Response(texto, mimetype='text/plain')


@bp.route('/sitemap.xml')
def sitemap():
    urls = ''.join(f'  <url><loc>{SITIO}{ruta}</loc></url>\n' for ruta in PAGINAS)
    xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n'
    return Response(xml, mimetype='application/xml')


@bp.route('/llms.txt')
def llms():
    return Response(LLMS, mimetype='text/plain')
