"""Smoke tests for agents config + FEAgent/BEAgent basic behavior."""

import pytest

from agents.agents_config import create_agent, list_agents


def test_list_agents_contains_core_agents():
    """list_agents should include fe/be/test/orch."""
    agents = list_agents()
    assert "fe" in agents
    assert "be" in agents
    assert "test" in agents
    assert "orch" in agents


def test_fe_agent_handle_request_missing_task():
    """FEAgent should return error when task is missing."""
    fe_agent = create_agent("fe")
    resp = fe_agent.handle_request({"target_files": ["dummy.tsx"]})
    assert resp["success"] is False
    assert isinstance(resp["error"], str)
    assert "task" in resp["error"].lower()


def test_be_agent_handle_request_missing_task():
    """BEAgent should return error when task is missing."""
    be_agent = create_agent("be")
    resp = be_agent.handle_request({"target_files": ["dummy.py"]})
    assert resp["success"] is False
    assert isinstance(resp["error"], str)
    assert "task" in resp["error"].lower()
