#!/bin/bash
echo "========================================="
echo "  Inicializando base de datos..."
echo "========================================="
# Aunque ahora se usa SQLAlchemy y db.create_all() en run.py, 
# se puede mantener create_admin.py para tareas pre-arranque.
python scripts/create_admin.py

echo "========================================="
echo "  Iniciando servidor Flask..."
echo "========================================="
exec python run.py
