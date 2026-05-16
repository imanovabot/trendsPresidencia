"""Tests para InstagramService (filtrado anti-bot)"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from services.instagram_service import InstagramService


class TestInstagramService:
    """Tests del servicio de Instagram"""

    @pytest.fixture
    def ig_svc(self):
        return InstagramService()

    def test_is_bot_account_few_followers(self, ig_svc):
        "Cuenta con pocos seguidores es bot"
        user = {
            "followers_count": 30,
            "follows_count": 20,
            "media_count": 10,
            "username": "bot_user",
        }
        assert ig_svc._is_bot_account(user) is True

    def test_is_bot_account_spam_keywords(self, ig_svc):
        "Nombre con palabras de bot lo marca como bot"
        user = {
            "followers_count": 100,
            "follows_count": 50,
            "media_count": 100,
            "username": "follow_for_follow_back",
        }
        assert ig_svc._is_bot_account(user) is True

    def test_is_real_account(self, ig_svc):
        "Cuenta real no es bot"
        user = {
            "followers_count": 15000,
            "follows_count": 500,
            "media_count": 300,
            "username": "influencer_real",
        }
        assert ig_svc._is_bot_account(user) is False

    @pytest.mark.asyncio
    async def test_calculate_instagram_score_no_token(self, ig_svc):
        "Sin access token devuelve 0"
        with patch('services.instagram_service.settings.instagram_access_token', None):
            score = await ig_svc.calculate_instagram_score("Abelardo")
            assert score == 0.0
