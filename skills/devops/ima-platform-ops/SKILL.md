---
name: ima-platform-ops
description: Hermes-specific platform operations skill for ImaServer/Coolify diagnostics. Verifies Coolify API powers, required env vars, Redis/Postgres visibility, and writes file evidence.
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
    tags: [ima, platform, ops, coolify, redis, postgres, diagnostic]
    category: devops
---

# Ima Platform Ops for Hermes

For any request about server powers, diagnostics, Coolify, Redis, PostgreSQL, or environment verification, run:

```bash
python /opt/data/skills/devops/ima-platform-ops/scripts/verify_imaserver_ops_setup.py
```

If `/opt/data` is not mounted in the execution sandbox, use:

```bash
python /workspace/skills/devops/ima-platform-ops/scripts/verify_imaserver_ops_setup.py
```

The script writes evidence to:

```text
/tmp/ima_platform_diagnostic_report.json
```

Do not block only because `/opt/data` is missing. If required env vars are present, use env-based operations.
