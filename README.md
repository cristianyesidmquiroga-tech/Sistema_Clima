# Sistema de monitoreo del clima (Flask)

<details>
<summary><b>Read this in English</b></summary>

Web system that collects, stores and publishes weather data for a region of Colombia: personal and public weather stations, national hydrological stations (FEWS/IDEAM) and daily NASA satellite imagery. It serves a public dashboard, a rain map and a weekly regional report, and exports data to PDF and Excel. Everything runs in Docker Compose.


## Features

- **Live dashboard** with current readings, history, statistics and a comparison between stations, charted with Chart.js.
- **Rain map** of nearby stations and per-station history.
- **Regional report** (hydrological stations, rivers and alerts) with a PDF version and a weekly summary of minimum and maximum values per municipality.
- **Satellite archive:** one capture per day and layer (GeoColor and infrared, NASA GOES-East). After three months the captures are packed into one compressed file per month, and the database records are kept.
- **Excel export** of historical data and a weekly report sent by email.
- **News section** with an authenticated admin form.
- **Protection:** rate limits by country, email alerts for blocked IPs, optional passkey validation on the station endpoint, CORS allowlist and a maintenance-mode switch.

## Architecture

Seven containers with explicit memory and CPU limits:

| Service | Role |
|---|---|
| `app` | Flask web app and API served by gunicorn |
| `db` | PostgreSQL |
| `redis` | Cache for expensive endpoints |
| `poller` | Pulls readings from the personal station |
| `historial_poller` | Stores daily history of public stations |
| `lecturas_fews_poller` | Daily readings of the hydrological stations |
| `publicador_velez`, `capturas_mapas_poller`, `reporter` | Regional report, satellite captures and weekly email |

```
app/        Flask app: routes, models, templates, static assets
scripts/    independent processes (pollers, importers, reporter)
docs/       documentation
```

## Run it

```bash
git clone https://github.com/cristianyesidmquiroga-tech/Sistema_Clima.git
cd Sistema_Clima
cp .env.example .env     # Windows: copy .env.example .env
# set DB_PASS, WU_API_KEY, STATION_PASSKEY and SMTP_* in .env
docker compose up -d --build
```

Every variable is documented with a comment in `.env.example`. Set `MODO_MANTENIMIENTO=true` to put the site in maintenance mode without touching code.

## Stack

Python, Flask, SQLAlchemy, PostgreSQL, Redis, gunicorn, WeasyPrint, openpyxl, Chart.js, Docker Compose.

## Author

Cristian Muñoz · [GitHub](https://github.com/cristianyesidmquiroga-tech)

</details>

Sistema web que recoge, guarda y publica datos del clima de una región de Colombia: estaciones meteorológicas propias y públicas, estaciones hidrológicas nacionales (FEWS/IDEAM) e imágenes satelitales diarias de la NASA. Ofrece un panel público, un mapa de lluvias y un reporte semanal de la región, y exporta datos a PDF y Excel. Todo corre con Docker Compose.

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker%20Compose-2496ED?logo=docker&logoColor=white)

## Qué incluye

- **Panel en vivo** con lecturas actuales, historial, estadísticas y comparación entre estaciones, con gráficas en Chart.js.
- **Mapa de lluvias** de estaciones cercanas e historial por estación.
- **Reporte regional** (estaciones hidrológicas, ríos y alertas) con versión en PDF y resumen semanal de mínimos y máximos por municipio.
- **Archivo satelital:** una captura diaria por capa (GeoColor e infrarrojo, NASA GOES-East). Pasados tres meses las capturas se empaquetan en un archivo comprimido por mes y los registros de la base se conservan.
- **Exportación a Excel** de datos históricos y reporte semanal enviado por correo.
- **Sección de noticias** con formulario de administración protegido.
- **Protección:** límites de peticiones por país, alertas por correo de IPs bloqueadas, validación opcional de passkey en el endpoint de la estación, lista de orígenes CORS y modo mantenimiento.

## Arquitectura

Siete contenedores con límites explícitos de memoria y CPU:

| Servicio | Función |
|---|---|
| `app` | App web y API en Flask con gunicorn |
| `db` | PostgreSQL |
| `redis` | Caché de los endpoints costosos |
| `poller` | Trae las lecturas de la estación propia |
| `historial_poller` | Guarda el historial diario de estaciones públicas |
| `lecturas_fews_poller` | Lecturas diarias de las estaciones hidrológicas |
| `publicador_velez`, `capturas_mapas_poller`, `reporter` | Reporte regional, capturas satelitales y correo semanal |

```
app/        app Flask: rutas, modelos, plantillas, estáticos
scripts/    procesos independientes (pollers, importadores, reporter)
docs/       documentación
```

## Cómo ponerlo a correr

```bash
git clone https://github.com/cristianyesidmquiroga-tech/Sistema_Clima.git
cd Sistema_Clima
cp .env.example .env     # en Windows: copy .env.example .env
# definir DB_PASS, WU_API_KEY, STATION_PASSKEY y SMTP_* en .env
docker compose up -d --build
```

Cada variable está documentada con un comentario en `.env.example`. Con `MODO_MANTENIMIENTO=true` el sitio pasa a modo mantenimiento sin tocar código.

## Stack

Python, Flask, SQLAlchemy, PostgreSQL, Redis, gunicorn, WeasyPrint, openpyxl, Chart.js y Docker Compose.

## Autor

Cristian Muñoz · [GitHub](https://github.com/cristianyesidmquiroga-tech)
