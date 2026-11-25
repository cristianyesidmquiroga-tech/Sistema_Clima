from dotenv import load_dotenv

# Solo en desarrollo local; en Docker las variables ya vienen del entorno
load_dotenv()

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 55)
    print("  SERVIDOR ESTACIÓN CLIMÁTICA SAINLOGIC")
    print("=" * 55)
    print("[DB] Tablas verificadas/creadas correctamente con SQLAlchemy")
    print("\n[OK] Servidor iniciado en http://127.0.0.1:8080")
    print("[OK] Dashboard: http://localhost:8080")
    print("[OK] Esperando datos de la estacion en /data/report/")
    print("\nPresiona Ctrl+C para detener\n")
    app.run(host='127.0.0.1', port=8080, debug=False)
