"""
Tests for agents/agents_config.py

验证 Agent 工厂函数和注册表正确工作。
使用绝对导入，不与业务代码冲突。
"""

import pytest
from agents.agents_config import create_agent, list_agents


class TestListAgents:
    """Tests for list_agents function."""

    def test_list_agents_contains_core_agents(self):
        """list_agents should return all core agents."""
        agents = list_agents()
        assert "fe" in agents
        assert "be" in agents
        assert "test" in agents
        assert "orch" in agents

    def test_list_agents_info_structure(self):
        """Each agent info should have key, name, description."""
        agents = list_agents()
        for key, info in agents.items():
            assert "key" in info
            assert "name" in info
            assert "description" in info
            assert info["key"] == key


class TestCreateAgent:
    """Tests for create_agent factory function."""

    def test_create_fe_agent_has_handle_request(self):
        """FEAgent should have handle_request method."""
        fe_agent = create_agent("fe")
        assert hasattr(fe_agent, "handle_request")
        assert callable(fe_agent.handle_request)

    def test_create_be_agent_has_handle_request(self):
        """BEAgent should have handle_request method."""
        be_agent = create_agent("be")
        assert hasattr(be_agent, "handle_request")
        assert callable(be_agent.handle_request)

    def test_create_test_agent_has_handle_request(self):
        """TestAgent should have handle_request method."""
        test_agent = create_agent("test")
        assert hasattr(test_agent, "handle_request")
        assert callable(test_agent.handle_request)

    def test_create_orch_agent_has_handle_request(self):
        """OrchestratorAgent should have handle_request method."""
        orch_agent = create_agent("orch")
        assert hasattr(orch_agent, "handle_request")
        assert callable(orch_agent.handle_request)

    def test_create_agent_case_insensitive(self):
        """create_agent should be case-insensitive."""
        agent1 = create_agent("FE")
        agent2 = create_agent("fe")
        agent3 = create_agent("Fe")
        assert all(hasattr(a, "handle_request") for a in [agent1, agent2, agent3])

    def test_create_agent_invalid_name_raises(self):
        """create_agent should raise KeyError for invalid agent name."""
        with pytest.raises(KeyError, match="Unknown agent"):
            create_agent("invalid_agent_name")
        with pytest.raises(KeyError, match="Unknown agent"):
            create_agent("nonexistent")
