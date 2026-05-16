#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_ENV_FILES = (Path('/opt/data/.env'), Path('/opt/data/.hermes/.env'), Path('/workspace/.env'))


def load_env_files(*, override: bool = False) -> None:
    """Load ImaServer/Coolify environment files when scripts run outside Hermes.

    The Telegram/Hermes runtime often has the variables already loaded, but local
    script execution commonly does not. Loading here keeps all canonical scripts
    consistent and avoids each script re-implementing partial env handling.
    """
    for env_file in DEFAULT_ENV_FILES:
        if not env_file.exists():
            continue
        for raw in env_file.read_text(encoding='utf-8', errors='replace').splitlines():
            line = raw.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if override or key not in os.environ:
                os.environ[key] = value


def required(name: str) -> str:
    value = os.getenv(name, '').strip()
    if not value:
        raise SystemExit(f'Missing required env var: {name}')
    return value


class CoolifyAPI:
    def __init__(self, base_url: str | None = None, token: str | None = None, *, load_env: bool = True) -> None:
        if load_env:
            load_env_files()
        self.base_url = (base_url or required('COOLIFY_BASE_URL')).rstrip('/')
        self.default_token = token or os.getenv('COOLIFY_WRITE_TOKEN') or os.getenv('COOLIFY_DEPLOY_TOKEN') or required('COOLIFY_API_TOKEN')

    def token_for(self, method: str, path: str) -> str:
        method = method.upper()
        deploy_paths = ('/start', '/restart', '/stop', '/deploy', '/cancel')
        if method in {'POST', 'GET'} and any(path.endswith(suffix) or suffix + '?' in path for suffix in deploy_paths):
            return os.getenv('COOLIFY_DEPLOY_TOKEN') or os.getenv('COOLIFY_WRITE_TOKEN') or required('COOLIFY_API_TOKEN')
        if method in {'POST', 'PATCH', 'PUT', 'DELETE'}:
            return os.getenv('COOLIFY_WRITE_TOKEN') or os.getenv('COOLIFY_API_TOKEN') or os.getenv('COOLIFY_DEPLOY_TOKEN') or self.default_token
        return os.getenv('COOLIFY_API_TOKEN') or os.getenv('COOLIFY_WRITE_TOKEN') or os.getenv('COOLIFY_DEPLOY_TOKEN') or self.default_token

    def headers_for(self, method: str, path: str) -> dict[str, str]:
        return {
            'Authorization': f'Bearer {self.token_for(method, path)}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            # Coolify is behind Cloudflare in ImaServer. A plain urllib user
            # agent can be rejected with 403/1010 even when the token is valid.
            'User-Agent': 'Mozilla/5.0 ImaHermesOps/1.0',
        }

    def request(self, method: str, path: str, payload: dict | None = None) -> Any:
        body = None if payload is None else json.dumps(payload).encode('utf-8')
        url = path if path.startswith('http://') or path.startswith('https://') else f'{self.base_url}/api/v1{path}'
        req = urllib.request.Request(url, data=body, headers=self.headers_for(method, path), method=method)
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                text = resp.read().decode('utf-8')
                return json.loads(text) if text else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode('utf-8', errors='replace')
            raise SystemExit(f'Coolify API error {exc.code} {method} {path}: {detail}')
