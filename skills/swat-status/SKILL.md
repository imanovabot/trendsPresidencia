---
name: swat-status
description: Show SWAT cloud runner progress - queue, ontology, vault, and pacing.
version: 1.0.0
metadata:
  hermes:
    tags: [swat, status, monitor, progress]
    category: devops
---

# SWAT Status

Show the current progress of the SWAT cloud runner running on ImaServer.

## Command

When the user asks for SWAT status, run this command from the ImaServer host:

```bash
cd /data/ima/apps/swat-cloud-runner && docker compose exec swat-cloud-runner python /app/swat_status.py
```

## Expected output

```
SWAT Cloud Runner — HH:MM UTC
   Queue: N total | D done | B blocked | E expanded | P pending
   Children: C (page/slide/sheet level)
   Ontology: N nodes | E edges
   Vault: V Obsidian notes
   Last action: timestamp
   Next: STEP-XXXXXX (page) — filename.pdf
```

## Interpretation

- **Queue total** = all items ever queued (files + children)
- **Done** = units fully processed (extraction + ontology + persist)
- **Blocked** = videos, unreadable files, quota issues
- **Expanded** = parent items waiting for children to complete
- **Pending** = items still queued
- **Children** = page/slide/sheet level units (granular processing)
- **Ontology nodes/edges** = consolidated graph from all fragments
- **Vault notes** = Obsidian markdown files generated under 30_obsidian/

## If the status script is missing

If `/app/swat_status.py` doesn't exist in the container, upload it from the local `scripts/swat_status.py` file.
