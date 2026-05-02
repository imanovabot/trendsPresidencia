"""
Tests para services/email_reader.py — EmailReader (Himalaya CLI wrapper).
"""

import json
from unittest.mock import Mock, patch, call
import pytest
from fastapi import HTTPException

from services.email_reader import EmailReader, EmailEnvelope


@pytest.fixture
def email_reader():
    return EmailReader()


def test_email_envelope_model():
    """EmailEnvelope model es válido."""
    env = EmailEnvelope(
        uid="123",
        message_id="<msg123>",
        subject="Test",
        from_="sender@example.com",
        date="2026-01-01T12:00:00",
        folder="INBOX",
        flags=["\\Seen"],
        preview="Preview text..."
    )
    assert env.uid == "123"
    assert env.from_ == "sender@example.com"
    assert env.preview == "Preview text..."


@patch("services.email_reader.subprocess.run")
def test_fetch_envelopes_success(mock_run, email_reader):
    """fetch_envelopes parsea output JSON correctamente."""
    # Simular output de `himalaya envelope list --output json`
    mock_output = json.dumps([
        {
            "uid": 1,
            "message_id": "<msg1>",
            "subject": "Subject 1",
            "from": "sender1@example.com",
            "date": "2026-01-01T10:00:00",
            "folder": "INBOX",
            "flags": ["\\Seen"],
            "body": "Body of email 1"
        },
        {
            "uid": 2,
            "message_id": "<msg2>",
            "subject": "Subject 2",
            "from": "sender2@example.com",
            "date": "2026-01-01T11:00:00",
            "folder": "INBOX",
            "flags": [],
            "body": "Body of email 2 with more text..."
        }
    ])
    mock_run.return_value = Mock(stdout=mock_output, returncode=0)

    envelopes = email_reader.fetch_envelopes(folder="INBOX", limit=10, page=1)

    assert len(envelopes) == 2
    assert envelopes[0].uid == "1"
    assert envelopes[0].subject == "Subject 1"
    assert envelopes[0].from_ == "sender1@example.com"
    assert envelopes[0].flags == ["\\Seen"]
    assert envelopes[0].preview == "Body of email 1"

    # Verificar que se llamó a himalaya con los argumentos correctos
    expected_cmd = [
        "himalaya", "envelope", "list",
        "--folder", "INBOX",
        "--page", "1",
        "--page-size", "10",
        "--output", "json"
    ]
    mock_run.assert_called_once_with(
        expected_cmd,
        capture_output=True,
        text=True,
        timeout=30
    )


@patch("services.email_reader.subprocess.run")
def test_fetch_envelopes_himalaya_not_found(mock_run, email_reader):
    """Himalaya no instalado levanta excepción clara."""
    mock_run.side_effect = FileNotFoundError("himalaya not found")

    with pytest.raises(Exception) as exc:
        email_reader.fetch_envelopes()
    assert "Himalaya CLI not found" in str(exc.value)


@patch("services.email_reader.subprocess.run")
def test_fetch_envelopes_timeout(mock_run, email_reader):
    """Timeout en subprocess levanta excepción."""
    import subprocess
    mock_run.side_effect = subprocess.TimeoutExpired(cmd="himalaya", timeout=30)

    with pytest.raises(Exception) as exc:
        email_reader.fetch_envelopes()
    assert "timed out" in str(exc.value).lower()


@patch("services.email_reader.subprocess.run")
def test_fetch_envelopes_non_zero_exit(mock_run, email_reader):
    """Himalaya retorna error no-zero."""
    mock_run.return_value = Mock(stdout="", stderr="IMAP auth failed", returncode=1)

    with pytest.raises(Exception) as exc:
        email_reader.fetch_envelopes()
    assert "Himalaya error" in str(exc.value)


@patch("services.email_reader.subprocess.run")
def test_fetch_envelopes_invalid_json(mock_run, email_reader):
    """Output no-JSON levanta JSONDecodeError."""
    mock_run.return_value = Mock(stdout="invalid json{", returncode=0)

    with pytest.raises(json.JSONDecodeError):
        email_reader.fetch_envelopes()


@patch("services.email_reader.subprocess.run")
def test_read_message(mock_run, email_reader):
    """read_message obtiene el mensaje completo."""
    mock_output = json.dumps({
        "uid": 42,
        "message_id": "<msg42>",
        "subject": "Re: Test",
        "from": "alice@example.com",
        "to": ["bob@example.com"],
        "cc": [],
        "bcc": [],
        "date": "2026-01-01T12:00:00",
        "folder": "INBOX",
        "flags": ["\\Seen", "\\Flagged"],
        "body": "Full message body",
        "headers": {"Reply-To": "alice@example.com"}
    })
    mock_run.return_value = Mock(stdout=mock_output, returncode=0)

    msg = email_reader.read_message(uid="42", folder="INBOX")

    assert msg["uid"] == 42
    assert msg["subject"] == "Re: Test"
    assert msg["body"] == "Full message body"

    expected_cmd = [
        "himalaya", "message", "read",
        "--folder", "INBOX",
        "42",
        "--output", "json"
    ]
    mock_run.assert_called_once_with(
        expected_cmd,
        capture_output=True,
        text=True,
        timeout=30
    )
