# Aprendizajes y pendientes

## Pendientes que necesitan a Cristian

### Backups de PostgreSQL (crítico)
Hoy no hay copia fuera del volumen `pgdata`. Falta elegir dónde guardarlas fuera del VPS.
1. Crear el destino (bucket S3 compatible: Cloudflare R2, Backblaze B2) y sus claves.
2. En Coolify, base de datos → Backups: activar el dump diario hacia ese destino, con retención de 30 días.
3. Probar una restauración en local una vez: `pg_restore -d prueba copia.dump`.

### Proxy de Cloudflare
Activo desde el 2026-11-25 en `nuestroclima.co` y `www`, con SSL Full (strict); Always Use HTTPS y Bot Fight Mode apagados. La app toma la IP y el país reales solo de los rangos de Cloudflare (`app/cloudflare.py`). `api.nuestroclima.co` sigue sin proxy y deja ver la IP del VPS.

### Sello por hora en la red SNA
El servicio `sellador` (`scripts/sellador_horas.py`) calcula cada hora keccak256(SELLO_SAL || lecturas de la hora) y la manda al sellador HTTP del nodo SNA, que firma con la billetera de clima (así no chocan los nonces con otro firmante). Queda quieto hasta tener sus variables. En Coolify, app clima → Environment Variables:
- `SELLADOR_URL=https://sellador-clima-sna.proyecto.sbs`.
- `SELLADOR_SECRETO`: el valor de `D:/NITRO 5/secretos-sna/sellador-clima.env`.
- `SELLO_SAL`: texto aleatorio de 32+ caracteres; si se pierde, las horas selladas ya no se pueden verificar.
Luego desplegar y revisar el log de `clima_sellador`: debe decir "N horas selladas". Para ver la huella de una hora: `python -m scripts.sellador_horas huella 2026-11-25T14`.

### Cuota de Weather Underground
La llave gratuita da 1500 consultas al día. El 2026-11-25 se agotó y dejaron de entrar lecturas; el PR #134 baja el consumo. Si vuelve a pasar, el log de `clima_poller` dice "Llave limitada".

### Escaneo de código web viejo
El permiso automático bloqueó `npx modern-web-guidance legacy-scan`. Correrlo a mano o autorizarlo, y abrir un PR por cada hallazgo.

### Runner propio de GitHub Actions
El repo es público: un runner propio dejaría que el PR de un fork ejecute código en el VPS. Se sigue usando el de GitHub hasta que el repo sea privado o se limite a PR de colaboradores.

### Despliegue manual
Coolify no despliega solo al fusionar en `main`; cada cambio fusionado se ve en producción después de un despliegue desde Coolify.
