from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.models.models import db
import os

limiter = Limiter(key_func=get_remote_address, default_limits=["200 per minute"])


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    limiter.init_app(app)

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
        db.create_all()

    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://unpkg.com https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https://*.tile.openstreetmap.org https://*.basemaps.cartocdn.com https://tilecache.rainviewer.com; "
            "connect-src 'self' https://api.rainviewer.com https://tilecache.rainviewer.com"
        )
        return response

    return app
