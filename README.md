# 🌦️ Sistema Clima — Finca Lagunitas

Dashboard de monitoreo climático en tiempo real para la estación meteorológica **Sainlogic**, ubicada en la **Vereda Botuba 2, Guavatá, Santander, Colombia**.

---

## 📡 ¿Qué hace?

Recibe datos automáticamente de la estación cada 60 segundos y los muestra en un dashboard web mobile-first con:

- 🌡️ Temperatura exterior e interior
- 💧 Humedad y punto de rocío
- 💨 Velocidad y dirección del viento (brújula animada)
- 🌧️ Lluvia acumulada del día y tasa por hora
- ☀️ Índice UV y radiación solar
- 🔵 Presión atmosférica relativa y absoluta
- 🌕 Fase lunar calculada automáticamente
- 📈 Gráficas históricas de temperatura y lluvia (últimas 24h)
- 🔍 Análisis comparativo semanal y mensual

---

## 🗂️ Estructura

```
Sistema Clima/
├── app.py                  # Servidor Flask + APIs REST
├── models.py               # Base de datos SQLite
├── configurar_estacion.py  # Script de configuración inicial
├── templates/
│   └── index.html          # Dashboard HTML
├── static/
│   ├── css/style.css       # Estilos glassmorphism
│   ├── js/dashboard.js     # Lógica del frontend
│   └── icon-*.svg          # Íconos dinámicos del clima
├── Dockerfile              # Para despliegue en contenedor
└── requirements.txt        # Dependencias Python
```

---

## 🚀 Cómo ejecutar

### Local
```bash
pip install -r requirements.txt
python app.py
```
Dashboard en: `http://localhost:8080`

### Docker
```bash
docker build -t sistema-clima .
docker run -p 8080:8080 sistema-clima
```

---

## 🔌 Endpoints API

| Ruta | Descripción |
|------|-------------|
| `GET /` | Dashboard principal |
| `GET /api/actual` | Última lectura de la estación |
| `GET /api/historial?horas=24` | Historial de lecturas |
| `GET /api/stats` | Estadísticas del día (min/max) |
| `GET /api/stats/comparative` | Análisis semanal/mensual |
| `POST /data/report/` | Endpoint que recibe la estación |
| `GET /api/test` | Insertar datos de prueba |

---

*Desarrollado para Finca Lagunitas — Guavatá, Santander 🇨🇴*
