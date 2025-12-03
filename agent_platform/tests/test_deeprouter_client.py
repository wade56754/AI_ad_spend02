"""
Tests for agent_platform.llm.deeprouter_client module.

集成测试 DeepRouter LLM Client，验证与 DeepRouter API 的交互。
"""

import os
import pytest
from unittest.mock import MagicMock, patch

from agent_platform.llm.deeprouter_client import DeepRouterLLMClient
from agent_platform.core.exceptions import LLMClientError


class TestDeepRouterLLMClientInit:
    """Tests for DeepRouterLLMClient initialization."""

    def test_init_requires_token(self, monkeypatch):
        """Should raise error if token is not provided."""
        monkeypatch.delenv("DEEPROUTER_CLAUDE_TOKEN", raising=False)

        with pytest.raises(LLMClientError) as exc_info:
            DeepRouterLLMClient()

        assert "DEEPROUTER_CLAUDE_TOKEN" in str(exc_info.value)

    def test_init_with_token_param(self):
        """Should initialize with token parameter."""
        client = DeepRouterLLMClient(token="test-token-123")
        assert client._token == "test-token-123"
        assert client._base_url == "https://deeprouter.top"
        assert client._model == "claude-sonnet-4-20250514"

    def test_init_with_env_token(self, monkeypatch):
        """Should initialize with token from environment variable."""
        monkeypatch.setenv("DEEPROUTER_CLAUDE_TOKEN", "env-token-456")
        monkeypatch.setenv("DEEPROUTER_BASE_URL", "https://custom.example.com")
        monkeypatch.setenv("DEEPROUTER_MODEL", "claude-opus-4")

        client = DeepRouterLLMClient()

        assert client._token == "env-token-456"
        assert client._base_url == "https://custom.example.com"
        assert client._model == "claude-opus-4"

    def test_init_uses_defaults(self, monkeypatch):
        """Should use default values when env vars not set."""
        monkeypatch.setenv("DEEPROUTER_CLAUDE_TOKEN", "test-token")

        client = DeepRouterLLMClient()

        assert client._base_url == "https://deeprouter.top"
        assert client._model == "claude-sonnet-4-20250514"
        assert client._api_url == "https://deeprouter.top/v1/messages"


class TestDeepRouterLLMClientGenerate:
    """Tests for DeepRouterLLMClient.generate() method."""

    @pytest.fixture
    def client(self):
        """Create a DeepRouterLLMClient instance for testing."""
        return DeepRouterLLMClient(token="test-token")

    def test_generate_success_openai_format(self, client):
        """Should parse OpenAI-style response format."""
        mock_response_data = {
            "model": "claude-sonnet-4-20250514",
            "choices": [
                {
                    "message": {
                        "content": "Hello, this is a test response."
                    }
                }
            ],
            "usage": {
                "input_tokens": 10,
                "output_tokens": 5
            }
        }

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client_class.return_value.__exit__.return_value = None

            resp = client.generate(system="You are a helpful assistant", user="Hello")

            assert resp.text == "Hello, this is a test response."
            assert resp.model == "claude-sonnet-4-20250514"
            assert resp.usage["input_tokens"] == 10
            assert resp.usage["output_tokens"] == 5
            assert resp.raw == mock_response_data

    def test_generate_success_anthropic_format(self, client):
        """Should parse Anthropic-style response format."""
        mock_response_data = {
            "model": "claude-sonnet-4-20250514",
            "content": [
                {"type": "text", "text": "This is an Anthropic-style response."}
            ],
            "usage": {
                "input_tokens": 15,
                "output_tokens": 8
            }
        }

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client_class.return_value.__exit__.return_value = None

            resp = client.generate(system="You are a helpful assistant", user="Hello")

            assert resp.text == "This is an Anthropic-style response."
            assert resp.model == "claude-sonnet-4-20250514"
            assert resp.usage["input_tokens"] == 15
            assert resp.usage["output_tokens"] == 8

    def test_generate_http_error(self, client):
        """Should raise LLMClientError on HTTP error."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client_class.return_value.__exit__.return_value = None

            with pytest.raises(LLMClientError) as exc_info:
                client.generate(system="Test", user="Hello")

            assert "DeepRouter API call failed" in str(exc_info.value)

    def test_generate_request_error(self, client):
        """Should raise LLMClientError on request error."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.post.side_effect = Exception("Connection error")
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client_class.return_value.__exit__.return_value = None

            with pytest.raises(LLMClientError) as exc_info:
                client.generate(system="Test", user="Hello")

            assert "DeepRouter API request failed" in str(exc_info.value)

    def test_generate_sets_correct_headers(self, client):
        """Should set correct headers including Authorization and x-api-key."""
        mock_response_data = {
            "choices": [{"message": {"content": "Test"}}],
            "usage": {"input_tokens": 0, "output_tokens": 0}
        }

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client_class.return_value.__exit__.return_value = None

            client.generate(system="Test", user="Hello")

            # 验证请求参数
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "https://deeprouter.top/v1/messages"
            
            headers = call_args[1]["headers"]
            assert headers["Authorization"] == "Bearer test-token"
            assert headers["x-api-key"] == "test-token"
            assert headers["Content-Type"] == "application/json"
            assert headers["Accept"] == "application/json"

    def test_generate_sets_correct_body(self, client):
        """Should set correct request body with system, messages, max_tokens."""
        mock_response_data = {
            "choices": [{"message": {"content": "Test"}}],
            "usage": {"input_tokens": 0, "output_tokens": 0}
        }

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client_class.return_value.__exit__.return_value = None

            client.generate(
                system="You are helpful",
                user="What is 2+2?",
                max_tokens=100,
                temperature=0.7
            )

            # 验证请求体
            call_args = mock_client.post.call_args
            body = call_args[1]["json"]
            
            assert body["model"] == "claude-sonnet-4-20250514"
            assert body["system"] == "You are helpful"
            assert body["messages"] == [{"role": "user", "content": "What is 2+2?"}]
            assert body["max_tokens"] == 100
            assert body["temperature"] == 0.7
            assert body["stream"] is False


class TestDeepRouterLLMClientIntegration:
    """Integration tests for DeepRouterLLMClient (requires real token)."""

    @pytest.mark.skipif(
        not os.environ.get("DEEPROUTER_CLAUDE_TOKEN"),
        reason="DEEPROUTER_CLAUDE_TOKEN not set, skipping integration test"
    )
    def test_generate_real_api_call(self):
        """Test actual API call to DeepRouter (requires DEEPROUTER_CLAUDE_TOKEN)."""
        client = DeepRouterLLMClient()

        resp = client.generate(
            system="你是一个智能AI助手",
            user="请用一句话介绍你自己",
            max_tokens=100
        )

        # 验证响应
        assert isinstance(resp.text, str)
        assert len(resp.text) > 0
        assert isinstance(resp.raw, dict)
        assert "model" in resp.raw or "choices" in resp.raw or "content" in resp.raw

