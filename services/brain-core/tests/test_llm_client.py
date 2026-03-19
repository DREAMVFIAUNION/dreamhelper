"""LLM Client 测试 — 提供商注册 + 模型列表"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.modules.llm.llm_client import LLMClient


class TestLLMClient:

    def setup_method(self):
        self.client = LLMClient()

    def test_providers_registered(self):
        assert len(self.client.providers) >= 1
        names = [p.name for p in self.client.providers]
        assert "minimax" in names

    def test_list_models(self):
        models = self.client.list_models()
        assert len(models) >= 1
        for m in models:
            assert "id" in m
            assert "provider" in m

    def test_get_provider_minimax(self):
        provider = self.client._get_provider("MiniMax-M2.5-highspeed")
        assert provider.name == "minimax"

    def test_get_provider_fallback(self):
        # Unknown model should fall back to first provider
        provider = self.client._get_provider("unknown-model-xyz")
        assert provider is not None

    def test_minimax_models_in_list(self):
        models = self.client.list_models()
        ids = [m["id"] for m in models]
        assert "MiniMax-M2.5" in ids or "MiniMax-M2.5-highspeed" in ids
