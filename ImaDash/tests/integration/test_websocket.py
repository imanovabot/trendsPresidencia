#!/usr/bin/env python3
"""Tests de integración: WebSocket real-time"""
import pytest
from fastapi.testclient import TestClient
import asyncio

class TestWebSocket:
    def test_ws_connection(self):
        """Cliente WebSocket debe conectarse"""
        from app import app
        client = TestClient(app)
        with client.websocket_connect("/ws") as websocket:
            data = websocket.receive_text()
            assert "connected" in data.lower()
