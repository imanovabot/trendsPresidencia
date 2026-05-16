#!/usr/bin/env python3
"""Legacy compatibility shim. Use /opt/data/skills/devops/ImaServer/scripts/deploy_redis_coolify.py."""
from __future__ import annotations
import runpy
from pathlib import Path
TARGET = Path(__file__).resolve().parents[2] / 'ImaServer' / 'scripts' / 'deploy_redis_coolify.py'
runpy.run_path(str(TARGET), run_name='__main__')
