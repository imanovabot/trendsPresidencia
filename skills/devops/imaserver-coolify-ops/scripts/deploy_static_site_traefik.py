#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

DEFAULT_HOST_SITE_ROOT = Path('/data/ima/sites')
DEFAULT_AGENT_SITE_ROOT = Path('/opt/data/sites')
DEFAULT_ENV_FILES = (
    Path('/opt/data/.env'),
    Path('/workspace/.env'),
)


def load_env_defaults() -> None:
    """Load simple KEY=VALUE entries from known Hermes env files.

    Hermes tool executions do not always inherit variables from /opt/data/.env.
    Loading the file here keeps the deployer deterministic without requiring the
    model to re-discover host/key values or hardcode a broken hostname.
    """
    for env_file in DEFAULT_ENV_FILES:
        if not env_file.exists():
            continue
        for raw_line in env_file.read_text(encoding='utf-8', errors='replace').splitlines():
            line = raw_line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def run(cmd: list[str], cwd: str | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def docker_available() -> bool:
    if not have('docker'):
        return False
    try:
        run(['docker', 'version'], check=True)
        return True
    except Exception:
        return False


def write_compose(site_dir: Path, site_name: str, domain: str, html_dir: Path) -> Path:
    compose = site_dir / 'docker-compose.yml'
    compose.write_text(f'''services:
  {site_name}:
    image: nginx:alpine
    container_name: {site_name}
    restart: unless-stopped
    volumes:
      - {html_dir.as_posix()}:/usr/share/nginx/html:ro
    networks:
      - coolify
    labels:
      - traefik.enable=true
      - traefik.docker.network=coolify
      - traefik.http.routers.{site_name}-http.entrypoints=http
      - traefik.http.routers.{site_name}-http.rule=Host(`{domain}`)
      - traefik.http.routers.{site_name}-http.middlewares=redirect-to-https@file
      - traefik.http.routers.{site_name}-https.entrypoints=https
      - traefik.http.routers.{site_name}-https.rule=Host(`{domain}`)
      - traefik.http.routers.{site_name}-https.tls=true
      - traefik.http.routers.{site_name}-https.tls.certresolver=letsencrypt
      - traefik.http.services.{site_name}.loadbalancer.server.port=80
      - coolify.managed=false
      - imanova.service={site_name}
networks:
  coolify:
    external: true
''', encoding='utf-8')
    return compose


def http_check(url: str) -> dict:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 ImaHermesOps/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read(160).decode('utf-8', errors='replace')
            return {'ok': 200 <= resp.status < 400, 'status': resp.status, 'url': resp.geturl(), 'preview': body[:100]}
    except Exception as exc:
        return {'ok': False, 'error': type(exc).__name__, 'detail': str(exc)[:200]}


def resolves_to_loopback(host: str) -> bool:
    try:
        return any(
            info[4][0].startswith('127.') or info[4][0] == '::1'
            for info in socket.getaddrinfo(host, None)
        )
    except Exception:
        return False


def normalize_ssh_host(args: argparse.Namespace) -> None:
    env_host = os.getenv('IMASERVER_SSH_HOST', '').strip()
    if args.ssh_host and env_host and args.ssh_host != env_host and resolves_to_loopback(args.ssh_host):
        args.ssh_host = env_host


def deploy_local(args: argparse.Namespace) -> dict:
    source = Path(args.source)
    if not source.exists():
        raise SystemExit(f'Source HTML not found: {source}')
    if not docker_available():
        raise SystemExit('Docker is not available in this runtime. Use --ssh-host or run inside the host runtime.')
    site_root = Path(args.site_root)
    site_dir = site_root / args.site_name
    html_dir = site_dir / 'html'
    html_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, html_dir / 'index.html')
    compose = write_compose(site_dir, args.site_name, args.domain, html_dir)
    run(['docker', 'compose', 'up', '-d', '--remove-orphans'], cwd=str(site_dir))
    time.sleep(args.wait)
    ps = run(['docker', 'ps', '--filter', f'name=^{args.site_name}$', '--format', '{{.Names}}\t{{.Status}}\t{{.Networks}}'], check=False).stdout.strip()
    https = http_check(f'https://{args.domain}')
    http = http_check(f'http://{args.domain}')
    return {
        'ok': bool(ps) and (https.get('ok') or http.get('ok')),
        'mode': 'local-docker-traefik',
        'domain': args.domain,
        'site_name': args.site_name,
        'source': str(source),
        'site_dir': str(site_dir),
        'compose': str(compose),
        'container_status': ps,
        'http': http,
        'https': https,
    }


def shell_quote(s: str) -> str:
    return "'" + s.replace("'", "'\"'\"'") + "'"


def deploy_ssh(args: argparse.Namespace) -> dict:
    source = Path(args.source)
    if not source.exists():
        raise SystemExit(f'Source HTML not found: {source}')
    ssh_key = Path(args.ssh_key).expanduser()
    if not ssh_key.exists():
        raise SystemExit(f'SSH key not found: {ssh_key}')
    remote = f'{args.ssh_user}@{args.ssh_host}'
    remote_tmp = f'/tmp/{args.site_name}.index.html'
    scp_cmd = ['scp', '-i', str(ssh_key), '-o', 'StrictHostKeyChecking=accept-new', str(source), f'{remote}:{remote_tmp}']
    run(scp_cmd)
    remote_script = f'''
set -eu
SITE_NAME={shell_quote(args.site_name)}
DOMAIN={shell_quote(args.domain)}
REMOTE_TMP={shell_quote(remote_tmp)}
SITE_ROOT={shell_quote(args.site_root)}
SITE_DIR="$SITE_ROOT/$SITE_NAME"
HTML_DIR="$SITE_DIR/html"
mkdir -p "$HTML_DIR"
cp "$REMOTE_TMP" "$HTML_DIR/index.html"
chmod 755 "$SITE_ROOT" "$SITE_DIR" "$HTML_DIR" 2>/dev/null || true
chmod 644 "$HTML_DIR/index.html"
cat > "$SITE_DIR/docker-compose.yml" <<YAML
services:
  $SITE_NAME:
    image: nginx:alpine
    container_name: $SITE_NAME
    restart: unless-stopped
    volumes:
      - $HTML_DIR:/usr/share/nginx/html:ro
    networks:
      - coolify
    labels:
      - traefik.enable=true
      - traefik.docker.network=coolify
      - traefik.http.routers.$SITE_NAME-http.entrypoints=http
      - traefik.http.routers.$SITE_NAME-http.rule=Host(\\`$DOMAIN\\`)
      - traefik.http.routers.$SITE_NAME-http.middlewares=redirect-to-https@file
      - traefik.http.routers.$SITE_NAME-https.entrypoints=https
      - traefik.http.routers.$SITE_NAME-https.rule=Host(\\`$DOMAIN\\`)
      - traefik.http.routers.$SITE_NAME-https.tls=true
      - traefik.http.routers.$SITE_NAME-https.tls.certresolver=letsencrypt
      - traefik.http.services.$SITE_NAME.loadbalancer.server.port=80
      - coolify.managed=false
      - imanova.service=$SITE_NAME
networks:
  coolify:
    external: true
YAML
cd "$SITE_DIR"
docker compose up -d --remove-orphans >/tmp/$SITE_NAME.deploy.log 2>&1
sleep {int(args.wait)}
docker ps --filter "name=^$SITE_NAME$" --format '{{{{.Names}}}}\t{{{{.Status}}}}\t{{{{.Networks}}}}'
'''
    out = run(['ssh', '-i', str(ssh_key), '-o', 'StrictHostKeyChecking=accept-new', remote, remote_script]).stdout.strip()
    https = http_check(f'https://{args.domain}')
    http = http_check(f'http://{args.domain}')
    return {
        'ok': bool(out) and (https.get('ok') or http.get('ok')),
        'mode': 'ssh-host-docker-traefik',
        'domain': args.domain,
        'site_name': args.site_name,
        'source': str(source),
        'ssh_host': args.ssh_host,
        'site_dir': f'{args.site_root}/{args.site_name}',
        'container_status': out,
        'http': http,
        'https': https,
    }


def main() -> None:
    load_env_defaults()
    parser = argparse.ArgumentParser(description='Deploy static site through nginx + Traefik on ImaServer host')
    parser.add_argument('--domain', required=True)
    parser.add_argument('--site-name', default=None)
    parser.add_argument('--source', default='/opt/data/website/index.html')
    parser.add_argument('--site-root', default=str(DEFAULT_HOST_SITE_ROOT))
    parser.add_argument('--wait', type=int, default=5)
    parser.add_argument('--ssh-host', default=os.getenv('IMASERVER_SSH_HOST', ''))
    parser.add_argument('--ssh-user', default=os.getenv('IMASERVER_SSH_USER', 'root'))
    parser.add_argument('--ssh-key', default=os.getenv('IMASERVER_SSH_KEY', '/opt/data/.ssh/imapi_hermes_root'))
    args = parser.parse_args()
    normalize_ssh_host(args)
    if not args.site_name:
        args.site_name = args.domain.split('.')[0].replace('_', '-').replace('.', '-') + '-website'
    if args.ssh_host:
        result = deploy_ssh(args)
    else:
        result = deploy_local(args)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(0 if result.get('ok') else 2)


if __name__ == '__main__':
    main()
