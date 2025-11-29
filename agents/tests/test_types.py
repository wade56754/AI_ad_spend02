"""
Tests for agents/tools/types.py type definitions

Migrated from tests/agents_legacy/test_types.py
Verifies that type structures are correctly defined and importable.
"""

import pytest
from agents.tools.types import (
    AgentResponse,
    SkillResult,
    AgentResponseData,
    SotViolationDict,
    ReviewResult,
)


class TestAgentResponseType:
    """Tests for AgentResponse TypedDict."""

    def test_agent_response_success_required(self):
        """AgentResponse should require 'success' field."""
        response: AgentResponse = {"success": True}
        assert response["success"] is True

    def test_agent_response_with_data(self):
        """AgentResponse can include optional data and error."""
        response: AgentResponse = {
            "success": True,
            "data": {"changes": {"file.py": "content"}},
            "error": None,
        }
        assert response["success"] is True
        assert response["data"] is not None

    def test_agent_response_error_case(self):
        """AgentResponse error response structure."""
        response: AgentResponse = {
            "success": False,
            "data": None,
            "error": "Something went wrong",
        }
        assert response["success"] is False
        assert response["error"] == "Something went wrong"


class TestSkillResultType:
    """Tests for SkillResult TypedDict."""

    def test_skill_result_success_required(self):
        """SkillResult should require 'success' field."""
        result: SkillResult = {"success": True}
        assert result["success"] is True

    def test_skill_result_with_raw(self):
        """SkillResult can include optional raw field for debugging."""
        result: SkillResult = {
            "success": True,
            "data": {"output": "generated code"},
            "error": None,
            "raw": "Raw API response text",
        }
        assert result["raw"] == "Raw API response text"
