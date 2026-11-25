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
El servicio `sellador` (`scripts/sellador_horas.py`) queda quieto hasta tener sus variables. En Coolify, app clima → Environment Variables, agregar:
- `SNA_RPC_URL=https://rpc-sna.proyecto.sbs`, `SNA_RPC_USUARIO=sna`, `SNA_REGISTRO=0x8c87D61e768C9D37E1f186558c16C0e70B8Aa946`.
- Secretos: `SNA_RPC_CLAVE` (clave del RPC), `SNA_LLAVE_SELLADORA` (llave de la billetera 0xbB4c283769053B7c48a0dD2BE79Cba0517017f1E, que necesita saldo y el rol SELLADOR) y `SELLO_SAL` (texto aleatorio de 32+ caracteres; si se pierde, las horas selladas ya no se pueden verificar).
Luego desplegar y revisar el log del contenedor `clima_sellador`: debe decir "N horas selladas".

### Cuota de Weather Underground
La llave gratuita da 1500 consultas al día. El 2026-11-25 se agotó y dejaron de entrar lecturas; el PR #134 baja el consumo. Si vuelve a pasar, el log de `clima_poller` dice "Llave limitada".

### Escaneo de código web viejo
El permiso automático bloqueó `npx modern-web-guidance legacy-scan`. Correrlo a mano o autorizarlo, y abrir un PR por cada hallazgo.

### Runner propio de GitHub Actions
El repo es público: un runner propio dejaría que el PR de un fork ejecute código en el VPS. Se sigue usando el de GitHub hasta que el repo sea privado o se limite a PR de colaboradores.

### Despliegue manual
Coolify no despliega solo al fusionar en `main`; cada cambio fusionado se ve en producción después de un despliegue desde Coolify.
