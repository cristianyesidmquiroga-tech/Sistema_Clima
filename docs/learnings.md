# Aprendizajes y pendientes

## Pendientes que necesitan a Cristian

### Backups de PostgreSQL (crítico)
Hoy no hay copia fuera del volumen `pgdata`. Falta elegir dónde guardarlas fuera del VPS.
1. Crear el destino (bucket S3 compatible: Cloudflare R2, Backblaze B2) y sus claves.
2. En Coolify, base de datos → Backups: activar el dump diario hacia ese destino, con retención de 30 días.
3. Probar una restauración en local una vez: `pg_restore -d prueba copia.dump`.

### Proxy de Cloudflare (nube naranja)
Antes de activarlo, la app debe leer la IP real; si no, todos los visitantes comparten el límite de peticiones y salen como extranjeros.
1. Hecho en el PR #128 (`app/cloudflare.py`): la app ya toma `CF-Connecting-IP` y `CF-IPCountry` solo si la petición llega desde los rangos de Cloudflare. Desplegarlo en Coolify antes del paso 3.
2. En Cloudflare: SSL/TLS en Full (strict); dejar apagados Always Use HTTPS (Coolify ya redirige) y Bot Fight Mode (bloquea la estación).
3. Activar el proxy en los registros A de nuestroclima.co.
4. Opcional: cerrar los puertos 80 y 443 del VPS para que solo entre tráfico de Cloudflare. Esto afecta a Coolify y a las otras apps del servidor.

### Escaneo de código web viejo
El permiso automático bloqueó `npx modern-web-guidance legacy-scan`. Correrlo a mano o autorizarlo, y abrir un PR por cada hallazgo.

### Runner propio de GitHub Actions
El repo es público: un runner propio dejaría que el PR de un fork ejecute código en el VPS. Se sigue usando el de GitHub hasta que el repo sea privado o se limite a PR de colaboradores.

### Despliegue manual
Coolify no despliega solo al fusionar en `main`; cada cambio fusionado se ve en producción después de un despliegue desde Coolify.
