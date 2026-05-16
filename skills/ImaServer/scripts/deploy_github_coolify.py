#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from coolify_api import CoolifyAPI, load_env_files, required  # noqa: E402


def github_repo_slug(repo: str) -> str:
    """Return owner/repo for GitHub URLs; Coolify private GitHub App endpoints expect this shape."""
    repo = repo.strip().rstrip('/')
    if repo.startswith('git@github.com:'):
        repo = repo.removeprefix('git@github.com:')
    elif 'github.com' in repo:
        parsed = urlparse(repo)
        repo = parsed.path.lstrip('/')
    if repo.endswith('.git'):
        repo = repo[:-4]
    return repo


def normalize_domain(domain: str) -> str:
    domain = domain.strip()
    if not domain:
        return domain
    if '://' not in domain:
        domain = f'https://{domain}'
    parsed = urlparse(domain)
    if not parsed.scheme or not parsed.netloc:
        raise SystemExit(f'Invalid domain/url: {domain}')
    if parsed.scheme not in {'http', 'https'}:
        raise SystemExit(f'Invalid domain scheme: {parsed.scheme}. Use http or https.')
    return domain.rstrip('/')


def redact(obj):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if any(s in k.lower() for s in ('password', 'token', 'secret', 'key')):
                out[k] = '***'
            else:
                out[k] = redact(v)
        return out
    if isinstance(obj, list):
        return [redact(v) for v in obj]
    return obj


def first_present(*names: str) -> str:
    for name in names:
        value = os.getenv(name, '').strip()
        if value:
            return value
    raise SystemExit(f'Missing required env var, tried: {", ".join(names)}')


def optional_first_present(*names: str) -> str:
    for name in names:
        value = os.getenv(name, '').strip()
        if value:
            return value
    return ''


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


def discover_servers(api: CoolifyAPI) -> list[dict]:
    for path in ('/servers',):
        try:
            servers = list_from_response(api.request('GET', path))
            if servers:
                return servers
        except SystemExit:
            continue
    return []


def server_connected_value(server: dict) -> Any:
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


def resolve_server_uuid(api: CoolifyAPI, args: argparse.Namespace, existing: dict | None) -> str:
    explicit = args.server_uuid or optional_first_present('COOLIFY_SERVER_UUID', 'IMASERVER_SERVER_UUID')
    if explicit:
        return explicit
    if existing:
        from_existing = server_uuid_from_app(existing)
        if from_existing:
            return from_existing

    apps = list_from_response(api.request('GET', '/applications'))
    for app in apps:
        if healthyish(app):
            value = server_uuid_from_app(app)
            if value:
                return value

    servers = discover_servers(api)
    if len(servers) == 1 and servers[0].get('uuid'):
        return str(servers[0]['uuid'])
    connected = [srv for srv in servers if server_connected_value(srv) is True and srv.get('uuid')]
    if connected:
        return str(connected[0]['uuid'])
    raise SystemExit('Unable to resolve server_uuid. Set --server-uuid, COOLIFY_SERVER_UUID, or fix Coolify server discovery before deploy.')


def resolve_destination_uuid(api: CoolifyAPI, args: argparse.Namespace, existing: dict | None, server_uuid: str) -> str:
    explicit = args.destination_uuid or optional_first_present('COOLIFY_DESTINATION_UUID', 'IMASERVER_DESTINATION_UUID')
    if explicit:
        return explicit
    if existing:
        value = destination_uuid_from_app(existing)
        if value:
            return value

    apps = list_from_response(api.request('GET', '/applications'))
    for app in apps:
        if healthyish(app) and (not server_uuid or server_uuid_from_app(app) == server_uuid):
            value = destination_uuid_from_app(app)
            if value:
                return value
    return ''


def validate_server(api: CoolifyAPI, server_uuid: str, *, require_connected: bool = False) -> dict:
    server = {}
    try:
        response = api.request('GET', f'/servers/{server_uuid}')
        if isinstance(response, dict):
            server = response
    except SystemExit as exc:
        raise SystemExit(f'Cannot read Coolify server {server_uuid}: {exc}')

    connected = server_connected_value(server)
    if require_connected and connected is not True:
        raise SystemExit(f'Coolify server {server_uuid} is not connected (connected={connected!r}). Aborting before creating orphan app.')
    return server


def app_matches(app: dict, *, name: str | None, repo: str | None, domain: str | None, uuid: str | None) -> bool:
    if uuid and app.get('uuid') == uuid:
        return True
    if name and app.get('name') == name:
        return True
    if repo and app.get('git_repository') and repo.rstrip('/') == str(app.get('git_repository')).rstrip('/'):
        return True
    if domain:
        hay = json.dumps(app.get('fqdn') or app.get('domains') or app.get('docker_compose_domains') or app, ensure_ascii=False)
        if domain in hay:
            return True
    return False


def find_application(api: CoolifyAPI, *, name: str | None, repo: str | None, domain: str | None, uuid: str | None) -> dict | None:
    if uuid:
        try:
            return api.request('GET', f'/applications/{uuid}')
        except SystemExit:
            pass
    apps = api.request('GET', '/applications')
    if not isinstance(apps, list):
        raise SystemExit(f'Unexpected /applications response: {type(apps).__name__}')
    matches = [app for app in apps if app_matches(app, name=name, repo=repo, domain=domain, uuid=uuid)]
    if len(matches) > 1 and not uuid and not name:
        raise SystemExit(f'Multiple applications match repo/domain. Pass --uuid or --name. Matches: {[m.get("uuid") for m in matches]}')
    return matches[0] if matches else None


def resolve_create_endpoint_and_auth(args: argparse.Namespace, api: CoolifyAPI | None = None) -> tuple[str, dict]:
    """Return Coolify creation endpoint plus auth fields for public/private repos.

    Coolify does not accept a raw GitHub PAT on /applications/public. Private repos
    must be created through either a configured GitHub App or a configured Deploy Key.
    ImaServer should use UUIDs already present in Hermes/Coolify env instead of asking
    the user to expose repository credentials in chat.
    """
    mode = (args.private_mode or 'auto').strip().lower()
    github_app_uuid = args.github_app_uuid or optional_first_present(
        'IMASERVER_GITHUB_APP_UUID', 'COOLIFY_GITHUB_APP_UUID', 'GITHUB_APP_UUID'
    )
    private_key_uuid = args.private_key_uuid or optional_first_present(
        'IMASERVER_PRIVATE_KEY_UUID', 'COOLIFY_PRIVATE_KEY_UUID', 'COOLIFY_DEPLOY_KEY_UUID', 'GIT_PRIVATE_KEY_UUID'
    )

    if mode in {'public', 'none'}:
        return '/applications/public', {}
    if mode in {'github-app', 'github_app', 'gh-app', 'gh_app'}:
        if not github_app_uuid:
            raise SystemExit('Private GitHub App deploy requires --github-app-uuid or IMASERVER_GITHUB_APP_UUID/COOLIFY_GITHUB_APP_UUID')
        return '/applications/private-github-app', {'github_app_uuid': github_app_uuid}
    if mode in {'deploy-key', 'deploy_key', 'private-key', 'private_key'}:
        if not private_key_uuid:
            raise SystemExit('Private deploy-key deploy requires --private-key-uuid or IMASERVER_PRIVATE_KEY_UUID/COOLIFY_PRIVATE_KEY_UUID')
        return '/applications/private-deploy-key', {'private_key_uuid': private_key_uuid}
    if mode != 'auto':
        raise SystemExit(f'Invalid --private-mode {args.private_mode!r}. Use auto, public, github-app, or deploy-key.')

    if github_app_uuid:
        return '/applications/private-github-app', {'github_app_uuid': github_app_uuid}
    if private_key_uuid:
        return '/applications/private-deploy-key', {'private_key_uuid': private_key_uuid}

    # Last resort: ask Coolify what credentials are already configured. This is
    # the important bit for ImaBot: do not ask the user to read/private-clone the
    # repo when Coolify already owns the GitHub App or deploy key.
    if api is not None and not args.no_discover_credentials:
        try:
            apps = api.request('GET', '/github-apps')
            if isinstance(apps, list) and apps:
                usable = [a for a in apps if 'public' not in str(a.get('name', '')).lower()] or apps
                preferred = [a for a in usable if a.get('is_system_wide')] or usable
                uuid = preferred[0].get('uuid')
                if uuid:
                    return '/applications/private-github-app', {'github_app_uuid': uuid}
        except SystemExit:
            pass
        try:
            keys = api.request('GET', '/security/keys')
            if isinstance(keys, list) and keys:
                git_keys = [k for k in keys if k.get('is_git_related')] or keys
                uuid = git_keys[0].get('uuid')
                if uuid:
                    return '/applications/private-deploy-key', {'private_key_uuid': uuid}
        except SystemExit:
            pass
    return '/applications/public', {}


def create_public_payload(args: argparse.Namespace, domain: str, api: CoolifyAPI | None = None) -> dict:
    build_pack = args.build_pack
    create_endpoint, auth_fields = resolve_create_endpoint_and_auth(args, api)
    git_repository = github_repo_slug(args.repo) if create_endpoint == '/applications/private-github-app' else args.repo
    payload = {
        'project_uuid': args.project_uuid or required('IMASERVER_PROJECT_UUID'),
        'environment_uuid': args.environment_uuid or os.getenv('IMASERVER_ENVIRONMENT_UUID', ''),
        'environment_name': args.environment_name or os.getenv('IMASERVER_ENVIRONMENT_NAME', 'production'),
        'server_uuid': args.server_uuid,
        'git_repository': git_repository,
        'git_branch': args.branch,
        'build_pack': build_pack,
        'name': args.name,
        'description': args.description or f'Deployed by Hermes /ImaServer from {args.repo}',
        'instant_deploy': bool(args.deploy),
        'force_domain_override': bool(args.force_domain_override),
        'is_force_https_enabled': not args.no_force_https,
        'is_auto_deploy_enabled': not args.no_auto_deploy,
        'autogenerate_domain': False,
    }
    payload.update(auth_fields)
    payload['_imaserver_create_endpoint'] = create_endpoint
    if args.destination_uuid:
        payload['destination_uuid'] = args.destination_uuid
    if build_pack == 'dockercompose':
        payload['docker_compose_location'] = args.compose_location
        payload['docker_compose_domains'] = [{'name': args.service_name, 'domain': domain}]
        # Coolify ignores ports_exposes for dockercompose but validation expects it to be set/rewritten.
        payload['ports_exposes'] = args.port
        if args.compose_start_command:
            payload['docker_compose_custom_start_command'] = args.compose_start_command
        if args.compose_build_command:
            payload['docker_compose_custom_build_command'] = args.compose_build_command
    else:
        payload['domains'] = domain
        payload['ports_exposes'] = args.port
        if args.base_directory:
            payload['base_directory'] = args.base_directory
        if args.dockerfile_location:
            payload['dockerfile_location'] = args.dockerfile_location
        if args.install_command:
            payload['install_command'] = args.install_command
        if args.build_command:
            payload['build_command'] = args.build_command
        if args.start_command:
            payload['start_command'] = args.start_command
        if args.health_path:
            payload['health_check_enabled'] = True
            payload['health_check_path'] = args.health_path
    return {k: v for k, v in payload.items() if v not in (None, '')}


def update_payload_from_create(payload: dict) -> dict:
    # Fields accepted by PATCH /applications/{uuid}; project/server/env/repo are creation-only enough for our use.
    blocked = {'project_uuid', 'environment_uuid', 'environment_name', 'server_uuid', 'destination_uuid', 'autogenerate_domain', '_imaserver_create_endpoint', 'docker_compose_domains', 'github_app_uuid', 'private_key_uuid'}
    return {k: v for k, v in payload.items() if k not in blocked}


def deploy(args: argparse.Namespace) -> None:
    load_env_files()
    domain = normalize_domain(args.domain)
    api = None if (args.dry_run and args.skip_existing_check) else CoolifyAPI()
    existing = None if api is None else find_application(api, name=args.name, repo=args.repo, domain=domain, uuid=args.uuid)
    if api is not None:
        args.server_uuid = resolve_server_uuid(api, args, existing)
        server = validate_server(api, args.server_uuid, require_connected=args.require_connected)
        if not args.destination_uuid:
            args.destination_uuid = resolve_destination_uuid(api, args, existing, args.server_uuid)
        if args.verbose_preflight:
            print(json.dumps({
                'ok': True,
                'preflight': {
                    'server_uuid': args.server_uuid,
                    'server_connected': server_connected_value(server),
                    'destination_uuid': args.destination_uuid or None,
                }
            }, indent=2, ensure_ascii=False), file=sys.stderr)
    elif not args.server_uuid:
        args.server_uuid = optional_first_present('COOLIFY_SERVER_UUID', 'IMASERVER_SERVER_UUID')
    create_payload = create_public_payload(args, domain, api)

    if args.dry_run:
        print(json.dumps({
            'ok': True,
            'dry_run': True,
            'action': 'update' if existing else 'create',
            'existing_uuid': existing.get('uuid') if existing else None,
            'endpoint': f'/applications/{existing.get("uuid")}' if existing else create_payload.get('_imaserver_create_endpoint', '/applications/public'),
            'payload': redact(update_payload_from_create(create_payload) if existing else {k: v for k, v in create_payload.items() if k != '_imaserver_create_endpoint'}),
        }, indent=2, ensure_ascii=False))
        return

    if existing and args.recreate_existing:
        old_uuid = existing['uuid']
        api.request('DELETE', f'/applications/{old_uuid}')
        existing = None

    if existing:
        uuid = existing['uuid']
        updated = api.request('PATCH', f'/applications/{uuid}', update_payload_from_create(create_payload))
        action = 'update'
    else:
        endpoint = create_payload.pop('_imaserver_create_endpoint', '/applications/public')
        updated = api.request('POST', endpoint, create_payload)
        uuid = updated.get('uuid') or updated.get('application_uuid')
        if not uuid:
            # Some Coolify versions return the serialized application.
            uuid = updated.get('data', {}).get('uuid') if isinstance(updated.get('data'), dict) else None
        if not uuid:
            raise SystemExit(f'Application created but UUID was not found in response: {redact(updated)}')
        action = 'recreate' if args.recreate_existing else 'create'

    deploy_result = None
    if args.deploy:
        deploy_result = api.request('POST', f'/applications/{uuid}/start')

    final = api.request('GET', f'/applications/{uuid}')
    print(json.dumps({
        'ok': True,
        'action': action,
        'uuid': uuid,
        'name': final.get('name'),
        'domain': domain,
        'repo': args.repo,
        'build_pack': args.build_pack,
        'deploy_triggered': bool(args.deploy),
        'deploy_result': redact(deploy_result),
        'status': final.get('status'),
        'result': redact(final),
    }, indent=2, ensure_ascii=False))


def status(args: argparse.Namespace) -> None:
    load_env_files()
    api = CoolifyAPI()
    domain = normalize_domain(args.domain) if args.domain else None
    app = find_application(api, name=args.name, repo=args.repo, domain=domain, uuid=args.uuid)
    print(json.dumps({'ok': bool(app), 'application': redact(app)}, indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description='Deploy GitHub repositories to Coolify from Hermes /ImaServer using public, GitHub App, or Deploy Key auth')
    sub = parser.add_subparsers(dest='command', required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--repo', help='Public Git repository URL, e.g. https://github.com/org/app.git')
    common.add_argument('--domain', help='Public domain or URL, e.g. api.example.com or https://api.example.com')
    common.add_argument('--name', help='Coolify application name')
    common.add_argument('--uuid', help='Existing Coolify application UUID')

    dep = sub.add_parser('deploy-github', aliases=['github', 'deploy'], parents=[common])
    dep.add_argument('--branch', default='main')
    dep.add_argument('--private-mode', choices=['auto', 'public', 'github-app', 'deploy-key'], default='auto', help='Repository auth mode. auto uses IMASERVER_GITHUB_APP_UUID/COOLIFY_GITHUB_APP_UUID or IMASERVER_PRIVATE_KEY_UUID/COOLIFY_PRIVATE_KEY_UUID when present.')
    dep.add_argument('--github-app-uuid', default='', help='Coolify GitHub App UUID for private GitHub repositories')
    dep.add_argument('--private-key-uuid', default='', help='Coolify Private/Deploy Key UUID for private repositories')
    dep.add_argument('--no-discover-credentials', action='store_true', help='Do not auto-discover GitHub Apps or deploy keys from Coolify')
    dep.add_argument('--build-pack', choices=['dockercompose', 'dockerfile', 'nixpacks', 'static'], default='dockercompose')
    dep.add_argument('--port', default='8000')
    dep.add_argument('--service-name', default='app', help='Docker Compose service receiving the domain; e.g. api, web, trading-signal')
    dep.add_argument('--compose-location', default='/docker-compose.yml')
    dep.add_argument('--compose-start-command', default='')
    dep.add_argument('--compose-build-command', default='')
    dep.add_argument('--base-directory', default='')
    dep.add_argument('--dockerfile-location', default='')
    dep.add_argument('--install-command', default='')
    dep.add_argument('--build-command', default='')
    dep.add_argument('--start-command', default='')
    dep.add_argument('--health-path', default='')
    dep.add_argument('--description', default='')
    dep.add_argument('--project-uuid', default='')
    dep.add_argument('--environment-uuid', default='')
    dep.add_argument('--environment-name', default='')
    dep.add_argument('--server-uuid', default='')
    dep.add_argument('--destination-uuid', default='')
    dep.add_argument('--require-connected', action='store_true', help='Abort if Coolify reports the selected server as disconnected. Off by default because some Coolify versions keep healthy local apps while connected is null.')
    dep.add_argument('--verbose-preflight', action='store_true', help='Print resolved server/destination preflight details to stderr with secrets redacted.')
    dep.add_argument('--force-domain-override', action='store_true')
    dep.add_argument('--recreate-existing', action='store_true', help='Delete a matching existing app first, then create it through the selected public/private endpoint')
    dep.add_argument('--no-force-https', action='store_true')
    dep.add_argument('--no-auto-deploy', action='store_true')
    dep.add_argument('--no-deploy', dest='deploy', action='store_false')
    dep.add_argument('--dry-run', action='store_true')
    dep.add_argument('--skip-existing-check', action='store_true', help='For dry-run only: do not call Coolify to find existing apps')
    dep.set_defaults(func=deploy, deploy=True)

    st = sub.add_parser('status', parents=[common])
    st.set_defaults(func=status)

    args = parser.parse_args()
    if args.command in {'deploy-github', 'github', 'deploy'}:
        if not args.repo:
            raise SystemExit('--repo is required')
        if not args.domain:
            raise SystemExit('--domain is required')
        if not args.name:
            parsed = urlparse(args.repo)
            repo_name = Path(parsed.path.rstrip('/')).stem or 'imaserver-app'
            args.name = repo_name.replace('_', '-').lower()
    args.func(args)


if __name__ == '__main__':
    main()
