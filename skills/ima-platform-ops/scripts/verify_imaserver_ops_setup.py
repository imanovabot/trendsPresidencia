#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Prefer Hermes venv because it contains asyncpg in the production image.
VENV_PY = Path('/opt/hermes/.venv/bin/python3')
if not os.getenv('_IMA_VERIFY_VENV') and VENV_PY.exists() and Path(sys.executable) != VENV_PY:
    env = dict(os.environ)
    env['_IMA_VERIFY_VENV'] = '1'
    os.execve(str(VENV_PY), [str(VENV_PY), __file__], env)

REQUIRED = [
    'COOLIFY_BASE_URL', 'COOLIFY_API_TOKEN', 'COOLIFY_WRITE_TOKEN',
    'COOLIFY_DEPLOY_TOKEN', 'HERMES_SERVICE_UUID', 'IMASERVER_PROJECT_UUID',
    'IMASERVER_ENVIRONMENT_UUID', 'COOLIFY_SERVER_UUID',
]
SERVICE_ENV = [
    'IMA_REDIS_HOST', 'IMA_REDIS_PORT', 'IMA_REDIS_PASSWORD',
    'REDIS_HOST', 'REDIS_PORT', 'REDIS_PASSWORD',
    'IMA_POSTGRES_HOST', 'IMA_POSTGRES_PORT', 'IMA_POSTGRES_USER',
    'IMA_POSTGRES_PASSWORD', 'IMA_POSTGRES_DB',
    'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_DB',
]
FILES = [
    '/opt/data/.env', '/opt/data/.hermes/.env',
    '/opt/data/skills/devops/ima-platform-ops/scripts/verify_imaserver_ops_setup.py',
    '/opt/data/skills/devops/imaserver-coolify-ops/scripts/deploy_redis_coolify.py',
    '/opt/data/skills/devops/imaserver-coolify-ops/scripts/coolify_api.py',
    '/workspace/skills/devops/ima-platform-ops/scripts/verify_imaserver_ops_setup.py',
    '/workspace/skills/devops/imaserver-coolify-ops/scripts/deploy_redis_coolify.py',
]


def load_env_files() -> None:
    for env_path in ('/opt/data/.env', '/opt/data/.hermes/.env'):
        p = Path(env_path)
        if not p.exists():
            continue
        for line in p.read_text(encoding='utf-8', errors='replace').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def tcp(host: str | None, port: str | int | None) -> dict:
    if not host or not port:
        return {'configured': False, 'ok': False, 'error': 'missing host/port'}
    try:
        with socket.create_connection((str(host), int(port)), timeout=5):
            return {'configured': True, 'ok': True, 'host': host, 'port': int(port)}
    except Exception as exc:
        return {'configured': True, 'ok': False, 'host': host, 'port': int(port), 'error': type(exc).__name__}


def redis_check() -> dict:
    host = os.getenv('IMA_REDIS_HOST') or os.getenv('REDIS_HOST')
    port = os.getenv('IMA_REDIS_PORT') or os.getenv('REDIS_PORT') or '6379'
    password = os.getenv('IMA_REDIS_PASSWORD') or os.getenv('REDIS_PASSWORD')
    base = tcp(host, port)
    if not base.get('ok') or not password:
        base['auth_checked'] = False
        base['auth_required_password_present'] = bool(password)
        return base

    def resp_cmd(*parts: str) -> bytes:
        out = f'*{len(parts)}\r\n'.encode()
        for part in parts:
            data = part.encode()
            out += b'$' + str(len(data)).encode() + b'\r\n' + data + b'\r\n'
        return out

    try:
        with socket.create_connection((str(host), int(port)), timeout=5) as s:
            s.sendall(resp_cmd('AUTH', password))
            auth = s.recv(256)
            s.sendall(resp_cmd('PING'))
            pong = s.recv(256)
        base.update({'auth_checked': True, 'auth_ok': auth.startswith(b'+OK'), 'ping_ok': pong.startswith(b'+PONG'), 'ok': auth.startswith(b'+OK') and pong.startswith(b'+PONG')})
    except Exception as exc:
        base.update({'auth_checked': True, 'ok': False, 'error': type(exc).__name__})
    return base


async def _postgres_asyncpg() -> dict:
    import asyncpg
    conn = await asyncpg.connect(
        host=os.getenv('IMA_POSTGRES_HOST') or os.getenv('POSTGRES_HOST'),
        port=int(os.getenv('IMA_POSTGRES_PORT') or os.getenv('POSTGRES_PORT') or '5432'),
        user=os.getenv('IMA_POSTGRES_USER') or os.getenv('POSTGRES_USER'),
        password=os.getenv('IMA_POSTGRES_PASSWORD') or os.getenv('POSTGRES_PASSWORD'),
        database=os.getenv('IMA_POSTGRES_DB') or os.getenv('POSTGRES_DB'),
        timeout=5,
        ssl=False,
    )
    val = await conn.fetchval('select 1')
    await conn.close()
    return {'ok': val == 1, 'auth_checked': True, 'select_1': val == 1}


def postgres_check() -> dict:
    host = os.getenv('IMA_POSTGRES_HOST') or os.getenv('POSTGRES_HOST')
    port = os.getenv('IMA_POSTGRES_PORT') or os.getenv('POSTGRES_PORT') or '5432'
    base = tcp(host, port)
    if not base.get('ok'):
        return base
    try:
        import asyncio
        auth = asyncio.run(_postgres_asyncpg())
        base.update(auth)
    except ModuleNotFoundError:
        base.update({'auth_checked': False, 'warning': 'asyncpg not installed; TCP check only'})
    except Exception as exc:
        base.update({'auth_checked': True, 'ok': False, 'error': type(exc).__name__})
    return base


def coolify_service_status(uuid: str | None) -> dict:
    if not uuid or not os.getenv('COOLIFY_BASE_URL') or not os.getenv('COOLIFY_API_TOKEN'):
        return {'ok': False, 'error': 'missing Coolify env'}
    token = os.getenv('COOLIFY_WRITE_TOKEN') or os.getenv('COOLIFY_API_TOKEN')
    url = os.getenv('COOLIFY_BASE_URL').rstrip('/') + f'/api/v1/services/{uuid}'
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 ImaHermesOps/1.0',
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        return {'ok': True, 'uuid': data.get('uuid'), 'name': data.get('name'), 'status': data.get('status')}
    except urllib.error.HTTPError as exc:
        return {'ok': False, 'error': f'HTTP {exc.code}'}
    except Exception as exc:
        return {'ok': False, 'error': type(exc).__name__}


def main() -> None:
    load_env_files()
    env_presence = {k: bool(os.getenv(k)) for k in REQUIRED + SERVICE_ENV}
    file_presence = {p: Path(p).exists() for p in FILES}
    redis = redis_check()
    postgres = postgres_check()
    coolify = {'hermes_service': coolify_service_status(os.getenv('HERMES_SERVICE_UUID'))}
    missing_required_env = [k for k in REQUIRED if not os.getenv(k)]
    missing_service_env = [k for k in ['IMA_REDIS_HOST', 'IMA_REDIS_PASSWORD', 'IMA_POSTGRES_HOST', 'IMA_POSTGRES_USER', 'IMA_POSTGRES_PASSWORD', 'IMA_POSTGRES_DB'] if not os.getenv(k)]
    core_files_ok = all(file_presence[p] for p in FILES if p.startswith('/opt/data/skills/devops'))
    ok = not missing_required_env and not missing_service_env and core_files_ok and coolify['hermes_service'].get('ok') and redis.get('ok') and postgres.get('ok')
    report = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'overall_status': 'OK' if ok else 'FAILED',
        'summary': {
            'scripts_ok': core_files_ok,
            'coolify_env_ok': not missing_required_env,
            'service_env_ok': not missing_service_env,
            'coolify_api_ok': bool(coolify['hermes_service'].get('ok')),
            'redis_ok': bool(redis.get('ok')),
            'postgres_ok': bool(postgres.get('ok')),
            'docker_required': False,
        },
        'execution_model': {
            'backend_expected': 'local',
            'docker_required': False,
            'note': 'Docker daemon access is not required. Hermes ops must use configured service hostnames, not localhost.',
        },
        'missing_required_env': missing_required_env,
        'missing_service_env': missing_service_env,
        'env_presence': env_presence,
        'file_presence': file_presence,
        'tcp': {'redis': redis, 'postgres': postgres},
        'coolify': coolify,
        'details': {
            'docker_daemon': {'ok': None, 'required': False, 'status': 'skipped_not_required'},
            'redis': redis,
            'postgres': postgres,
            'coolify': coolify,
        },
    }
    report_path = Path('/tmp/ima_platform_diagnostic_report.json')
    try:
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    except PermissionError:
        # Old diagnostics may have been created by root from manual SSH checks.
        # Do not fail the verifier because evidence-file ownership is stale.
        report_path = Path(f"/tmp/ima_platform_diagnostic_report_{os.getuid()}.json")
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f'DIAGNOSTIC_REPORT={report_path}')


if __name__ == '__main__':
    main()
