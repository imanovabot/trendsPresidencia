#!/usr/bin/env python3
"""Tests para orchestrator_integration.py"""
import pytest
from unittest.mock import patch, MagicMock

class TestOrchestratorIntegration:
    @pytest.mark.asyncio
    async def test_list_projects_calls_imapi(self):
        """list_projects debe llamar a ImaPi /projects"""
        from orchestrator_integration import list_projects
        # TODO: mock httpx.get
        pass
    
    def test_start_workflow_payload_format(self):
        """start_workflow debe enviar payload correcto a ImaPi"""
        pass
    
    def test_agent_status_mapping(self):
        """get_agent_status debe mapear estados correctamente"""
        pass
