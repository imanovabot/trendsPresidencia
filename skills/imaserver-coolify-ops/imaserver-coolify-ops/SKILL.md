---
name: imaserver-coolify-ops
description: Hermes-specific ImaServer Coolify operations skill. Uses bundled scripts to manage Redis and verify Coolify power from Hermes.
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
    tags: [imaserver, coolify, redis, deploy, ops]
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
