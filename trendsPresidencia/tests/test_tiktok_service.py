"""Tests para TikTokService (filtrado anti-bot)"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from services.tiktok_service import TikTokService


class TestTikTokService:
    """Tests del servicio de TikTok"""

    @pytest.fixture
    def tiktok_svc(self):
        return TikTokService()

    def test_is_bot_account_few_followers(self, tiktok_svc):
        """Cuenta con pocos seguidores es bot"""
        video = {
            "author": {
                "followers": 30,
                "following": 10,
                "video_count": 50,
                "username": "real_user",
            }
        }
        assert tiktok_svc._is_bot_account(video) is True

    def test_is_bot_account_spam_ratio(self, tiktok_svc):
        """Ratio following/followers muy alto indica spam"""
        video = {
            "author": {
                "followers": 50,
                "following": 600,  # 12x más siguiendo (> 10x)
                "video_count": 20,
                "username": "spam_account",
            }
        }
        assert tiktok_svc._is_bot_account(video) is True

    def test_is_bot_account_many_videos_few_followers(self, tiktok_svc):
        "Muchos videos pero pocos seguidores es sospechoso"
        video = {
            "author": {
                "followers": 80,
                "following": 100,
                "video_count": 1500,
                "username": "content_farm",
            }
        }
        assert tiktok_svc._is_bot_account(video) is True

    def test_is_real_account(self, tiktok_svc):
        "Cuenta con métricas saludables no es bot"
        video = {
            "author": {
                "followers": 10000,
                "following": 500,
                "video_count": 200,
                "username": "verified_creator",
            }
        }
        assert tiktok_svc._is_bot_account(video) is False

    @pytest.mark.asyncio
    async def test_calculate_tiktok_score_no_api_key(self, tiktok_svc):
        "Sin API key devuelve 0"
        score = await tiktok_svc.calculate_tiktok_score("Abelardo")
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_calculate_tiktok_score_no_results(self, tiktok_svc):
        "Sin videos devuelve 0"
        with patch.object(tiktok_svc, 'get_hashtag_metrics', return_value={"real_accounts": 0}):
            score = await tiktok_svc.calculate_tiktok_score("Abelardo")
            assert score == 0.0
