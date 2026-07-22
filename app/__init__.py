from flask import Flask
from flask_cors import CORS
from app.models.models import db
import os

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    CORS(app)
    
    # Configuración de BD SQLAlchemy
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'clima.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar la base de datos
    db.init_app(app)

    with app.app_context():
        # Importar y registrar rutas
        from app.routes import api
        app.register_blueprint(api.bp)
        
    return app
