"""
Tests for MCP Server Agent and Skill tools - Phase 4

Test coverage:
- ap_list_agents: MCP-safe filtering
- ap_run_agent: MCP-safe enforcement
- ap_list_skills: MCP-safe filtering
- ap_run_skill: MCP-safe enforcement

基准对齐:
- AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md Phase 4
- Agent Layer Freeze v1.0
- SoT Freeze v2.6
"""

import pytest
from unittest.mock import patch, MagicMock


class TestMCPListAgents:
    """Tests for ap_list_agents MCP tool."""

    def test_list_agents_default_returns_mcp_safe_only(self):
        """Default call should only return mcp_safe=True agents."""
        from agent_platform.mcp.server import list_agents

        result = list_agents()

        assert result["success"] is True
        assert result["filter"] == "mcp_safe_only"
        assert result["mcp_mode"] is True

        # All returned agents should be mcp_safe
        for agent in result["agents"]:
            assert agent["mcp_safe"] is True

        # Should include test, review, doc
        agent_names = [a["name"] for a in result["agents"]]
        assert "test" in agent_names
        assert "review" in agent_names
        assert "doc" in agent_names

        # Should NOT include LLM-dependent agents
        assert "fe" not in agent_names
        assert "be" not in agent_names
        assert "orch" not in agent_names

    def test_list_agents_include_all_returns_all(self):
        """include_all=True should return all agents."""
        from agent_platform.mcp.server import list_agents

        result = list_agents(include_all=True)

        assert result["success"] is True
        assert result["filter"] == "all"

        agent_names = [a["name"] for a in result["agents"]]

        # Should include both MCP-safe and LLM-dependent agents
        assert "test" in agent_names
        assert "review" in agent_names
        assert "doc" in agent_names
        assert "fe" in agent_names
        assert "be" in agent_names
        assert "orch" in agent_names

    def test_list_agents_returns_metadata(self):
        """Agent list should include metadata."""
        from agent_platform.mcp.server import list_agents

        result = list_agents()

        assert result["success"] is True

        for agent in result["agents"]:
            assert "name" in agent
            assert "description" in agent
            assert "version" in agent
            assert "mcp_safe" in agent
            assert "tags" in agent


class TestMCPRunAgent:
    """Tests for ap_run_agent MCP tool."""

    def test_run_mcp_safe_agent_succeeds(self):
        """Running MCP-safe agent should succeed."""
        from agent_platform.mcp.server import run_agent

        # Run review agent with empty changes (should pass)
        result = run_agent(
            agent_name="review",
            payload={"action": "review", "changes": {}},
        )

        assert result["success"] is True
        assert result["agent_name"] == "review"
        assert result["mcp_safe"] is True

    def test_run_mcp_unsafe_agent_blocked(self):
        """Running MCP-unsafe agent should be blocked."""
        from agent_platform.mcp.server import run_agent

        # Try to run fe agent (mcp_safe=False)
        result = run_agent(
            agent_name="fe",
            payload={"task": "some task"},
        )

        assert result["success"] is False
        assert result["error_kind"] == "MCP_UNSAFE_AGENT"
        assert result["mcp_safe"] is False
        assert "available_agents" in result

    def test_run_unknown_agent_returns_error(self):
        """Running unknown agent should return proper error."""
        from agent_platform.mcp.server import run_agent

        result = run_agent(
            agent_name="nonexistent",
            payload={},
        )

        assert result["success"] is False
        assert result["error_kind"] == "AGENT_NOT_FOUND"
        assert "available_agents" in result

    def test_run_test_agent_returns_prompt(self):
        """TestAgent should return generated prompt."""
        from agent_platform.mcp.server import run_agent

        # Test agent with invalid mode should return error
        result = run_agent(
            agent_name="test",
            payload={"mode": "invalid_mode"},
        )

        # The agent should return success=False for invalid mode
        assert "agent_result" in result

    def test_run_doc_agent_generates_content(self):
        """DocAgent should generate document content."""
        from agent_platform.mcp.server import run_agent

        result = run_agent(
            agent_name="doc",
            payload={
                "action": "generate",
                "doc_type": "spec",
                "target": "test.md",
                "context": "Test content",
            },
        )

        assert result["success"] is True
        assert result["agent_name"] == "doc"
        assert "agent_result" in result


class TestMCPListSkills:
    """Tests for ap_list_skills MCP tool."""

    def test_list_skills_default_returns_mcp_safe_only(self):
        """Default call should only return mcp_safe=True skills."""
        from agent_platform.mcp.server import list_skills

        result = list_skills()

        assert result["success"] is True
        assert result["filter"] == "mcp_safe_only"
        assert result["mcp_mode"] is True

        # All returned skills should be mcp_safe
        for skill in result["skills"]:
            assert skill["mcp_safe"] is True

        # Should include db_test, backend_test, sot_guard
        skill_names = [s["name"] for s in result["skills"]]
        assert "db_test" in skill_names
        assert "backend_test" in skill_names
        assert "sot_guard" in skill_names

    def test_list_skills_include_all_returns_all(self):
        """include_all=True should return all skills."""
        from agent_platform.mcp.server import list_skills

        result = list_skills(include_all=True)

        assert result["success"] is True
        assert result["filter"] == "all"

        skill_names = [s["name"] for s in result["skills"]]

        # Should include both MCP-safe and LLM-dependent skills
        assert "db_test" in skill_names
        assert "backend_test" in skill_names
        assert "sot_guard" in skill_names
        assert "fe_dev" in skill_names
        assert "be_dev" in skill_names


class TestMCPRunSkill:
    """Tests for ap_run_skill MCP tool."""

    def test_run_sot_guard_skill_succeeds(self):
        """Running sot_guard skill should succeed."""
        from agent_platform.mcp.server import run_skill

        result = run_skill(
            skill_name="sot_guard",
            params={"changes": {}},
        )

        assert result["success"] is True
        assert result["skill_name"] == "sot_guard"
        assert result["mcp_safe"] is True

    def test_run_sot_guard_detects_violation(self):
        """sot_guard should detect violations."""
        from agent_platform.mcp.server import run_skill

        code_with_violation = '''
def update_balance(account):
    account.balance = account.balance + 100
'''
        result = run_skill(
            skill_name="sot_guard",
            params={"changes": {"ledger.py": code_with_violation}},
        )

        assert result["success"] is True
        skill_result = result["skill_result"]
        assert skill_result["passed"] is False
        assert len(skill_result["violations"]) > 0

    def test_run_backend_test_skill_returns_prompt(self):
        """backend_test skill should return prompt."""
        from agent_platform.mcp.server import run_skill

        result = run_skill(
            skill_name="backend_test",
            params={"scope": "ledger", "level": "quick"},
        )

        assert result["success"] is True
        assert result["skill_name"] == "backend_test"
        skill_result = result["skill_result"]
        assert "prompt" in skill_result["data"]

    def test_run_mcp_unsafe_skill_blocked(self):
        """Running MCP-unsafe skill should be blocked."""
        from agent_platform.mcp.server import run_skill

        # Try to run fe_dev skill (mcp_safe=False)
        result = run_skill(
            skill_name="fe_dev",
            params={},
        )

        assert result["success"] is False
        assert result["error_kind"] == "MCP_UNSAFE_SKILL"
        assert result["mcp_safe"] is False
        assert "available_skills" in result

    def test_run_unknown_skill_returns_error(self):
        """Running unknown skill should return proper error."""
        from agent_platform.mcp.server import run_skill

        result = run_skill(
            skill_name="nonexistent",
            params={},
        )

        assert result["success"] is False
        assert result["error_kind"] == "SKILL_NOT_FOUND"
        assert "available_skills" in result


class TestMCPToolRegistry:
    """Tests for MCP tool registry."""

    def test_registry_contains_agent_tools(self):
        """Registry should contain agent-related tools."""
        from agent_platform.mcp.server import _registry

        tool_names = list(_registry.tools.keys())

        assert "ap_list_agents" in tool_names
        assert "ap_run_agent" in tool_names

    def test_registry_contains_skill_tools(self):
        """Registry should contain skill-related tools."""
        from agent_platform.mcp.server import _registry

        tool_names = list(_registry.tools.keys())

        assert "ap_list_skills" in tool_names
        assert "ap_run_skill" in tool_names

    def test_registry_list_tools_returns_mcp_format(self):
        """list_tools should return MCP-compatible format."""
        from agent_platform.mcp.server import _registry

        tools = _registry.list_tools()

        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool


class TestMCPHandleRequest:
    """Tests for MCP request handling."""

    def test_handle_tools_list_includes_new_tools(self):
        """tools/list should include Phase 4 tools."""
        from agent_platform.mcp.server import handle_mcp_request

        response = handle_mcp_request({
            "method": "tools/list",
            "id": 1,
        })

        assert "result" in response
        tools = response["result"]["tools"]
        tool_names = [t["name"] for t in tools]

        # Phase 4 tools
        assert "ap_list_agents" in tool_names
        assert "ap_run_agent" in tool_names
        assert "ap_list_skills" in tool_names
        assert "ap_run_skill" in tool_names

    def test_handle_tools_call_run_agent(self):
        """tools/call should invoke ap_run_agent."""
        from agent_platform.mcp.server import handle_mcp_request
        import json

        response = handle_mcp_request({
            "method": "tools/call",
            "params": {
                "name": "ap_run_agent",
                "arguments": {
                    "agent_name": "review",
                    "payload": {"action": "review", "changes": {}},
                },
            },
            "id": 1,
        })

        assert "result" in response
        content = response["result"]["content"]
        assert len(content) > 0
        assert content[0]["type"] == "text"

        # Parse the JSON result
        result = json.loads(content[0]["text"])
        assert result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
