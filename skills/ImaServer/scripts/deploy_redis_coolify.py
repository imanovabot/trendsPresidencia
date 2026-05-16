#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from coolify_api import CoolifyAPI, required  # noqa: E402


def install_redis(args: argparse.Namespace) -> None:
    payload = {
        'server_uuid': required('COOLIFY_SERVER_UUID'),
        'project_uuid': required('IMASERVER_PROJECT_UUID'),
        'environment_uuid': required('IMASERVER_ENVIRONMENT_UUID'),
        'environment_name': os.getenv('IMASERVER_ENVIRONMENT_NAME', 'production'),
        'name': args.name,
        'description': 'Redis provisioned by Hermes ImaServer Coolify Ops',
        'image': args.image,
        'redis_password': args.password or secrets.token_urlsafe(32),
        'is_public': False,
        'instant_deploy': True,
    }
    # IMPORTANT: omit redis_conf when empty; Coolify rejects empty redis_conf with 422.
    if args.redis_conf:
        payload['redis_conf'] = args.redis_conf
    result = CoolifyAPI().request('POST', '/databases/redis', payload)
    safe = dict(result)
    for key in list(safe.keys()):
        if any(s in key.lower() for s in ('password', 'token', 'key', 'secret', 'url')):
            safe[key] = '***'
    print(json.dumps({'ok': True, 'action': 'install-redis', 'result': safe}, indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description='ImaServer Coolify Redis deployer')
    sub = parser.add_subparsers(dest='command', required=True)
    redis = sub.add_parser('install-redis', aliases=['redis'])
    redis.add_argument('--name', default='imapi-redis')
    redis.add_argument('--image', default='redis:7-alpine')
    redis.add_argument('--password', default=None)
    redis.add_argument('--redis-conf', default='')
    redis.set_defaults(func=install_redis)
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
