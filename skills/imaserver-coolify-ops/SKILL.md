---
name: imaserver-coolify-ops
description: Hermes-specific ImaServer operations skill. Uses bundled scripts to manage Redis, deploy static sites through the ImaServer host/Traefik, and verify Coolify power from Hermes.
version: 1.0.0
required_environment_variables:
  - COOLIFY_BASE_URL
  - COOLIFY_API_TOKEN
  - COOLIFY_WRITE_TOKEN
  - COOLIFY_DEPLOY_TOKEN
  - HERMES_SERVICE_UUID
  - IMASERVER_PROJECT_UUID
  - IMASERVER_ENVIRONMENT_UUID
  - COOLIFY_SERVER_UUID
metadata:
  hermes:
    tags: [imaserver, coolify, redis, static-site, traefik, deploy, ops]
    category: devops
---

# ImaServer Coolify Ops for Hermes

To install Redis, run:

```bash
python /opt/data/skills/devops/imaserver-coolify-ops/scripts/deploy_redis_coolify.py install-redis --name imapi-redis
```

If `/opt/data` is not mounted in the execution sandbox, use the workspace mirror:

```bash
python /workspace/skills/devops/imaserver-coolify-ops/scripts/deploy_redis_coolify.py install-redis --name imapi-redis
```

To check access/powers, run:

```bash
python /opt/data/skills/devops/ima-platform-ops/scripts/verify_imaserver_ops_setup.py
```

## Static site deployment

When the user asks to deploy a prepared static website/domain, do not give manual instructions and do not try to create an unsupported Coolify service first.

Run the bundled static-site deployer:

```bash
python /opt/data/skills/devops/imaserver-coolify-ops/scripts/deploy_static_site_traefik.py \
  --domain erp.imanova.cloud \
  --site-name erp-website \
  --source /opt/data/website/index.html \
  --ssh-host srv1359926.hstgr.cloud \
  --ssh-user root \
  --ssh-key /opt/data/.ssh/imapi_hermes_root
```

Expected output is JSON with:

- `ok: true`
- `mode: ssh-host-docker-traefik`
- `domain`
- `container_status`
- `http`
- `https`

If `/opt/data` is not mounted, use the workspace mirror for the script but keep the source path that actually contains the prepared HTML.
