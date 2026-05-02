"""
Tests para services/github_reader.py — GitHub REST API client (read-only).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import httpx

from services.github_reader import GitHubReader, GitHubProject, GitHubIssue


@pytest.fixture
def github_reader():
    return GitHubReader(token="test-token", owner="test-owner", repo="test-repo")


@pytest.mark.asyncio
async def test_github_project_model():
    """GitHubProject model validation."""
    project = GitHubProject(
        id=1,
        name="Test Project",
        number=1,
        body="Description",
        state="open",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        url="https://github.com/orgs/test-owner/projects/1"
    )
    assert project.name == "Test Project"
    assert project.state == "open"


@pytest.mark.asyncio
async def test_github_issue_model():
    """GitHubIssue model validation."""
    issue = GitHubIssue(
        id=101,
        number=42,
        title="Bug fix",
        body="Fix something",
        state="open",
        user="alice",
        assignees=["alice", "bob"],
        labels=["bug", "high-priority"],
        milestone="v1.0",
        project_ids=[1, 2],
        created_at=datetime.now(),
        updated_at=datetime.now(),
        url="https://github.com/test-owner/test-repo/issues/42"
    )
    assert issue.title == "Bug fix"
    assert "bug" in issue.labels
    assert issue.project_ids == [1, 2]


@pytest.mark.asyncio
async def test_list_projects_success(github_reader):
    """list_projects parsea projects de GitHub correctamente."""
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "id": 1,
            "name": "Project Alpha",
            "number": 1,
            "body": "First project",
            "state": "open",
            "created_at": "2026-01-01T10:00:00Z",
            "updated_at": "2026-01-02T10:00:00Z",
            "html_url": "https://github.com/orgs/test-owner/projects/1"
        },
        {
            "id": 2,
            "name": "Project Beta",
            "number": 2,
            "body": None,
            "state": "closed",
            "created_at": "2026-01-03T10:00:00Z",
            "updated_at": "2026-01-04T10:00:00Z",
            "html_url": "https://github.com/orgs/test-owner/projects/2"
        }
    ]
    mock_response.raise_for_status = MagicMock()

    async with github_reader as reader:
        reader.client = AsyncMock()
        reader.client.get.return_value = mock_response

        projects = await reader.list_projects()

    assert len(projects) == 2
    assert projects[0].name == "Project Alpha"
    assert projects[0].state == "open"
    assert projects[1].name == "Project Beta"
    assert projects[1].body is None

    # Verificar llamada a API
    reader.client.get.assert_called_once_with(
        "https://api.github.com/orgs/test-owner/projects",
        params={"per_page": 20, "state": "open"}
    )


@pytest.mark.asyncio
async def test_list_issues_basic(github_reader):
    """list_issues retorna issues con filtros básicos."""
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "id": 1001,
            "number": 10,
            "title": "Issue 10",
            "body": "Body 10",
            "state": "open",
            "user": {"login": "alice"},
            "assignees": [{"login": "alice"}, {"login": "bob"}],
            "labels": [{"name": "bug"}, {"name": "frontend"}],
            "milestone": {"title": "v1.0"},
            "project_ids": [1, 2],
            "created_at": "2026-01-01T10:00:00Z",
            "updated_at": "2026-01-02T10:00:00Z",
            "closed_at": None,
            "html_url": "https://github.com/test-owner/test-repo/issues/10"
        }
    ]
    mock_response.raise_for_status = MagicMock()

    async with github_reader as reader:
        reader.client = AsyncMock()
        reader.client.get.return_value = mock_response

        issues = await reader.list_issues(state="open", limit=50)

    assert len(issues) == 1
    issue = issues[0]
    assert issue.number == 10
    assert issue.title == "Issue 10"
    assert issue.user == "alice"
    assert issue.assignees == ["alice", "bob"]
    assert issue.labels == ["bug", "frontend"]
    assert issue.milestone == "v1.0"
    assert issue.project_ids == [1, 2]


@pytest.mark.asyncio
async def test_list_issues_with_filters(github_reader):
    """list_issues incluye parámetros de filtrado en request."""
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status = MagicMock()

    async with github_reader as reader:
        reader.client = AsyncMock()
        reader.client.get.return_value = mock_response

        since = datetime(2026, 1, 1)
        await reader.list_issues(
            state="closed",
            labels="bug,critical",
            milestone="v2.0",
            assignee="bob",
            since=since
        )

    # Verificar que se pasaron los params correctos
    call_args = reader.client.get.call_args
    params = call_args[1]["params"]
    assert params["state"] == "closed"
    assert params["labels"] == "bug,critical"
    assert params["milestone"] == "v2.0"
    assert params["assignee"] == "bob"
    assert "since" in params


@pytest.mark.asyncio
async def test_list_issues_http_error(github_reader):
    """HTTP error se propaga como HTTPException."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404 Not Found", request=MagicMock(), response=MagicMock()
    )

    async with github_reader as reader:
        reader.client = AsyncMock()
        reader.client.get.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            await reader.list_issues()


@pytest.mark.asyncio
async def test_context_manager(github_reader):
    """__aenter__/__aexit__ gestiona cliente correctamente."""
    async with github_reader as reader:
        assert reader.client is not None
        assert isinstance(reader.client, httpx.AsyncClient)

    # after exit, client debe estar cerrado
    assert reader.client.is_closed


def test_github_reader_init_params():
    """Inicialización con parámetros."""
    reader = GitHubReader(
        token="mytoken",
        owner="myorg",
        repo="myrepo"
    )
    assert reader.token == "mytoken"
    assert reader.owner == "myorg"
    assert reader.repo == "myrepo"
    assert reader.base_url == "https://api.github.com"
    assert "Authorization" in reader.headers
    assert reader.headers["User-Agent"] == "ImaDash-Monitor"
