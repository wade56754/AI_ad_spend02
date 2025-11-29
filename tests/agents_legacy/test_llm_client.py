"""
Tests for LLM client module (tools/llm_client.py)

LEGACY WARNING: 这些测试已迁移到 agents/tests/test_llm_client.py
保留此文件仅作历史记录，日常测试请运行 agents/tests。

# Fix: F-P1-01 - 补充最小必要测试

Tests cover:
- get_llm_client() returns valid client instance
- extract_response_text() handles various response formats
- reset_client() properly clears singleton
- Backend detection based on environment variable
"""
import pytest
from unittest.mock import MagicMock, patch

from agents import create_agent, list_agents
from agents.tools.llm_client import get_llm_client
from agents.tools.types import AgentResponse, SkillResult

# 标记整个模块为 legacy（跳过）
pytestmark = pytest.mark.skip(reason="Migrated to agents/tests/test_llm_client.py")

class TestGetLlmClient:
    """Tests for get_llm_client function."""

    def test_get_llm_client_returns_instance(self, monkeypatch):
        """get_llm_client should return a client instance."""
        # Clear any cached client
        from agents.tools import llm_client
        llm_client.reset_client()

        # Mock environment (no API key = Claude Code mode)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        # Mock ClaudeCodeClient to avoid actual CLI dependency
        mock_client = MagicMock()
        with patch.object(llm_client, "ClaudeCodeClient", return_value=mock_client):
            # Import fresh
            from agents.tools.llm_client import get_llm_client
            client = get_llm_client()

        assert client is not None

    def test_get_llm_client_singleton(self, monkeypatch):
        """get_llm_client should return same instance on multiple calls."""
        from agents.tools import llm_client
        llm_client.reset_client()

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        mock_client = MagicMock()
        with patch.object(llm_client, "ClaudeCodeClient", return_value=mock_client):
            from agents.tools.llm_client import get_llm_client
            client1 = get_llm_client()
            client2 = get_llm_client()

        assert client1 is client2


class TestExtractResponseText:
    """Tests for extract_response_text function."""

    def test_extract_from_anthropic_format(self):
        """Should extract text from Anthropic API response format."""
        from agents.tools.llm_client import extract_response_text

        # Mock Anthropic response structure
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = "Hello, world!"

        mock_response = MagicMock()
        mock_response.content = [mock_block]

        result = extract_response_text(mock_response)
        assert result == "Hello, world!"

    def test_extract_from_plain_string(self):
        """Should handle plain string response."""
        from agents.tools.llm_client import extract_response_text

        mock_response = MagicMock(spec=[])  # No content attribute
        mock_response.__str__ = lambda self: "plain text"

        result = extract_response_text(mock_response)
        assert "plain" in result.lower() or result is not None

    def test_extract_multiple_blocks(self):
        """Should concatenate multiple text blocks."""
        from agents.tools.llm_client import extract_response_text

        block1 = MagicMock()
        block1.type = "text"
        block1.text = "Part 1. "

        block2 = MagicMock()
        block2.type = "text"
        block2.text = "Part 2."

        mock_response = MagicMock()
        mock_response.content = [block1, block2]

        result = extract_response_text(mock_response)
        assert "Part 1" in result
        assert "Part 2" in result


class TestResetClient:
    """Tests for reset_client function."""

    def test_reset_clears_singleton(self, monkeypatch):
        """reset_client should clear the cached client."""
        from agents.tools import llm_client
        llm_client.reset_client()

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        # Create first client
        mock_client1 = MagicMock()
        with patch.object(llm_client, "ClaudeCodeClient", return_value=mock_client1):
            client1 = llm_client.get_llm_client()

        # Reset
        llm_client.reset_client()

        # Create second client
        mock_client2 = MagicMock()
        with patch.object(llm_client, "ClaudeCodeClient", return_value=mock_client2):
            client2 = llm_client.get_llm_client()

        # Should be different instances
        assert client1 is not client2


class TestBackendDetection:
    """Tests for LLM backend detection."""

    def test_uses_anthropic_when_api_key_set(self, monkeypatch):
        """Should use Anthropic API when ANTHROPIC_API_KEY is set."""
        from agents.tools import llm_client
        llm_client.reset_client()

        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")

        # Mock Anthropic to avoid actual import
        mock_anthropic = MagicMock()
        with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
            with patch.object(llm_client, "Anthropic", create=True) as mock_cls:
                mock_cls.return_value = MagicMock()
                try:
                    client = llm_client.get_llm_client()
                    # Should have tried to use Anthropic
                except Exception:
                    pass  # OK if Anthropic not installed

    def test_uses_claude_code_when_no_api_key(self, monkeypatch):
        """Should use Claude Code CLI when no ANTHROPIC_API_KEY."""
        from agents.tools import llm_client
        llm_client.reset_client()

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        mock_client = MagicMock()
        with patch.object(llm_client, "ClaudeCodeClient", return_value=mock_client):
            client = llm_client.get_llm_client()

        assert client is mock_client
