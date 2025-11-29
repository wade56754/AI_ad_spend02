"""
Tests for Claude Code CLI Adapter (claude_code_adapter.py)

Migrated from tests/agents_legacy/test_claude_code_adapter.py
Tests JSON extraction and mock response structures.
"""

import pytest
import json
from agents.tools.claude_code_adapter import (
    _extract_json,
    ClaudeCodeClient,
    _MockResponse,
    _MockTextBlock,
    check_claude_code_available,
    CLAUDE_CODE_CONFIG,
)


class TestExtractJson:
    """Tests for _extract_json function."""

    def test_extract_pure_json_object(self):
        """Should extract pure JSON object."""
        text = '{"key": "value", "number": 42}'
        result = _extract_json(text)
        assert result == {"key": "value", "number": 42}

    def test_extract_pure_json_array(self):
        """Should extract pure JSON array."""
        text = '[1, 2, 3]'
        result = _extract_json(text)
        assert result == [1, 2, 3]

    def test_extract_json_from_markdown_code_block(self):
        """Should extract JSON from markdown code block."""
        text = '''
Here is the response:

```json
{"changes": [{"file": "test.py", "content": "hello"}]}
```

That's all.
'''
        result = _extract_json(text)
        assert result["changes"][0]["file"] == "test.py"

    def test_extract_json_from_plain_code_block(self):
        """Should extract JSON from plain code block without json tag."""
        text = '''
```
{"key": "value"}
```
'''
        result = _extract_json(text)
        assert result == {"key": "value"}

    def test_extract_json_embedded_in_text(self):
        """Should extract JSON embedded in surrounding text."""
        text = '''
Here is your result:
{"success": true, "data": {"count": 5}}
Thank you!
'''
        result = _extract_json(text)
        assert result["success"] is True
        assert result["data"]["count"] == 5

    def test_extract_json_with_nested_structure(self):
        """Should handle nested JSON structures."""
        text = '{"outer": {"inner": {"deep": "value"}}}'
        result = _extract_json(text)
        assert result["outer"]["inner"]["deep"] == "value"

    def test_invalid_json_raises_error(self):
        """Should raise JSONDecodeError for invalid JSON."""
        text = "This is not JSON at all"
        with pytest.raises(json.JSONDecodeError):
            _extract_json(text)

    def test_malformed_json_raises_error(self):
        """Should raise JSONDecodeError for malformed JSON."""
        text = '{"key": "missing closing brace"'
        with pytest.raises(json.JSONDecodeError):
            _extract_json(text)


class TestMockResponse:
    """Tests for mock response classes."""

    def test_mock_response_structure(self):
        """MockResponse should have proper content structure."""
        response = _MockResponse("Hello, World!")
        assert hasattr(response, "content")
        assert len(response.content) == 1
        assert response.content[0].type == "text"
        assert response.content[0].text == "Hello, World!"

    def test_mock_text_block(self):
        """MockTextBlock should have text and type attributes."""
        block = _MockTextBlock("Test content")
        assert block.type == "text"
        assert block.text == "Test content"


class TestClaudeCodeClient:
    """Tests for ClaudeCodeClient class."""

    def test_client_has_messages_attribute(self):
        """Client should have messages attribute."""
        client = ClaudeCodeClient()
        assert hasattr(client, "messages")
        assert hasattr(client.messages, "create")

    def test_messages_api_has_create_method(self):
        """Messages API should have create method."""
        client = ClaudeCodeClient()
        assert callable(client.messages.create)


class TestClaudeCodeConfig:
    """Tests for configuration constants."""

    def test_config_has_required_keys(self):
        """Config should have all required keys."""
        assert "command" in CLAUDE_CODE_CONFIG
        assert "timeout" in CLAUDE_CODE_CONFIG
        assert "max_retries" in CLAUDE_CODE_CONFIG

    def test_timeout_is_reasonable(self):
        """Timeout should be a reasonable value."""
        assert CLAUDE_CODE_CONFIG["timeout"] >= 60
        assert CLAUDE_CODE_CONFIG["timeout"] <= 600


class TestCheckClaudeCodeAvailable:
    """Tests for check_claude_code_available function."""

    def test_returns_dict_structure(self):
        """Should return proper dictionary structure."""
        result = check_claude_code_available()
        assert isinstance(result, dict)
        assert "available" in result
        assert "path" in result
        assert "version" in result
        assert "error" in result

    def test_available_is_bool(self):
        """Available field should be boolean."""
        result = check_claude_code_available()
        assert isinstance(result["available"], bool)


class TestRetryMechanism:
    """Tests for call_claude_code retry mechanism (P1-02 fix)."""

    def test_config_has_retry_settings(self):
        """Config should have retry-related settings."""
        assert "max_retries" in CLAUDE_CODE_CONFIG
        assert "retry_delay" in CLAUDE_CODE_CONFIG
        assert "retry_backoff" in CLAUDE_CODE_CONFIG

    def test_retry_config_values_reasonable(self):
        """Retry config values should be reasonable."""
        assert CLAUDE_CODE_CONFIG["max_retries"] >= 0
        assert CLAUDE_CODE_CONFIG["max_retries"] <= 5
        assert CLAUDE_CODE_CONFIG["retry_delay"] >= 0.5
        assert CLAUDE_CODE_CONFIG["retry_backoff"] >= 1.0

    def test_call_claude_code_returns_retries_count(self, monkeypatch):
        """call_claude_code should return retries count in result."""
        from agents.tools import claude_code_adapter

        # Mock _find_claude_cli to return None (CLI not found)
        monkeypatch.setattr(claude_code_adapter, "_find_claude_cli", lambda: None)

        from agents.tools.claude_code_adapter import call_claude_code
        result = call_claude_code("test prompt")

        assert "retries" in result
        assert isinstance(result["retries"], int)
        assert result["retries"] == 0  # No retries when CLI not found

    def test_non_retryable_error_returns_immediately(self, monkeypatch):
        """Non-retryable errors (CLI not found) should not retry."""
        from agents.tools import claude_code_adapter

        call_count = {"value": 0}

        def mock_find_cli():
            call_count["value"] += 1
            return None  # CLI not found

        monkeypatch.setattr(claude_code_adapter, "_find_claude_cli", mock_find_cli)

        from agents.tools.claude_code_adapter import call_claude_code
        result = call_claude_code("test prompt", max_retries=3)

        assert result["success"] is False
        assert call_count["value"] == 1  # Only called once, no retries

    def test_result_includes_error_on_failure(self, monkeypatch):
        """Failed calls should include error message."""
        from agents.tools import claude_code_adapter
        monkeypatch.setattr(claude_code_adapter, "_find_claude_cli", lambda: None)

        from agents.tools.claude_code_adapter import call_claude_code
        result = call_claude_code("test prompt")

        assert result["success"] is False
        assert result["error"] is not None
        assert isinstance(result["error"], str)
        assert len(result["error"]) > 0
