#!/usr/bin/env python3
"""
Despliega la app Trading Signal en Coolify usando la API.
Uso: python deploy_trading_to_coolify.py
"""
import json
import os
import sys
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'skills', 'imaserver-coolify-ops', 'scripts'))
from coolify_api import CoolifyAPI, required  # noqa: E402


def getenv_or_prompt(name: str, default: str = None) -> str:
    val = os.getenv(name, '').strip()
    if not val and default:
        return default
    if not val:
        raise SystemExit(f'Missing required env var: {name}')
    return val


def main() -> None:
    print("🚀 Desplegando Trading Signal en Coolify\n")

    # Configuración
    COOLIFY = CoolifyAPI()
    PROJECT_UUID = required('IMASERVER_PROJECT_UUID')
    SERVER_UUID = required('COOLIFY_SERVER_UUID')
    ENVIRONMENT_UUID = required('IMASERVER_ENVIRONMENT_UUID')

    # Domain que me digas (aquí deberías modificar)
    DOMAIN = os.getenv('TRADING_DOMAIN', 'trading-signal.imanova.cloud')

    # Repo GitHub
    GIT_REPO = 'https://github.com/imanovabot/NoticiasIA.git'
    GIT_BRANCH = 'main'
    GIT_DIR = 'trading_signal_skill'

    print(f"📦 Proyecto: {GIT_REPO} (rama: {GIT_BRANCH}, dir: {GIT_DIR})")
    print(f"🌐 Domain: {DOMAIN}")
    print(f"🖥️  Server UUID: {SERVER_UUID}")
    print(f"📂 Project UUID: {PROJECT_UUID}")
    print()

    # ── 1. Crear/obtener aplicación en Coolify ───────────────────────────────────
    PROJECT_UUID = required('IMASERVER_PROJECT_UUID')
    print(f"📂 Project UUID: {PROJECT_UUID}")

    # Buscar si ya existe
    print("🔍 Buscando aplicación existente...")
    apps_response = COOLIFY.request('GET', f'/projects/{PROJECT_UUID}/applications')
    apps_list = apps_response if isinstance(apps_response, list) else apps_response.get('data', [])

    app_uuid = None
    for app in apps_list:
        if 'trading-signal' in app.get('name', '').lower():
            app_uuid = app['uuid']
            print(f"✅ Encontrada: {app['name']} (UUID: {app_uuid})")
            break

    if not app_uuid:
        print("ℹ️  No existe, creando nueva aplicación...")
        create_payload = {
            'name': 'trading-signal',
            'description': 'Trading Signal Skill v1.1.0 - Backend FastAPI + PostgreSQL + Schedulers',
            'project_uuid': PROJECT_UUID,
            'environment_uuid': ENVIRONMENT_UUID,
            'server_uuid': SERVER_UUID,
            'is_public': True,
            'instant_deploy': False,
        }
        result = COOLIFY.request('POST', f'/projects/{PROJECT_UUID}/applications', create_payload)
        app_uuid = result['uuid']
        print(f"✅ Creada: {result.get('name','trading-signal')} (UUID: {app_uuid})")

    # ── 2. Configurar Git repository ────────────────────────────────────────────
    print("\n⚙️  Configurando repositorio Git...")
    git_config = {
        'repository': GIT_REPO,
        'branch': GIT_BRANCH,
        'subdirectory': GIT_DIR,
    }
    COOLIFY.request('PUT', f'/applications/{app_uuid}/git', git_config)
    print("✅ Git configurado")

    # ── 3. Configurar Docker Compose override ───────────────────────────────────
    print("\n📦 Configurando Docker Compose...")
    compose_config = {
        'dockerCompose': compose_content,
    }
    COOLIFY.request('PUT', f'/applications/{app_uuid}/docker-compose', compose_config)
    print("✅ Docker Compose configurado")

    # ── 4. Configurar dominio y SSL ─────────────────────────────────────────────
    print("\n🌐 Configurando dominio...")
    domain_config = {
        'domains': [DOMAIN],
        'enable_ssl': True,
        'force_ssl': True,
    }
    COOLIFY.request('PUT', f'/applications/{app_uuid}/domains', domain_config)
    print(f"✅ Dominio {DOMAIN} configurado con SSL")

    # ── 5. Trigger deploy ───────────────────────────────────────────────────────
    print("\n🚀 Iniciando deploy...")
    deploy_result = COOLIFY.request('POST', f'/applications/{app_uuid}/deploy', {
        'type': 'docker-compose',
        'force': True
    })
    print(f"✅ Deploy iniciado (ID: {deploy_result.get('uuid', 'N/A')})")

    # ── 6. Mostrar información final ────────────────────────────────────────────
    print("\n" + "="*60)
    print("✅ ¡Despliegue completado!")
    print("="*60)
    print(f"\n📡 API URL: https://{DOMAIN}")
    print(f"🔍 Health check: https://{DOMAIN}/health")
    print(f"📊 Recomendación: https://{DOMAIN}/recomendacion")
    print(f"\n📁 Proyecto en GitHub: {GIT_REPO}/tree/{GIT_BRANCH}/{GIT_DIR}")
    print("\n⏳ Espera 1-2 minutos para que el deploy termine...")
    print("   Luego prueba:")
    print(f"   curl https://{DOMAIN}/health")
    print(f"   curl https://{DOMAIN}/recomendacion")
    print()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
