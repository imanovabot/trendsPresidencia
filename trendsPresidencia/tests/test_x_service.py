"""Tests para XService (filtrado anti-bot)"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from services.x_service import XService


class TestXService:
    """Tests del servicio de X/Twitter"""

    @pytest.fixture
    def x_svc(self):
        return XService()

    def test_is_bot_account_not_verified_low_followers(self, x_svc):
        "Cuenta no verificada con pocos seguidores es bot"
        user = {
            "verified": False,
            "public_metrics": {
                "followers_count": 50,
                "following_count": 10,
                "tweet_count": 100,
            }
        }
        assert x_svc._is_bot_account(user) is True

    def test_is_bot_account_following_spam(self, x_svc):
        "Ratio following/followers muy alto indica spam"
        user = {
            "verified": False,
            "public_metrics": {
                "followers_count": 100,
                "following_count": 1000,
                "tweet_count": 500,
            }
        }
        assert x_svc._is_bot_account(user) is True

    def test_is_bot_account_verified_ok(self, x_svc):
        "Cuenta verificada no es bot"
        user = {
            "verified": True,
            "public_metrics": {
                "followers_count": 10000,
                "following_count": 500,
                "tweet_count": 5000,
            }
        }
        assert x_svc._is_bot_account(user) is False

    @pytest.mark.asyncio
    async def test_calculate_x_score_no_token(self, x_svc):
        "Sin bearer token devuelve 0"
        with patch('services.x_service.settings.x_bearer_token', None):
            score = await x_svc.calculate_x_score("Abelardo")
            assert score == 0.0
