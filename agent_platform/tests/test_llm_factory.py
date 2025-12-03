"""
Tests for agent_platform.llm.factory module.

Phase 3.0C: Tests for multi-source configuration loading.
- ANTHROPIC_API_KEY loading from env/.env.local/anthropic.json
- ANTHROPIC_BASE_URL loading from env/.env.local/anthropic.json
- Priority chain: env > .env.local > anthropic.json
"""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile


class TestLoadAnthropicApiKey:
    """Tests for _load_anthropic_api_key function."""

    def test_loads_from_env_first(self, monkeypatch):
        """Environment variable has highest priority."""
        from agent_platform.llm import factory

        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-api-key")

        api_key, source = factory._load_anthropic_api_key()

        assert api_key == "env-api-key"
        assert source == "env"

    def test_loads_from_env_local_when_no_env(self, monkeypatch, tmp_path):
        """Falls back to .env.local when env var not set."""
        from agent_platform.llm import factory

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        # Create temp .env.local
        env_local = tmp_path / ".env.local"
        env_local.write_text('ANTHROPIC_API_KEY="local-api-key"\n')

        # Patch _REPO_ROOT
        with patch.object(factory, "_REPO_ROOT", tmp_path):
            api_key, source = factory._load_anthropic_api_key()

        assert api_key == "local-api-key"
        assert source == ".env.local"

    def test_loads_from_json_when_no_env_local(self, monkeypatch, tmp_path):
        """Falls back to anthropic.json when .env.local not found."""
        from agent_platform.llm import factory

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        # Create temp anthropic.json
        config_dir = tmp_path / "local_config"
        config_dir.mkdir()
        json_file = config_dir / "anthropic.json"
        json_file.write_text(json.dumps({"ANTHROPIC_API_KEY": "json-api-key"}))

        with patch.object(factory, "_REPO_ROOT", tmp_path):
            api_key, source = factory._load_anthropic_api_key()

        assert api_key == "json-api-key"
        assert source == "anthropic.json"

    def test_returns_none_when_no_key_found(self, monkeypatch, tmp_path):
        """Returns None when no key found in any source."""
        from agent_platform.llm import factory

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with patch.object(factory, "_REPO_ROOT", tmp_path):
            api_key, source = factory._load_anthropic_api_key()

        assert api_key is None
        assert source is None


class TestLoadAnthropicBaseUrl:
    """Tests for _load_anthropic_base_url function."""

    def test_loads_from_env_first(self, monkeypatch):
        """Environment variable has highest priority."""
        from agent_platform.llm import factory

        monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://env.example.com")

        base_url, source = factory._load_anthropic_base_url()

        assert base_url == "https://env.example.com"
        assert source == "env"

    def test_loads_from_env_local_when_no_env(self, monkeypatch, tmp_path):
        """Falls back to .env.local when env var not set."""
        from agent_platform.llm import factory

        monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)

        # Create temp .env.local
        env_local = tmp_path / ".env.local"
        env_local.write_text('ANTHROPIC_BASE_URL="https://local.example.com"\n')

        with patch.object(factory, "_REPO_ROOT", tmp_path):
            base_url, source = factory._load_anthropic_base_url()

        assert base_url == "https://local.example.com"
        assert source == ".env.local"

    def test_loads_from_json_when_no_env_local(self, monkeypatch, tmp_path):
        """Falls back to anthropic.json when .env.local not found."""
        from agent_platform.llm import factory

        monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)

        # Create temp anthropic.json
        config_dir = tmp_path / "local_config"
        config_dir.mkdir()
        json_file = config_dir / "anthropic.json"
        json_file.write_text(json.dumps({
            "ANTHROPIC_BASE_URL": "https://json.example.com"
        }))

        with patch.object(factory, "_REPO_ROOT", tmp_path):
            base_url, source = factory._load_anthropic_base_url()

        assert base_url == "https://json.example.com"
        assert source == "anthropic.json"

    def test_returns_none_for_official_endpoint(self, monkeypatch, tmp_path):
        """Returns None when no base_url configured (use official endpoint)."""
        from agent_platform.llm import factory

        monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)

        with patch.object(factory, "_REPO_ROOT", tmp_path):
            base_url, source = factory._load_anthropic_base_url()

        assert base_url is None
        assert source is None

    def test_env_not_overridden_by_local_files(self, monkeypatch, tmp_path):
        """Environment variable should NOT be overridden by local files."""
        from agent_platform.llm import factory

        monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://env.example.com")

        # Create .env.local with different value
        env_local = tmp_path / ".env.local"
        env_local.write_text('ANTHROPIC_BASE_URL="https://should-not-use.com"\n')

        with patch.object(factory, "_REPO_ROOT", tmp_path):
            base_url, source = factory._load_anthropic_base_url()

        # Should use env, not .env.local
        assert base_url == "https://env.example.com"
        assert source == "env"


class TestParseEnvFile:
    """Tests for _parse_env_file function."""

    def test_parses_simple_key_value(self, tmp_path):
        """Should parse simple KEY=value format."""
        from agent_platform.llm.factory import _parse_env_file

        env_file = tmp_path / ".env.local"
        env_file.write_text("ANTHROPIC_API_KEY=simple-key\n")

        result = _parse_env_file(env_file, "ANTHROPIC_API_KEY")
        assert result == "simple-key"

    def test_parses_double_quoted_value(self, tmp_path):
        """Should strip double quotes from value."""
        from agent_platform.llm.factory import _parse_env_file

        env_file = tmp_path / ".env.local"
        env_file.write_text('ANTHROPIC_API_KEY="quoted-key"\n')

        result = _parse_env_file(env_file, "ANTHROPIC_API_KEY")
        assert result == "quoted-key"

    def test_parses_single_quoted_value(self, tmp_path):
        """Should strip single quotes from value."""
        from agent_platform.llm.factory import _parse_env_file

        env_file = tmp_path / ".env.local"
        env_file.write_text("ANTHROPIC_API_KEY='single-quoted'\n")

        result = _parse_env_file(env_file, "ANTHROPIC_API_KEY")
        assert result == "single-quoted"

    def test_ignores_comments(self, tmp_path):
        """Should ignore comment lines."""
        from agent_platform.llm.factory import _parse_env_file

        env_file = tmp_path / ".env.local"
        env_file.write_text(
            "# This is a comment\n"
            "ANTHROPIC_API_KEY=real-key\n"
            "# Another comment\n"
        )

        result = _parse_env_file(env_file, "ANTHROPIC_API_KEY")
        assert result == "real-key"

    def test_handles_multiple_keys(self, tmp_path):
        """Should correctly find specific key among multiple."""
        from agent_platform.llm.factory import _parse_env_file

        env_file = tmp_path / ".env.local"
        env_file.write_text(
            "ANTHROPIC_API_KEY=the-key\n"
            "ANTHROPIC_BASE_URL=https://example.com\n"
            "OTHER_KEY=other-value\n"
        )

        key = _parse_env_file(env_file, "ANTHROPIC_API_KEY")
        url = _parse_env_file(env_file, "ANTHROPIC_BASE_URL")

        assert key == "the-key"
        assert url == "https://example.com"


class TestParseJsonConfig:
    """Tests for _parse_json_config function."""

    def test_parses_uppercase_key(self, tmp_path):
        """Should find uppercase key."""
        from agent_platform.llm.factory import _parse_json_config

        json_file = tmp_path / "config.json"
        json_file.write_text(json.dumps({
            "ANTHROPIC_API_KEY": "uppercase-key"
        }))

        result = _parse_json_config(json_file, "ANTHROPIC_API_KEY")
        assert result == "uppercase-key"

    def test_parses_lowercase_key(self, tmp_path):
        """Should fallback to lowercase key."""
        from agent_platform.llm.factory import _parse_json_config

        json_file = tmp_path / "config.json"
        json_file.write_text(json.dumps({
            "anthropic_api_key": "lowercase-key"
        }))

        result = _parse_json_config(json_file, "ANTHROPIC_API_KEY")
        assert result == "lowercase-key"

    def test_prefers_uppercase_over_lowercase(self, tmp_path):
        """Should prefer uppercase when both exist."""
        from agent_platform.llm.factory import _parse_json_config

        json_file = tmp_path / "config.json"
        json_file.write_text(json.dumps({
            "ANTHROPIC_API_KEY": "uppercase-wins",
            "anthropic_api_key": "lowercase-loses"
        }))

        result = _parse_json_config(json_file, "ANTHROPIC_API_KEY")
        assert result == "uppercase-wins"

    def test_handles_base_url_key(self, tmp_path):
        """Should correctly parse ANTHROPIC_BASE_URL."""
        from agent_platform.llm.factory import _parse_json_config

        json_file = tmp_path / "config.json"
        json_file.write_text(json.dumps({
            "ANTHROPIC_API_KEY": "the-key",
            "ANTHROPIC_BASE_URL": "https://proxy.example.com"
        }))

        key = _parse_json_config(json_file, "ANTHROPIC_API_KEY")
        url = _parse_json_config(json_file, "ANTHROPIC_BASE_URL")

        assert key == "the-key"
        assert url == "https://proxy.example.com"


class TestGetLlmClientIntegration:
    """Integration tests for get_llm_client with base_url support."""

    def test_injects_base_url_from_env_local(self, monkeypatch, tmp_path):
        """Should inject base_url from .env.local into os.environ."""
        from agent_platform.llm import factory
        factory.reset_client()

        # Clear both env vars
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)

        # Create .env.local with both key and URL
        env_local = tmp_path / ".env.local"
        env_local.write_text(
            'ANTHROPIC_API_KEY="test-key-12345"\n'
            'ANTHROPIC_BASE_URL="https://deeprouter.example.com"\n'
        )

        mock_anthropic_client = MagicMock()
        mock_anthropic_class = MagicMock(return_value=mock_anthropic_client)
        mock_anthropic_module = MagicMock()
        mock_anthropic_module.Anthropic = mock_anthropic_class

        import sys
        with patch.object(factory, "_REPO_ROOT", tmp_path), \
             patch.dict(sys.modules, {"anthropic": mock_anthropic_module}):
            factory.get_llm_client()

        # Verify base_url was injected
        assert os.environ.get("ANTHROPIC_BASE_URL") == "https://deeprouter.example.com"

        # Verify Anthropic client was called with base_url
        mock_anthropic_class.assert_called_once()
        call_kwargs = mock_anthropic_class.call_args[1]
        assert call_kwargs.get("base_url") == "https://deeprouter.example.com"

    def test_env_base_url_not_overridden(self, monkeypatch, tmp_path):
        """Env ANTHROPIC_BASE_URL should NOT be overridden by local files."""
        from agent_platform.llm import factory
        factory.reset_client()

        # Set env vars
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://env-url.com")

        # Create .env.local with different URL
        env_local = tmp_path / ".env.local"
        env_local.write_text('ANTHROPIC_BASE_URL="https://should-not-use.com"\n')

        mock_anthropic_client = MagicMock()
        mock_anthropic_class = MagicMock(return_value=mock_anthropic_client)
        mock_anthropic_module = MagicMock()
        mock_anthropic_module.Anthropic = mock_anthropic_class

        import sys
        with patch.object(factory, "_REPO_ROOT", tmp_path), \
             patch.dict(sys.modules, {"anthropic": mock_anthropic_module}):
            factory.get_llm_client()

        # Verify env URL was NOT overridden
        assert os.environ.get("ANTHROPIC_BASE_URL") == "https://env-url.com"

        # Verify Anthropic client was called with env URL
        call_kwargs = mock_anthropic_class.call_args[1]
        assert call_kwargs.get("base_url") == "https://env-url.com"

    def test_uses_official_endpoint_when_no_base_url(self, monkeypatch, tmp_path):
        """Should use official endpoint when no base_url configured."""
        from agent_platform.llm import factory
        factory.reset_client()

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)

        mock_anthropic_client = MagicMock()
        mock_anthropic_class = MagicMock(return_value=mock_anthropic_client)
        mock_anthropic_module = MagicMock()
        mock_anthropic_module.Anthropic = mock_anthropic_class

        import sys
        with patch.object(factory, "_REPO_ROOT", tmp_path), \
             patch.dict(sys.modules, {"anthropic": mock_anthropic_module}):
            factory.get_llm_client()

        # Verify Anthropic client was called WITHOUT base_url
        call_kwargs = mock_anthropic_class.call_args[1]
        assert "base_url" not in call_kwargs


class TestResetClient:
    """Tests for reset_client function."""

    def test_reset_clears_singleton(self, monkeypatch):
        """reset_client should clear the cached client and backend type."""
        from agent_platform.llm import factory

        factory.reset_client()

        # Verify state is cleared
        assert factory._client is None
        assert factory._backend_type is None


class TestGetBackendType:
    """Tests for get_backend_type function."""

    def test_returns_none_before_init(self):
        """Should return None before client is initialized."""
        from agent_platform.llm import factory
        factory.reset_client()

        assert factory.get_backend_type() is None

    def test_returns_anthropic_api(self, monkeypatch, tmp_path):
        """Should return 'anthropic_api' when using Anthropic."""
        from agent_platform.llm import factory
        factory.reset_client()

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        mock_anthropic_client = MagicMock()
        mock_anthropic_class = MagicMock(return_value=mock_anthropic_client)
        mock_anthropic_module = MagicMock()
        mock_anthropic_module.Anthropic = mock_anthropic_class

        import sys
        with patch.object(factory, "_REPO_ROOT", tmp_path), \
             patch.dict(sys.modules, {"anthropic": mock_anthropic_module}):
            factory.get_llm_client()

        assert factory.get_backend_type() == "anthropic_api"

    def test_returns_deeprouter(self, monkeypatch):
        """Should return 'deeprouter' when using DeepRouter backend."""
        from agent_platform.llm import factory
        factory.reset_client()

        monkeypatch.setenv("LLM_BACKEND", "deeprouter")
        monkeypatch.setenv("DEEPROUTER_CLAUDE_TOKEN", "test-deeprouter-token")

        # Mock DeepRouterLLMClient to avoid actual HTTP calls
        with patch("agent_platform.llm.factory.DeepRouterLLMClient") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            factory.get_llm_client()

            assert factory.get_backend_type() == "deeprouter"
            mock_client_class.assert_called_once()

    def test_deeprouter_backend_priority_with_anthropic_key(self, monkeypatch, tmp_path):
        """
        When LLM_BACKEND=deeprouter but ANTHROPIC_API_KEY+ANTHROPIC_BASE_URL exist,
        should use Anthropic API format (recommended) instead of DeepRouterLLMClient.
        """
        from agent_platform.llm import factory
        factory.reset_client()

        # Set DeepRouter backend explicitly, but also provide ANTHROPIC_API_KEY + base_url
        monkeypatch.setenv("LLM_BACKEND", "deeprouter")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-deeprouter-token")
        monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://deeprouter.top")

        # Mock Anthropic SDK
        mock_anthropic_client = MagicMock()
        mock_anthropic_class = MagicMock(return_value=mock_anthropic_client)
        mock_anthropic_module = MagicMock()
        mock_anthropic_module.Anthropic = mock_anthropic_class

        with patch.object(factory, "_REPO_ROOT", tmp_path), \
             patch.dict(sys.modules, {"anthropic": mock_anthropic_module}):
            client = factory.get_llm_client()

            # Should use anthropic_api backend (via DeepRouter proxy), not deeprouter
            assert factory.get_backend_type() == "anthropic_api"
            assert client.__class__.__name__ == "AnthropicLLMClient"
            mock_anthropic_class.assert_called_once()

    def test_deeprouter_backend_without_anthropic_key(self, monkeypatch):
        """
        When LLM_BACKEND=deeprouter but no ANTHROPIC_API_KEY,
        should use DeepRouterLLMClient directly.
        """
        from agent_platform.llm import factory
        factory.reset_client()

        monkeypatch.setenv("LLM_BACKEND", "deeprouter")
        monkeypatch.setenv("DEEPROUTER_CLAUDE_TOKEN", "test-token")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with patch("agent_platform.llm.factory.DeepRouterLLMClient") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            client = factory.get_llm_client()

            assert factory.get_backend_type() == "deeprouter"
            assert client == mock_client_instance
            mock_client_class.assert_called_once()