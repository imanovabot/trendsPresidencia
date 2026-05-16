---
name: imacycle-orchestrator
description: ImaCycle workflow — SWAT prep, PRD, architecture, code generation via orchestrator
version: 1.0.0
metadata:
  hermes:
    tags: [imacycle, swat, workflow, orchestrator, code, prd, architecture]
    category: devops
---

# ImaCycle Orchestrator for Hermes

Full software creation pipeline: SWAT preparation → ImaCycle (9 stages) → code + docs.

## Architecture

```
Telegram /swat → SWAT Colony (drive → ontology → vault)
Telegram /imacycle → Orchestrator (ontology → PRD → code)

Orchestrator URL: http://lhh3ub0cd5nflq2qujf3xvuf.187.77.14.245.sslip.io
Health: curl $ORCHESTRATOR_URL/health
```

## Workflow stages (ImaCycle)

1. Intention → deepseek-v4-flash:cloud
2. Living Spec (BDD/Gherkin) → deepseek-v4-pro:cloud
3. Architecture (ADRs) → glm-5.1:cloud
4. Contracts (OpenAPI/schemas) → qwen3-coder-next:cloud
5. Generation (TDD) → qwen3-coder-next:cloud
6. Human Handoff (docs) → glm-5.1:cloud
7. Governance (>80% coverage) → deepseek-v4-pro:cloud
8. Evolution (changelogs/semver) → deepseek-v4-flash:cloud
9. Judgment Day (go/no-go) → deepseek-v4-pro:cloud

Model selection: modules/ImaCycle/ima-models.yaml → hybrid profile

## Commands

### Run a project through ImaCycle

```bash
curl -s -X POST $ORCHESTRATOR_URL/execute \
  -H "Content-Type: application/json" \
  -d '{"agent": "ima-orchestrator", "prompt": "Run full ImaCycle on PROJECT_NAME. Repo: REPO_URL. Goal: USER_GOAL"}'
```

### Check project status

```bash
curl -s $ORCHESTRATOR_URL/projects
```

### Run a specific stage

```bash
curl -s -X POST $ORCHESTRATOR_URL/execute \
  -H "Content-Type: application/json" \
  -d '{"agent": "AGENT_NAME", "prompt": "STAGE_PROMPT", "project_name": "PROJECT"}'
```

### List available agents

```bash
curl -s $ORCHESTRATOR_URL/agents
```

## SWAT + ImaCycle combined flow

When user wants a complete solution:

1. First run SWAT on the project folder:
   ```bash
   docker exec imapi-swat-cloud-runner python /app/swat_status.py
   ```
   If SWAT-EXTRACTED/ exists with ontology, proceed to step 2.

2. Run ImaCycle:
   ```
   Agent: ima-orchestrator
   Prompt: "Run full ImaCycle on PROJECT using SWAT ontology at SWAT-EXTRACTED/10_ontology/. Goal: USER_GOAL"
   ```

3. Monitor:
   ```bash
   curl -s $ORCHESTRATOR_URL/projects/PROJECT
   ```
