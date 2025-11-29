"""Unit tests for fe_dev_skill."""

import pytest
from agents.skills.fe_dev_skill import fe_dev_skill


def test_fe_dev_skill_missing_task():
    """Test that fe_dev_skill returns error when task is missing."""
    result = fe_dev_skill("", ["file.tsx"])

    assert result["success"] is False
    assert result["error"] is not None
    assert "task" in result["error"].lower()


def test_fe_dev_skill_invalid_target_files_not_list():
    """Test that fe_dev_skill returns error when target_files is not a list."""
    result = fe_dev_skill("task", "not_a_list")

    assert result["success"] is False
    assert result["error"] is not None


def test_fe_dev_skill_empty_target_files():
    """Test that fe_dev_skill returns error when target_files is empty."""
    result = fe_dev_skill("task", [])

    assert result["success"] is False
    assert result["error"] is not None
    assert "target_files" in result["error"].lower()


def test_fe_dev_skill_success_path(monkeypatch):
    """Test fe_dev_skill success path with mocked Anthropic client."""
    class MockMessage:
        def __init__(self):
            self.content = [
                type('obj', (object,), {
                    'text': '{"changes": [{"file": "file.tsx", "content": "mock content"}], "notes": ["test note"]}'
                })
            ]

    class MockClient:
        class messages:
            @staticmethod
            def create(**kwargs):
                return MockMessage()

    def mock_get_client():
        return MockClient()

    import agents.skills.fe_dev_skill as fe_module
    monkeypatch.setattr(fe_module, "_get_client", mock_get_client)

    result = fe_dev_skill("Create button component", ["components/Button.tsx"])

    assert result["success"] is True
    assert "changes" in result["data"]
    assert "file.tsx" in result["data"]["changes"]
    assert result["data"]["changes"]["file.tsx"] == "mock content"
    assert "notes" in result["data"]
