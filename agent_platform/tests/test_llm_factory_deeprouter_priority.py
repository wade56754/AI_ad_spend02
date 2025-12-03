"""
Tests for LLM factory backend priority with DeepRouter support.

验证当同时配置 ANTHROPIC_API_KEY + ANTHROPIC_BASE_URL（指向 DeepRouter）时，
优先使用 Anthropic API 风格，而不是回退到 Claude Code CLI。
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import sys

from agent_platform.llm.factory import get_llm_client, get_backend_type, reset_client


class TestDeepRouterPriority:
    """测试 DeepRouter 代理的优先级逻辑"""

    def test_anthropic_api_priority_over_claude_cli(self, monkeypatch, tmp_path):
        """
        当有 ANTHROPIC_API_KEY + ANTHROPIC_BASE_URL（DeepRouter）时，
        应该优先使用 Anthropic API 风格，而不是 Claude Code CLI。
        """
        reset_client()
        
        # 设置环境变量
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-deeprouter-token")
        monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://deeprouter.top")
        monkeypatch.delenv("LLM_BACKEND", raising=False)
        
        # Mock Anthropic SDK
        mock_anthropic_client = MagicMock()
        mock_anthropic_class = MagicMock(return_value=mock_anthropic_client)
        mock_anthropic_module = MagicMock()
        mock_anthropic_module.Anthropic = mock_anthropic_class
        
        import sys
        from agent_platform import llm
        with patch.object(llm.factory, "_REPO_ROOT", tmp_path), \
             patch.dict(sys.modules, {"anthropic": mock_anthropic_module}):
            client = get_llm_client()
            backend = get_backend_type()
        
        # 应该使用 anthropic_api 后端，而不是 claude_code
        assert backend == "anthropic_api", f"Expected anthropic_api, got {backend}"
        assert client.__class__.__name__ == "AnthropicLLMClient"
        
        # 验证 Anthropic 客户端被调用，而不是 Claude Code CLI
        mock_anthropic_class.assert_called_once()
        # 验证 base_url 被正确设置
        call_kwargs = mock_anthropic_class.call_args[1]
        assert "base_url" in call_kwargs
        assert "deeprouter.top" in str(call_kwargs["base_url"]).lower()

    def test_llm_backend_deeprouter_with_anthropic_key(self, monkeypatch, tmp_path):
        """
        当 LLM_BACKEND=deeprouter 但同时有 ANTHROPIC_API_KEY + ANTHROPIC_BASE_URL 时，
        应该使用 Anthropic API 风格（推荐），而不是 DeepRouterLLMClient。
        """
        reset_client()
        
        # 设置环境变量
        monkeypatch.setenv("LLM_BACKEND", "deeprouter")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-token")
        monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://deeprouter.top")
        
        # Mock Anthropic SDK
        mock_anthropic_client = MagicMock()
        mock_anthropic_class = MagicMock(return_value=mock_anthropic_client)
        mock_anthropic_module = MagicMock()
        mock_anthropic_module.Anthropic = mock_anthropic_class
        
        import sys
        from agent_platform import llm
        with patch.object(llm.factory, "_REPO_ROOT", tmp_path), \
             patch.dict(sys.modules, {"anthropic": mock_anthropic_module}):
            client = get_llm_client()
            backend = get_backend_type()
        
        # 应该使用 anthropic_api 后端（通过 DeepRouter 代理）
        assert backend == "anthropic_api", f"Expected anthropic_api, got {backend}"
        assert client.__class__.__name__ == "AnthropicLLMClient"

    def test_fallback_to_claude_cli_when_no_api_key(self, monkeypatch):
        """
        当没有 ANTHROPIC_API_KEY 时，应该回退到 Claude Code CLI。
        """
        reset_client()
        
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
        monkeypatch.delenv("LLM_BACKEND", raising=False)
        
        # Mock Claude Code CLI
        mock_claude_code_client = MagicMock()
        mock_claude_code_class = MagicMock(return_value=mock_claude_code_client)
        
        with patch("agent_platform.llm.factory._create_claude_code_client") as mock_create:
            mock_create.return_value = mock_claude_code_client
            
            client = get_llm_client()
            backend = get_backend_type()
        
        # 应该使用 claude_code 后端
        assert backend == "claude_code"
        mock_create.assert_called_once()

    def test_anthropic_api_without_base_url_uses_official(self, monkeypatch, tmp_path):
        """
        当有 ANTHROPIC_API_KEY 但没有 base_url 时，使用官方 API。
        """
        reset_client()
        
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-token")
        monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
        
        # Mock Anthropic SDK
        mock_anthropic_client = MagicMock()
        mock_anthropic_class = MagicMock(return_value=mock_anthropic_client)
        mock_anthropic_module = MagicMock()
        mock_anthropic_module.Anthropic = mock_anthropic_class
        
        import sys
        from agent_platform import llm
        with patch.object(llm.factory, "_REPO_ROOT", tmp_path), \
             patch.dict(sys.modules, {"anthropic": mock_anthropic_module}):
            client = get_llm_client()
            backend = get_backend_type()
        
        assert backend == "anthropic_api"
        # 验证没有传递 base_url（使用官方端点）
        call_kwargs = mock_anthropic_class.call_args[1] if mock_anthropic_class.call_args else {}
        assert "base_url" not in call_kwargs or call_kwargs.get("base_url") is None

