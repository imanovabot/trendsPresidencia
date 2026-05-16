#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from coolify_api import CoolifyAPI, load_env_files  # noqa: E402


def nested(obj: Any, *path: str) -> Any:
    cur = obj
    for part in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def list_from_response(response: Any) -> list[dict]:
    if isinstance(response, list):
        return [item for item in response if isinstance(item, dict)]
    if isinstance(response, dict):
        for key in ('data', 'servers', 'items'):
            value = response.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def connected_value(server: dict) -> Any:
    for key in ('connected', 'is_connected', 'isReachable', 'reachable'):
        if key in server:
            return server.get(key)
    return nested(server, 'settings', 'connected')


def main() -> None:
    load_env_files()
    api = CoolifyAPI()
    servers = list_from_response(api.request('GET', '/servers'))
    report = {
        'ok': any(connected_value(server) is True for server in servers),
        'servers_total': len(servers),
        'servers_connected': sum(1 for server in servers if connected_value(server) is True),
        'servers': [
            {
                'uuid': server.get('uuid'),
                'name': server.get('name'),
                'ip': server.get('ip'),
                'connected': connected_value(server),
                'agentVersion': server.get('agentVersion') or server.get('agent_version'),
                'is_coolify_host': server.get('is_coolify_host'),
            }
            for server in servers
        ],
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
