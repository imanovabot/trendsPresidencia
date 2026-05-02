import os

"""
Tests para services/calendar_reader.py — CalDAV client (read-only).
"""

from unittest.mock import Mock, patch, MagicMock
import pytest
from datetime import datetime, timedelta

from services.calendar_reader import fetch_upcoming_meetings, fetch_recent_meetings

import pytest
from unittest.mock import MagicMock, patch


# Mock de vobject para eventos
class MockVEvent:
    def __init__(self, uid, summary, dtstart, dtend=None, description=None, location=None):
        self.uid = Mock(value=uid)
        self.summary = Mock(value=summary)
        self.dtstart = Mock(value=dtstart)
        self.dtend = Mock(value=dtend) if dtend else None
        self.description = Mock(value=description) if description else None
        self.location = Mock(value=location) if location else None


class MockEvent:
    def __init__(self, vevent):
        self.vobject_instance = Mock(vevent=vevent)


class MockCalendar:
    def __init__(self, events):
        self._events = events

    def date_search(self, start, end):
        # Retornar eventos dentro del rango
        return [e for e in self._events if start <= e.vobject_instance.vevent.dtstart.value <= end]


class MockPrincipal:
    def __init__(self, calendars):
        self._calendars = calendars

    def calendars(self):
        return self._calendars


class MockDAVClient:
    def __init__(self, url=None, username=None, password=None):
        self.url = url
        self.username = username
        self.password = password

    def principal(self):
        # Retornar un principal con 2 calendars
        cal1 = MockCalendar([])  # se llena abajo
        cal2 = MockCalendar([])
        return MockPrincipal([cal1, cal2])


@pytest.fixture
def mock_caldav(monkeypatch):
    """Mock de la librería caldav."""
    import services.calendar_reader as cal_mod
    monkeypatch.setattr(cal_mod, "CALDAV_AVAILABLE", True)
    return cal_mod




@pytest.fixture
def mock_caldav_client(monkeypatch):
    """Mock del cliente CalDAV."""
    from services import calendar_reader as cal_mod
    
    mock_client = MagicMock()
    mock_principal = MagicMock()
    mock_calendar = MagicMock()
    
    # Crear eventos fake
    event1 = MagicMock()
    event1.instance.vevent.summary.value = "Reunión 1"
    event1.instance.vevent.dtstart.value = "2025-01-01T10:00:00"
    event1.instance.vevent.dtend.value = "2025-01-01T11:00:00"
    event1.instance.vevent.location.value = "Sala 1"
    
    event2 = MagicMock()
    event2.instance.vevent.summary.value = "Reunión 2"
    event2.instance.vevent.dtstart.value = "2025-01-02T14:00:00"
    event2.instance.vevent.dtend.value = "2025-01-02T15:00:00"
    event2.instance.vevent.location.value = "Virtual"
    
    mock_calendar.events.return_value = [event1, event2]
    mock_principal.calendar.return_value = mock_calendar
    mock_client.principal.return_value = mock_principal
    
    monkeypatch.setattr(cal_mod, 'caldav', MagicMock(DAVClient=MagicMock(return_value=mock_client)))
    monkeypatch.setattr(cal_mod, 'CALDAV_AVAILABLE', True)
    return mock_client


def test_fetch_upcoming_meetings_no_config():
    """Si no hay variables de entorno, retorna []."""
    with patch.dict(os.environ, {}, clear=True):
        result = fetch_upcoming_meetings()
        assert result == []


def test_fetch_upcoming_meetings_caldev_not_installed(monkeypatch):
    """Si caldav no instalado, retorna []."""
    import services.calendar_reader as cal_mod
    monkeypatch.setattr(cal_mod, "CALDAV_AVAILABLE", False)
    result = fetch_upcoming_meetings()
    assert result == []


@patch("services.calendar_reader.caldav")
def test_fetch_upcoming_meetings_success(mock_caldav_lib, monkeypatch):
    """fetch_upcoming_meetings parsea eventos correctamente."""
    import services.calendar_reader as cal_mod
    monkeypatch.setattr(cal_mod, "CALDAV_AVAILABLE", True)
    # Configurar env
    monkeypatch.setenv("CALDAV_URL", "https://caldav.example.com")
    monkeypatch.setenv("CALDAV_USER", "user")
    monkeypatch.setenv("CALDAV_PASS", "pass")

    # Crear eventos mock
    now = datetime.now()
    event1 = MockEvent(MockVEvent(
        uid="event-1",
        summary="Reunión 1",
        dtstart=now + timedelta(days=1),
        dtend=now + timedelta(days=1, hours=1),
        description="Descripción 1",
        location="Sala A"
    ))
    event2 = MockEvent(MockVEvent(
        uid="event-2",
        summary="Reunión 2",
        dtstart=now + timedelta(days=3),
        dtend=now + timedelta(days=3, hours=2),
        description=None,
        location=None
    ))

    # Mock client → principal → calendars
    mock_client = Mock()
    mock_principal = Mock()
    mock_calendar = Mock()
    mock_calendar.date_search.return_value = [event1, event2]
    mock_principal.calendars.return_value = [mock_calendar]
    mock_client.principal.return_value = mock_principal
    mock_caldav_lib.DAVClient.return_value = mock_client

    meetings = fetch_upcoming_meetings(days_ahead=7, limit=10)

    assert len(meetings) == 2
    assert meetings[0]["uid"] == "event-1"
    assert meetings[0]["summary"] == "Reunión 1"
    assert meetings[0]["start"] is not None
    assert meetings[0]["end"] is not None
    assert meetings[0]["description"] == "Descripción 1"
    assert meetings[0]["location"] == "Sala A"

    assert meetings[1]["uid"] == "event-2"
    assert meetings[1]["location"] is None


@patch("services.calendar_reader.caldav")
def test_fetch_upcoming_meetings_respects_limit(mock_caldav_lib, monkeypatch):
    """Limita resultados a `limit`."""
    import services.calendar_reader as cal_mod
    monkeypatch.setattr(cal_mod, "CALDAV_AVAILABLE", True)
    monkeypatch.setenv("CALDAV_URL", "https://caldav.example.com")
    monkeypatch.setenv("CALDAV_USER", "user")
    monkeypatch.setenv("CALDAV_PASS", "pass")

    now = datetime.now()
    many_events = [
        MockEvent(MockVEvent(f"event-{i}", f"Meeting {i}", now + timedelta(days=i), now + timedelta(days=i, hours=1)))
        for i in range(50)
    ]

    mock_client = Mock()
    mock_principal = Mock()
    mock_calendar = Mock()
    mock_calendar.date_search.return_value = many_events
    mock_principal.calendars.return_value = [mock_calendar]
    mock_client.principal.return_value = mock_principal
    mock_caldav_lib.DAVClient.return_value = mock_client

    meetings = fetch_upcoming_meetings(limit=10)
    assert len(meetings) == 10


@patch("services.calendar_reader.caldav")
def test_fetch_upcoming_meetings_sorted_asc(mock_caldav_lib, monkeypatch):
    """Resultados ordenados por start ascendente."""
    import services.calendar_reader as cal_mod
    monkeypatch.setattr(cal_mod, "CALDAV_AVAILABLE", True)
    monkeypatch.setenv("CALDAV_URL", "https://caldav.example.com")
    monkeypatch.setenv("CALDAV_USER", "user")
    monkeypatch.setenv("CALDAV_PASS", "pass")

    now = datetime.now()
    events = [
        MockEvent(MockVEvent("z", "Z", now + timedelta(days=5))),
        MockEvent(MockVEvent("a", "A", now + timedelta(days=1))),
        MockEvent(MockVEvent("m", "M", now + timedelta(days=3))),
    ]

    mock_client = Mock()
    mock_principal = Mock()
    mock_calendar = Mock()
    mock_calendar.date_search.return_value = events
    mock_principal.calendars.return_value = [mock_calendar]
    mock_client.principal.return_value = mock_principal
    mock_caldav_lib.DAVClient.return_value = mock_client

    meetings = fetch_upcoming_meetings()
    summaries = [m["summary"] for m in meetings]
    assert summaries == ["A", "M", "Z"]


@patch("services.calendar_reader.caldav")
def test_fetch_recent_meetings_sorted_desc(mock_caldav_lib, monkeypatch):
    """fetch_recent_meetings ordena por start descendente."""
    monkeypatch.setenv("CALDAV_URL", "https://caldav.example.com")
    monkeypatch.setenv("CALDAV_USER", "user")
    monkeypatch.setenv("CALDAV_PASS", "pass")

    now = datetime.now()
    events = [
        MockEvent(MockVEvent("a", "A", now - timedelta(days=5))),
        MockEvent(MockVEvent("z", "Z", now - timedelta(days=1))),
        MockEvent(MockVEvent("m", "M", now - timedelta(days=3))),
    ]

    mock_client = Mock()
    mock_principal = Mock()
    mock_calendar = Mock()
    mock_calendar.date_search.return_value = events
    mock_principal.calendars.return_value = [mock_calendar]
    mock_client.principal.return_value = mock_principal
    mock_caldav_lib.DAVClient.return_value = mock_client

    meetings = fetch_recent_meetings(days_back=7)
    summaries = [m["summary"] for m in meetings]
    assert summaries == ["Z", "M", "A"]


@patch("services.calendar_reader.caldav")
def test_fetch_meetings_caldav_exception(mock_caldav_lib, monkeypatch):
    """Excepción en CalDAV se traga y retorna []."""
    monkeypatch.setenv("CALDAV_URL", "https://caldav.example.com")
    monkeypatch.setenv("CALDAV_USER", "user")
    monkeypatch.setenv("CALDAV_PASS", "pass")

    mock_client = Mock()
    mock_client.principal.side_effect = Exception("Connection failed")
    mock_caldav_lib.DAVClient.return_value = mock_client

    meetings = fetch_upcoming_meetings()
    assert meetings == []
