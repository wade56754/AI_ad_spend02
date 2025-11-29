"""Unit tests for TestAgent."""

import pytest
from agents.agents_config import create_agent


def test_test_agent_handle_request_success():
    """Test that TestAgent returns success with executed=False."""
    test_agent = create_agent("test")
    response = test_agent.handle_request({})

    assert response["success"] is True
    assert response["data"] is not None
    assert response["data"]["executed"] is False
    assert "not executed" in response["data"]["reason"].lower() or "requires" in response["data"]["reason"].lower()
    assert "prompt" in response["data"]
    assert isinstance(response["data"]["prompt"], str)
    assert len(response["data"]["prompt"]) > 0


def test_test_agent_without_project_id():
    """Test that TestAgent without project_id still generates prompt."""
    test_agent = create_agent("test", supabase_project_id=None)
    response = test_agent.handle_request({})

    assert response["success"] is True
    assert response["data"]["executed"] is False
