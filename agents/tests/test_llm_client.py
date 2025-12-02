"""
Tests for LLM client module (tools/llm_client.py)

Migrated from tests/agents_legacy/test_llm_client.py
Fixed: Added missing imports (MagicMock, patch)
Fixed: P1-TEST - Corrected patch location for ClaudeCodeClient (imported inside function)
"""

import pytest
from unittest.mock import MagicMock, patch


class TestGetLlmClient:
    """Tests for get_llm_client function."""

    def test_get_llm_client_returns_instance(self, monkeypatch):
        """get_llm_client should return a client instance."""
        from agents.tools import llm_client
        llm_client.reset_client()

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        mock_client = MagicMock()
        # Fix: ClaudeCodeClient is imported inside get_llm_client(), patch at source
        with patch(
            "agents.tools.claude_code_adapter.ClaudeCodeClient",
            return_value=mock_client,
        ), patch(
            "agents.tools.claude_code_adapter.check_claude_code_available",
            return_value={"available": True, "path": "claude", "version": "1.0"},
        ):
            from agents.tools.llm_client import get_llm_client
            client = get_llm_client()

        assert client is not None

    def test_get_llm_client_singleton(self, monkeypatch):
        """get_llm_client should return same instance on multiple calls."""
        from agents.tools import llm_client
        llm_client.reset_client()

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        mock_client = MagicMock()
        # Fix: ClaudeCodeClient is imported inside get_llm_client(), patch at source
        with patch(
            "agents.tools.claude_code_adapter.ClaudeCodeClient",
            return_value=mock_client,
        ), patch(
            "agents.tools.claude_code_adapter.check_claude_code_available",
            return_value={"available": True, "path": "claude", "version": "1.0"},
        ):
            from agents.tools.llm_client import get_llm_client
            client1 = get_llm_client()
            client2 = get_llm_client()

        assert client1 is client2

    def test_get_llm_client_prefers_anthropic_when_api_key_set(self, monkeypatch):
        """When API key exists, Anthropic client should be used instead of CLI."""
        from agents.tools import llm_client
        llm_client.reset_client()

        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")

        mock_api_client = MagicMock(name="AnthropicClient")
        with patch(
            "anthropic.Anthropic",
            return_value=mock_api_client,
        ) as mock_anthropic, patch(
            "agents.tools.claude_code_adapter.ClaudeCodeClient",
        ) as mock_cli:
            from agents.tools.llm_client import get_llm_client
            client = get_llm_client()

        assert client is mock_api_client
        mock_anthropic.assert_called_once()
        mock_cli.assert_not_called()


class TestExtractResponseText:
    """Tests for extract_response_text function."""

    def test_extract_from_anthropic_format(self):
        """Should extract text from Anthropic API response format."""
        from agents.tools.llm_client import extract_response_text

        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = "Hello, world!"

        mock_response = MagicMock()
        mock_response.content = [mock_block]

        result = extract_response_text(mock_response)
        assert result == "Hello, world!"

    def test_extract_from_plain_string(self):
        """Should handle plain string response (no .content attribute)."""
        from agents.tools.llm_client import extract_response_text

        # Fix: Use a simple object without .content attribute
        # The extract_response_text function calls str(resp) when no .content
        class PlainResponse:
            def __str__(self):
                return "plain text"

        mock_response = PlainResponse()

        result = extract_response_text(mock_response)
        assert result == "plain text"

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

    def test_extract_from_empty_content(self):
        """Should return empty string when content list is empty.

        P1-01 边界测试：验证 content = [] 时返回空字符串。
        """
        from agents.tools.llm_client import extract_response_text

        mock_response = MagicMock()
        mock_response.content = []

        result = extract_response_text(mock_response)
        assert result == ""

    def test_extract_from_nested_content(self):
        """Should extract text from nested content lists.

        P1-01 边界测试：验证嵌套列表 [[TextBlock1], [TextBlock2]] 能正确拼接。
        llm_client.py:115-118 处理此分支。
        """
        from agents.tools.llm_client import extract_response_text

        # 创建嵌套的 text blocks
        block1 = MagicMock()
        block1.type = "text"
        block1.text = "Nested 1. "

        block2 = MagicMock()
        block2.type = "text"
        block2.text = "Nested 2."

        mock_response = MagicMock()
        # 嵌套列表格式：[[block1], [block2]]
        mock_response.content = [[block1], [block2]]

        result = extract_response_text(mock_response)
        assert "Nested 1" in result
        assert "Nested 2" in result

    def test_extract_ignores_non_text_blocks(self):
        """Should skip non-text blocks (e.g., image, tool_use).

        P1-01 边界测试：验证混合类型 content 中跳过非 text 类型。
        """
        from agents.tools.llm_client import extract_response_text

        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Only text content"

        image_block = MagicMock()
        image_block.type = "image"  # 应被跳过

        tool_use_block = MagicMock()
        tool_use_block.type = "tool_use"  # 应被跳过

        mock_response = MagicMock()
        mock_response.content = [image_block, text_block, tool_use_block]

        result = extract_response_text(mock_response)
        assert result == "Only text content"

    def test_extract_handles_block_without_type(self):
        """Should skip blocks without 'type' attribute.

        P1-01 边界测试：验证缺少 type 属性的 block 被安全跳过。
        llm_client.py:120 使用 getattr(item, "type", None) 处理此情况。
        """
        from agents.tools.llm_client import extract_response_text

        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Valid block"

        # 创建一个没有 type 属性的对象
        class BlockWithoutType:
            pass

        invalid_block = BlockWithoutType()

        mock_response = MagicMock()
        mock_response.content = [invalid_block, text_block]

        result = extract_response_text(mock_response)
        assert result == "Valid block"


class TestResetClient:
    """Tests for reset_client function."""

    def test_reset_clears_singleton(self, monkeypatch):
        """reset_client should clear the cached client."""
        from agents.tools import llm_client
        llm_client.reset_client()

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        mock_client1 = MagicMock()
        # Fix: Patch at source module
        with patch(
            "agents.tools.claude_code_adapter.ClaudeCodeClient",
            return_value=mock_client1,
        ), patch(
            "agents.tools.claude_code_adapter.check_claude_code_available",
            return_value={"available": True, "path": "claude", "version": "1.0"},
        ):
            client1 = llm_client.get_llm_client()

        llm_client.reset_client()

        mock_client2 = MagicMock()
        with patch(
            "agents.tools.claude_code_adapter.ClaudeCodeClient",
            return_value=mock_client2,
        ), patch(
            "agents.tools.claude_code_adapter.check_claude_code_available",
            return_value={"available": True, "path": "claude", "version": "1.0"},
        ):
            client2 = llm_client.get_llm_client()

        assert client1 is not client2


class TestBackendDetection:
    """Tests for LLM backend detection."""

    def test_uses_claude_code_when_no_api_key(self, monkeypatch):
        """Should use Claude Code CLI when no ANTHROPIC_API_KEY."""
        from agents.tools import llm_client
        llm_client.reset_client()

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        mock_client = MagicMock()
        # Fix: Patch at source module
        with patch(
            "agents.tools.claude_code_adapter.ClaudeCodeClient",
            return_value=mock_client,
        ), patch(
            "agents.tools.claude_code_adapter.check_claude_code_available",
            return_value={"available": True, "path": "claude", "version": "1.0"},
        ):
            client = llm_client.get_llm_client()

        assert client is mock_client
