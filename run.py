from app import create_app
from app.models.models import db

app = create_app()

if __name__ == '__main__':
    print("=" * 55)
    print("  SERVIDOR ESTACIÓN CLIMÁTICA SAINLOGIC")
    print("=" * 55)
    
    with app.app_context():
        db.create_all()
        print("[DB] Tablas verificadas/creadas correctamente con SQLAlchemy")
        
    print("\n[OK] Servidor iniciado en http://0.0.0.0:8080")
    print("[OK] Dashboard: http://localhost:8080")
    print("[OK] Esperando datos de la estacion en /data/report/")
    print("[OK] Prueba con: http://localhost:8080/api/test")
    print("\nPresiona Ctrl+C para detener\n")
    app.run(host='0.0.0.0', port=8080, debug=False)
