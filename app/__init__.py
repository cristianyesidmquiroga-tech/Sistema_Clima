from flask import Flask
from flask_cors import CORS
from app.models.models import db
import os

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    CORS(app)
    
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

    db.init_app(app)

    with app.app_context():
        from app.routes import api
        app.register_blueprint(api.bp)
        
    return app
