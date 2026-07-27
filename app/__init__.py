from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from werkzeug.middleware.proxy_fix import ProxyFix
from app.models.models import db
from app.security import limite_dinamico_por_pais, alertar_limite_excedido
import os


def _limite_dinamico():
    return limite_dinamico_por_pais(get_remote_address())


def _en_ruptura_de_limite(request_limit):
    ip = get_remote_address()
    alertar_limite_excedido(ip, request.path, str(request_limit.limit))


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[_limite_dinamico],
    on_breach=_en_ruptura_de_limite,
)

cache = Cache()


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    # Detras de Traefik (1 solo proxy): confiar en X-Forwarded-For/Proto
    # para que request.remote_addr sea la IP real del visitante, no la
    # IP interna del proxy.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    # Redis: le da al rate-limiter un contador compartido entre los 2
    # workers de gunicorn (antes cada uno contaba por separado, con
    # memoria propia) y sirve de cache para las consultas mas pesadas.
    # Si no esta configurado (ej. entorno local sin Redis), cae a
    # almacenamiento en memoria para que la app igual funcione.
    redis_url = os.environ.get('REDIS_URL', '')
    if redis_url:
        app.config['RATELIMIT_STORAGE_URI'] = redis_url
        cache.init_app(app, config={'CACHE_TYPE': 'RedisCache', 'CACHE_REDIS_URL': redis_url, 'CACHE_DEFAULT_TIMEOUT': 300})
    else:
        cache.init_app(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})
    limiter.init_app(app)

    @app.errorhandler(429)
    def limite_excedido(e):
        return jsonify({"error": "Demasiadas peticiones, intenta mas tarde"}), 403

    # CORS: restringido al/los origenes permitidos por ALLOWED_ORIGINS
    # (separados por coma). Si no se define, no se habilita CORS
    # (el dashboard es same-origin, no lo necesita).
    allowed_origins = os.environ.get('ALLOWED_ORIGINS', '')
    if allowed_origins:
        CORS(app, origins=[o.strip() for o in allowed_origins.split(',') if o.strip()])

    # Configuración PostgreSQL desde variables de entorno
    DB_USER = os.environ.get('DB_USER', 'clima')
    DB_PASS = os.environ.get('DB_PASS', 'clima123')
    DB_HOST = os.environ.get('DB_HOST', 'db')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'clima_db')

    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    # Evita que la app se caiga por conexiones muertas a Postgres
    # (proxies/redes que cierran conexiones idle) y limita el tamano
    # maximo de una peticion como defensa basica ante abuso.
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 280,
    }
    app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1 MB

    db.init_app(app)

    with app.app_context():
        from app.routes import api
        app.register_blueprint(api.bp)
        try:
            db.create_all()
        except Exception as e:
            # Si dos procesos arrancan a la vez (deploys con solapamiento,
            # por ejemplo) puede haber una condicion de carrera creando
            # una tabla nueva por primera vez. No es motivo para tumbar
            # la app: la tabla igual queda creada por el otro proceso.
            print(f"[DB] Aviso creando tablas (probable carrera entre workers): {e}")
            db.session.rollback()

    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            # 'unsafe-eval' es necesario porque el cargador de modulos Dojo
            # (usado internamente por la ArcGIS API for JavaScript 3.x) lo
            # requiere para funcionar; sin esto el mapa no carga.
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.arcgis.com; "
            "style-src 'self' 'unsafe-inline' https://js.arcgis.com https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://js.arcgis.com; "
            "img-src 'self' data: https://*.tile.openstreetmap.org https://tilecache.rainviewer.com https://js.arcgis.com; "
            "connect-src 'self' https://api.rainviewer.com https://tilecache.rainviewer.com https://js.arcgis.com https://api.open-meteo.com"
        )
        return response

    return app
