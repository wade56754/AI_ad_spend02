"""
Tests for Agent factory functions (agents_config.py)

LEGACY WARNING: 这些测试已迁移到 agents/tests/test_factory.py
保留此文件仅作历史记录，日常测试请运行 agents/tests。

# Fix: F-P1-01 - 补充最小必要测试

Tests cover:
- create_agent() returns valid instances for all agent types
- list_agents() returns complete registry
- Agent instances have required handle_request method
"""
import pytest

from agents import create_agent, list_agents
from agents.tools.llm_client import get_llm_client
from agents.tools.types import AgentResponse, SkillResult

# 标记整个模块为 legacy（跳过）
pytestmark = pytest.mark.skip(reason="Migrated to agents/tests/test_factory.py")

class TestCreateAgent:
    """Tests for create_agent factory function."""

    def test_create_fe_agent(self):
        """create_agent('fe') should return FEAgent instance."""
        agent = create_agent("fe")
        assert agent is not None
        assert hasattr(agent, "handle_request")
        assert callable(agent.handle_request)

    def test_create_be_agent(self):
        """create_agent('be') should return BEAgent instance."""
        agent = create_agent("be")
        assert agent is not None
        assert hasattr(agent, "handle_request")

    def test_create_test_agent(self):
        """create_agent('test') should return TestAgent instance."""
        agent = create_agent("test")
        assert agent is not None
        assert hasattr(agent, "handle_request")

    def test_create_orch_agent(self):
        """create_agent('orch') should return OrchestratorAgent instance."""
        agent = create_agent("orch")
        assert agent is not None
        assert hasattr(agent, "handle_request")

    def test_create_doc_agent(self):
        """create_agent('doc') should return DocAgent instance."""
        agent = create_agent("doc")
        assert agent is not None
        assert hasattr(agent, "handle_request")

    def test_create_review_agent(self):
        """create_agent('review') should return CodeReviewAgent instance."""
        agent = create_agent("review")
        assert agent is not None
        assert hasattr(agent, "handle_request")

    def test_create_agent_case_insensitive(self):
        """create_agent should be case-insensitive."""
        agent1 = create_agent("FE")
        agent2 = create_agent("fe")
        agent3 = create_agent("Fe")
        assert all(hasattr(a, "handle_request") for a in [agent1, agent2, agent3])

    def test_create_agent_invalid_raises(self):
        """create_agent with invalid name should raise KeyError."""
        with pytest.raises(KeyError, match="Unknown agent"):
            create_agent("invalid_agent")

    def test_create_agent_with_custom_base_path(self, tmp_path):
        """create_agent should accept custom base_path."""
        agent = create_agent("fe", base_path=tmp_path)
        assert agent is not None
        assert agent.base_path == tmp_path


class TestListAgents:
    """Tests for list_agents function."""

    def test_list_agents_returns_dict(self):
        """list_agents should return a dictionary."""
        agents = list_agents()
        assert isinstance(agents, dict)

    def test_list_agents_contains_core_agents(self):
        """list_agents should contain all core agents."""
        agents = list_agents()
        core_agents = ["fe", "be", "test", "orch", "doc", "review"]
        for agent_key in core_agents:
            assert agent_key in agents, f"Missing agent: {agent_key}"

    def test_list_agents_info_structure(self):
        """Each agent info should have key, name, description."""
        agents = list_agents()
        for key, info in agents.items():
            assert "key" in info
            assert "name" in info
            assert "description" in info
            assert info["key"] == key


class TestAgentIntegration:
    """Integration tests for agent creation and basic usage."""

    def test_all_agents_can_be_created(self):
        """All registered agents should be creatable."""
        agents = list_agents()
        for key in agents.keys():
            agent = create_agent(key)
            assert agent is not None
            assert hasattr(agent, "handle_request")

    def test_agent_handle_request_returns_dict(self):
        """Agent handle_request should return a dict with success field."""
        # Test with a simple request that won't trigger LLM
        agent = create_agent("orch")
        result = agent.handle_request({})  # Missing flow -> error response
        assert isinstance(result, dict)
        assert "success" in result
        assert result["success"] is False  # Should fail gracefully

    def test_doc_agent_basic_request(self):
        """DocAgent should handle basic request without LLM."""
        agent = create_agent("doc")
        result = agent.handle_request({
            "action": "review",
            "doc_type": "module",
            "target": None,
        })
        assert isinstance(result, dict)
        assert "success" in result
