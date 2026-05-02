#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


def required(name: str) -> str:
    value = os.getenv(name, '').strip()
    if not value:
        raise SystemExit(f'Missing required env var: {name}')
    return value


class CoolifyAPI:
    def __init__(self) -> None:
        self.base_url = required('COOLIFY_BASE_URL').rstrip('/')
        self.token = os.getenv('COOLIFY_WRITE_TOKEN') or os.getenv('COOLIFY_DEPLOY_TOKEN') or required('COOLIFY_API_TOKEN')
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            # Coolify is behind Cloudflare in ImaServer. A plain urllib user
            # agent can be rejected with 403/1010 even when the token is valid.
            'User-Agent': 'Mozilla/5.0 ImaHermesOps/1.0',
        }

    def request(self, method: str, path: str, payload: dict | None = None) -> dict:
        body = None if payload is None else json.dumps(payload).encode('utf-8')
        url = f'{self.base_url}/api/v1{path}'
        req = urllib.request.Request(url, data=body, headers=self.headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                text = resp.read().decode('utf-8')
                return json.loads(text) if text else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode('utf-8', errors='replace')
            raise SystemExit(f'Coolify API error {exc.code} {method} {path}: {detail}')
