#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from coolify_api import CoolifyAPI, load_env_files  # noqa: E402


def redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            key: ('***' if any(s in key.lower() for s in ('token', 'secret', 'password', 'key')) else redact(value))
            for key, value in obj.items()
        }
    if isinstance(obj, list):
        return [redact(item) for item in obj]
    return obj


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
        for key in ('data', 'servers', 'applications', 'resources', 'items'):
            value = response.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def server_connected(server: dict) -> Any:
    for key in ('connected', 'is_connected', 'isReachable', 'reachable'):
        if key in server:
            return server.get(key)
    return nested(server, 'settings', 'connected')


def server_uuid_from_app(app: dict) -> str:
    for value in (
        app.get('server_uuid'),
        app.get('server_id'),
        nested(app, 'server', 'uuid'),
        nested(app, 'destination', 'server', 'uuid'),
        nested(app, 'destination', 'server_uuid'),
    ):
        if value:
            return str(value)
    return ''


def destination_uuid_from_app(app: dict) -> str:
    for value in (
        app.get('destination_uuid'),
        nested(app, 'destination', 'uuid'),
        nested(app, 'destination', 'id'),
    ):
        if value:
            return str(value)
    return ''


def healthyish(app: dict) -> bool:
    status = str(app.get('status') or app.get('health_status') or '').lower()
    return 'running' in status or 'healthy' in status


def main() -> None:
    parser = argparse.ArgumentParser(description='Resolve a usable Coolify server/destination pair for ImaServer deploys.')
    parser.add_argument('--reference-app', default='', help='Prefer destination/server metadata from this healthy app name or UUID.')
    parser.add_argument('--require-connected', action='store_true', help='Fail if no server reports connected=true.')
    args = parser.parse_args()

    load_env_files()
    api = CoolifyAPI()
    servers = list_from_response(api.request('GET', '/servers'))
    apps = list_from_response(api.request('GET', '/applications'))

    reference = None
    if args.reference_app:
        for app in apps:
            if app.get('uuid') == args.reference_app or app.get('name') == args.reference_app:
                reference = app
                break
    if reference is None:
        reference = next((app for app in apps if healthyish(app) and destination_uuid_from_app(app)), None)

    selected_server_uuid = server_uuid_from_app(reference or {}) if reference else ''
    selected_destination_uuid = destination_uuid_from_app(reference or {}) if reference else ''

    if not selected_server_uuid:
        connected = [server for server in servers if server_connected(server) is True and server.get('uuid')]
        if connected:
            selected_server_uuid = str(connected[0]['uuid'])
        elif len(servers) == 1 and servers[0].get('uuid'):
            selected_server_uuid = str(servers[0]['uuid'])

    selected_server = next((server for server in servers if server.get('uuid') == selected_server_uuid), {})
    if args.require_connected and server_connected(selected_server) is not True:
        raise SystemExit(f'No connected server found. Selected={selected_server_uuid or None}, connected={server_connected(selected_server)!r}')

    print(json.dumps(redact({
        'ok': bool(selected_server_uuid),
        'server_uuid': selected_server_uuid or None,
        'destination_uuid': selected_destination_uuid or None,
        'server_connected': server_connected(selected_server),
        'reference_app': {
            'uuid': reference.get('uuid') if reference else None,
            'name': reference.get('name') if reference else None,
            'status': reference.get('status') if reference else None,
            'fqdn': reference.get('fqdn') if reference else None,
        },
        'servers_seen': [
            {
                'uuid': server.get('uuid'),
                'name': server.get('name'),
                'ip': server.get('ip'),
                'connected': server_connected(server),
            }
            for server in servers
        ],
    }), indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
