"""
Tests para services/imapi_client.py — ImaPi API client (async, read-only).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import httpx

from services.imapi_client import ImaPiClient, ImaPiHealth, AgentStatus, WorkflowStatus, ProjectStatus


@pytest.fixture
def imapi_client():
    return ImaPiClient(base_url="http://localhost:8000")


@pytest.mark.asyncio
async def test_context_manager(imapi_client):
    """__aenter__ crea cliente, __aexit__ lo cierra."""
    async with imapi_client as client:
        assert client.client is not None
        assert isinstance(client.client, httpx.AsyncClient)

    assert client.client.is_closed is True


@pytest.mark.asyncio
async def test_get_health_success(imapi_client):
    """get_health parsea respuesta correctamente."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "status": "ok",
        "agents": 5,
        "workflows": 12,
        "uptime": "2h 30m",
        "version": "1.0.0"
    }
    mock_resp.raise_for_status = MagicMock()

    async with imapi_client as client:
        client.client = AsyncMock()
        client.client.get.return_value = mock_resp

        health = await client.get_health()

    assert health.status == "ok"
    assert health.agents == 5
    assert health.workflows == 12
    assert health.uptime == "2h 30m"
    assert health.version == "1.0.0"


@pytest.mark.asyncio
async def test_list_agents(imapi_client):
    """list_agents retorna lista de AgentStatus."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = [
        {
            "id": "agent-1",
            "name": "WhisperAgent",
            "type": "transcription",
            "status": "running",
            "current_task": "processing audio file",
            "skills": ["whisper", "audio"]
        },
        {
            "id": "agent-2",
            "name": "EmailAgent",
            "type": "email",
            "status": "idle",
            "current_task": None,
            "skills": ["imap", "parse"]
        }
    ]
    mock_resp.raise_for_status = MagicMock()

    async with imapi_client as client:
        client.client = AsyncMock()
        client.client.get.return_value = mock_resp

        agents = await client.list_agents()

    assert len(agents) == 2
    assert agents[0].name == "WhisperAgent"
    assert agents[0].status == "running"
    assert agents[1].status == "idle"


@pytest.mark.asyncio
async def test_list_workflows(imapi_client):
    """list_workflows parsea correctamente."""
    mock_resp = MagicMock()
    now = datetime.now().isoformat()
    mock_resp.json.return_value = [
        {
            "id": "wf-1",
            "name": "Process Email",
            "description": "Parse incoming emails",
            "status": "completed",
            "created_at": now,
            "completed_at": now,
            "tasks": 5,
            "agent": "EmailAgent"
        }
    ]
    mock_resp.raise_for_status = MagicMock()

    async with imapi_client as client:
        client.client = AsyncMock()
        client.client.get.return_value = mock_resp

        workflows = await client.list_workflows(limit=50)

    assert len(workflows) == 1
    wf = workflows[0]
    assert wf.name == "Process Email"
    assert wf.status == "completed"
    assert wf.tasks == 5


@pytest.mark.asyncio
async def test_get_workflow(imapi_client):
    """get_workflow por ID."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "id": "wf-123",
        "name": "Specific Workflow",
        "description": "Test",
        "status": "running",
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "tasks": 3,
        "agent": "TestAgent"
    }
    mock_resp.raise_for_status = MagicMock()

    async with imapi_client as client:
        client.client = AsyncMock()
        client.client.get.return_value = mock_resp

        wf = await client.get_workflow("wf-123")

    assert wf.id == "wf-123"
    assert wf.name == "Specific Workflow"


@pytest.mark.asyncio
async def test_list_projects(imapi_client):
    """list_projects retorna ProjectStatus."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = [
        {
            "id": "proj-1",
            "name": "Project Alpha",
            "description": "First project",
            "status": "active",
            "workflow_ids": ["wf-1", "wf-2"]
        }
    ]
    mock_resp.raise_for_status = MagicMock()

    async with imapi_client as client:
        client.client = AsyncMock()
        client.client.get.return_value = mock_resp

        projects = await client.list_projects()

    assert len(projects) == 1
    proj = projects[0]
    assert proj.name == "Project Alpha"
    assert proj.workflow_ids == ["wf-1", "wf-2"]


@pytest.mark.asyncio
async def test_http_error_propagates(imapi_client):
    """HTTP error se propaga como httpx.HTTPStatusError."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404 Not Found", request=MagicMock(), response=MagicMock()
    )

    async with imapi_client as client:
        client.client = AsyncMock()
        client.client.get.return_value = mock_resp

        with pytest.raises(httpx.HTTPStatusError):
            await client.get_health()


def test_imapi_client_base_url():
    """Base URL se normaliza (sin trailing slash)."""
    client = ImaPiClient(base_url="http://localhost:8000/")
    assert client.base_url == "http://localhost:8000"
