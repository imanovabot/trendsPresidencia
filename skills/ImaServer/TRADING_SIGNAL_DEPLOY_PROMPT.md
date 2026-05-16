# ImaBot Prompt — Deploy `trading-signal` with ImaServer

Paste this into ImaBot.

```txt
/imaserver

Actuá como ImaServer DevOps executor. No actúes como shell genérico ni como auditor preguntón.

Objetivo:
Dejar funcionando:

- Repo: https://github.com/imanovabot/NoticiasIA.git
- Dominio: trading-signal.imanova.cloud
- App name: trading-signal
- Cron diario 8 AM: trading-signal-daily-8am

Contexto importante:
ImaServer estaba fallando porque creaba apps huérfanas o sin server/destination correcto. Ya hay scripts canónicos preparados/corregidos que debés usar desde:

/opt/data/skills/ImaServer/scripts/

Scripts requeridos:
- coolify_api.py
- check_coolify_agent.py
- resolve_deploy_server.py
- deploy_github_coolify.py

Si alguno falta en runtime, copiá/sincronizá desde la versión canónica de ImaServer antes de desplegar. No uses `.archive` como fuente principal.

Reglas:
- No uses `.archive`.
- No uses `--git-token`.
- No uses `--private-mode public`.
- No pidas GitHub PAT.
- No instales agentes/paquetes no verificados.
- No crees scripts hardcodeados por app.
- No imprimas secretos.
- No borres volúmenes ni bases de datos.
- No uses `docker system prune`.
- No toques apps sanas no relacionadas.

GitHub App disponible:
- UUID: mr8uy0pmqlawtiwzes2fk19r

Referencia de app sana:
- imadash

Fallo adicional confirmado del cron 8 AM:

El job `trading-signal-daily-8am` falló ejecutando:

`/opt/data/skills/trading-signal-skill/scripts/telegram_notifier.py`

Error raíz:

`AssertionError: Class <class 'sqlalchemy.sql.elements.SQLCoreOperations'> directly inherits TypingOnly but has additional attributes {'__firstlineno__', '__static_attributes__'}`

Esto ocurre al importar SQLAlchemy desde:

`/opt/data/skills/trading-signal-skill/venv/lib/python3.13/site-packages/sqlalchemy/...`

Diagnóstico:
- Es incompatibilidad entre Python 3.13 y la versión instalada de SQLAlchemy.
- No es error de Telegram.
- No es error de Coolify.
- No es error de `/run_hourly`.
- El script ni siquiera llega a ejecutar lógica de negocio.

Acción obligatoria para el cron:

Antes de declarar resuelto el despliegue, corregí el venv local de `trading-signal-skill`:

```bash
/opt/data/skills/trading-signal-skill/venv/bin/python - <<'PY'
import sys
print(sys.version)
PY

/opt/data/skills/trading-signal-skill/venv/bin/python -m pip show SQLAlchemy || true

/opt/data/skills/trading-signal-skill/venv/bin/python -m pip install --upgrade "SQLAlchemy>=2.0.34,<3"

/opt/data/skills/trading-signal-skill/venv/bin/python - <<'PY'
import sqlalchemy
print(sqlalchemy.__version__)
PY
```

Después probá el import exacto que fallaba:

```bash
cd /opt/data/skills/trading-signal-skill
./venv/bin/python - <<'PY'
from app.config import settings
from app import models
print("IMPORT_OK")
PY
```

Luego probá el notifier:

```bash
cd /opt/data/skills/trading-signal-skill
./venv/bin/python scripts/telegram_notifier.py
```

Si falla por credenciales/env/DB, reportá el nuevo error exacto. No vuelvas a culpar SQLAlchemy si el import ya pasa.

Flujo obligatorio:

1. Verificar que los scripts canónicos existan:

```bash
ls -la /opt/data/skills/ImaServer/scripts/coolify_api.py \
       /opt/data/skills/ImaServer/scripts/check_coolify_agent.py \
       /opt/data/skills/ImaServer/scripts/resolve_deploy_server.py \
       /opt/data/skills/ImaServer/scripts/deploy_github_coolify.py
```

2. Verificar sintaxis de scripts, sin build:

```bash
python -m py_compile \
  /opt/data/skills/ImaServer/scripts/coolify_api.py \
  /opt/data/skills/ImaServer/scripts/check_coolify_agent.py \
  /opt/data/skills/ImaServer/scripts/resolve_deploy_server.py \
  /opt/data/skills/ImaServer/scripts/deploy_github_coolify.py
```

3. Diagnóstico Coolify:

```bash
python /opt/data/skills/ImaServer/scripts/check_coolify_agent.py
```

No uses `connected=None` como única razón para abortar si existe una app sana como `imadash` corriendo en el mismo destination/server. Usalo como señal, no como bloqueo absoluto.

4. Resolver server/destination usando `imadash`:

```bash
python /opt/data/skills/ImaServer/scripts/resolve_deploy_server.py --reference-app imadash
```

Guardá:
- server_uuid
- destination_uuid si aparece
- server_connected

5. Hacer dry-run del deploy:

```bash
python /opt/data/skills/ImaServer/scripts/deploy_github_coolify.py deploy-github \
  --repo https://github.com/imanovabot/NoticiasIA.git \
  --domain trading-signal.imanova.cloud \
  --name trading-signal \
  --build-pack dockercompose \
  --compose-location /docker-compose.yml \
  --service-name app \
  --port 8000 \
  --private-mode github-app \
  --github-app-uuid mr8uy0pmqlawtiwzes2fk19r \
  --recreate-existing \
  --verbose-preflight \
  --dry-run
```

Si el dry-run muestra `server_uuid` vacío o `destination_uuid` vacío y la API exige destination, NO crees la app. Resolvé primero destination desde `imadash` o desde Coolify API.

6. Ejecutar deploy real:

```bash
python /opt/data/skills/ImaServer/scripts/deploy_github_coolify.py deploy-github \
  --repo https://github.com/imanovabot/NoticiasIA.git \
  --domain trading-signal.imanova.cloud \
  --name trading-signal \
  --build-pack dockercompose \
  --compose-location /docker-compose.yml \
  --service-name app \
  --port 8000 \
  --private-mode github-app \
  --github-app-uuid mr8uy0pmqlawtiwzes2fk19r \
  --recreate-existing \
  --verbose-preflight
```

7. Verificación Soldier:

Después del deploy, verificá:

- app UUID final
- server/destination asignado
- image creada
- container_name creado
- status running/healthy
- fqdn/domain asignado
- logs de build/deploy si falla
- health externo:

```bash
python - <<'PY'
import urllib.request
url = 'https://trading-signal.imanova.cloud/health'
try:
    with urllib.request.urlopen(url, timeout=20) as r:
        print(r.status, r.read(300).decode('utf-8', errors='replace'))
except Exception as e:
    print(type(e).__name__, e)
    raise
PY
```

8. Cron/notificador:

No configures cron con:
- localhost:8001
- curl si el entorno no tiene curl

Si `/run_hourly` existe y la app está healthy, el endpoint correcto debe ser:

https://trading-signal.imanova.cloud/run_hourly

Usá Python stdlib/urllib si el runner no tiene curl.

Además, verificá el cron diario:

- Job: `trading-signal-daily-8am`
- Debe ejecutar con el venv corregido.
- Debe pasar el import de SQLAlchemy.
- Debe producir reporte o un error nuevo real de negocio/configuración.

Definición de éxito:

- https://trading-signal.imanova.cloud/health responde OK.
- trading-signal tiene contenedor real.
- `trading-signal-daily-8am` ya no falla por SQLAlchemy/Python 3.13.
- No queda app huérfana sin server/destination.
- No se usó `.archive`, `--git-token`, ni public mode para repo privado.

Reporte final:

A. Scripts canónicos usados
B. server_uuid y destination_uuid resueltos
C. App UUID final
D. Container final
E. Estado Coolify final
F. Resultado health externo
G. Cron/notificador: versión SQLAlchemy final, prueba import, ejecución notifier, corregido o pendiente con causa exacta
H. Si falló: causa exacta y siguiente acción genérica de ImaServer

Ejecutá.
```
