#!/usr/bin/env python3
"""Legacy compatibility shim. Real ImaServer code lives in ../ImaServer/scripts."""
from __future__ import annotations
import runpy
from pathlib import Path
TARGET = Path(__file__).resolve().parents[2] / 'ImaServer' / 'scripts' / 'coolify_api.py'
globals().update(runpy.run_path(str(TARGET)))
