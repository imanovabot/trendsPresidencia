---
name: imaserver-coolify-ops
description: Hermes-specific ImaServer operations skill. Deploys GitHub repositories to Coolify domains, manages Redis, deploys static sites through the ImaServer host/Traefik, and verifies Coolify power from Hermes.
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
    tags: [imaserver, coolify, github, docker-compose, dockerfile, redis, static-site, traefik, deploy, ops]
    category: devops
---

> **Important:** this is the low-level Coolify adapter bundle. The user-facing Hermes/ImaBot command is `/ImaServer`, backed by the `ImaServer` bridge skill and the ImaPi `modules/ImaServer` module. Do not tell users that `imaserver-coolify-ops` is the primary skill identity.


# ImaServer Coolify Ops for Hermes

Compatibility-only skill. Real implementation lives in `ImaServer/scripts`; this package must not own deploy logic.

Adapter command: `/imaserver-coolify-ops` (internal/legacy). User-facing command: `/ImaServer`.





## Private repositories / credentials

ImaServer MUST NOT ask the user to manually read or clone private repositories. Use the credentials already available in Hermes/Coolify:

- Prefer a configured Coolify GitHub App: `IMASERVER_GITHUB_APP_UUID`, `COOLIFY_GITHUB_APP_UUID`, or auto-discovery via `GET /github-apps`.
- Fallback to a configured Deploy Key: `IMASERVER_PRIVATE_KEY_UUID`, `COOLIFY_PRIVATE_KEY_UUID`, `COOLIFY_DEPLOY_KEY_UUID`, or auto-discovery via `GET /security/keys`.
- Create private GitHub apps through Coolify endpoint `/applications/private-github-app`.
- Create private deploy-key apps through Coolify endpoint `/applications/private-deploy-key`.
- Use `/applications/public` only when no private credential exists or the user explicitly chooses public mode.

For private repos, call the deployer with `--private-mode auto` by default. Do not request GitHub PATs in chat. Do not expose tokens in logs. The deployer redacts token/key fields.

## GitHub application deployment — PRIMARY USE CASE

When the user says things like “tenés esto en GitHub, desplegalo en este dominio”, DO NOT answer that the skill only supports static sites. That is wrong. Use the GitHub deployer.

For a Docker Compose app:

```bash
python3 /opt/data/skills/devops/ImaServer/scripts/deploy_github_coolify.py deploy-github \
  --repo https://github.com/ORG/REPO.git \
  --domain api.example.com \
  --name my-api \
  --build-pack dockercompose \
  --compose-location /docker-compose.yml \
  --service-name api \
  --port 8000
```

If `/opt/data` is not mounted in the execution sandbox, use the workspace mirror:

```bash
python3 /workspace/skills/devops/ImaServer/scripts/deploy_github_coolify.py deploy-github \
  --repo https://github.com/ORG/REPO.git \
  --domain api.example.com \
  --name my-api \
  --build-pack dockercompose \
  --compose-location /docker-compose.yml \
  --service-name api \
  --port 8000
```

For Dockerfile/Nixpacks apps, use `--build-pack dockerfile` or `--build-pack nixpacks`; the domain is attached directly with `--domain` and `--port`.

Useful options:

- `--dry-run` shows the Coolify payload without creating/updating anything.
- `--uuid` updates an existing Coolify application by UUID.
- `--force-domain-override` is required only if Coolify reports a domain conflict and the user confirms replacing it.
- `--no-deploy` creates/updates the app without triggering deployment.

For Docker Compose, `--service-name` must match the compose service that should receive the public domain, for example `api`, `web`, or `trading-signal`. If unsure, inspect the repo compose file first.

Expected output is JSON with:

- `ok: true`
- `action: create` or `update`
- `uuid`
- `domain`
- `deploy_triggered`
- `status`

To install Redis, run:

```bash
python3 /opt/data/skills/devops/ImaServer/scripts/deploy_redis_coolify.py install-redis --name imapi-redis
```

If `/opt/data` is not mounted in the execution sandbox, use the workspace mirror:

```bash
python3 /workspace/skills/devops/ImaServer/scripts/deploy_redis_coolify.py install-redis --name imapi-redis
```

To check access/powers, run:

```bash
python /opt/data/skills/devops/ima-platform-ops/scripts/verify_imaserver_ops_setup.py
```

## Static site deployment

When the user asks to deploy a prepared static website/domain, do not give manual instructions and do not try to create an unsupported Coolify service first.

Run the bundled static-site deployer:

```bash
python3 /opt/data/skills/devops/ImaServer/scripts/deploy_static_site_traefik.py \
  --domain erp.imanova.cloud \
  --site-name erp-website \
  --source /opt/data/website/index.html
```

The deployer reads `/opt/data/.env` automatically for:

- `IMASERVER_SSH_HOST=187.77.14.245`
- `IMASERVER_SSH_USER=root`
- `IMASERVER_SSH_KEY=/opt/data/.ssh/imapi_hermes_root`

Do **not** pass `srv1359926.hstgr.cloud` as `--ssh-host` from inside Hermes containers:
inside the runtime it resolves to `127.0.1.1`, which points back to the container
instead of the ImaServer host.

Expected output is JSON with:

- `ok: true`
- `mode: ssh-host-docker-traefik`
- `domain`
- `container_status`
- `http`
- `https`

If `/opt/data` is not mounted, use the workspace mirror for the script but keep the source path that actually contains the prepared HTML.
