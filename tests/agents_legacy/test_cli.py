"""
Tests for agents/cli.py

验证 CLI 模块可正确导入和解析参数。
使用绝对导入，不与业务代码冲突。
"""

import pytest
from agents.agents_config import create_agent, list_agents


class TestCLIImports:
    """Test CLI module imports work correctly."""

    def test_create_agent_importable(self):
        """create_agent should be importable from agents.agents_config."""
        assert callable(create_agent)

    def test_list_agents_importable(self):
        """list_agents should be importable from agents.agents_config."""
        assert callable(list_agents)

    def test_list_agents_returns_valid_choices(self):
        """list_agents should return agent keys suitable for CLI choices."""
        agents = list_agents()
        assert isinstance(agents, dict)
        assert len(agents) >= 4  # At least fe, be, test, orch
        for key in agents.keys():
            assert isinstance(key, str)
            assert len(key) > 0


class TestCLIAgentCreation:
    """Test CLI can create agents via factory."""

    def test_create_agent_from_cli_key(self):
        """CLI should be able to create agent using key from list_agents."""
        for key in list_agents().keys():
            agent = create_agent(key)
            assert agent is not None
            assert hasattr(agent, "handle_request")

