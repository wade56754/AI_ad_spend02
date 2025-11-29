"""Unit tests for be_dev_skill."""

import pytest
from agents.skills.be_dev_skill import be_dev_skill


def test_be_dev_skill_missing_task():
    """Test that be_dev_skill returns error when task is missing."""
    result = be_dev_skill("", ["file.py"])

    assert result["success"] is False
    assert result["error"] is not None
    assert "task" in result["error"].lower()


def test_be_dev_skill_invalid_target_files_not_list():
    """Test that be_dev_skill returns error when target_files is not a list."""
    result = be_dev_skill("task", "not_a_list")

    assert result["success"] is False
    assert result["error"] is not None


def test_be_dev_skill_empty_target_files():
    """Test that be_dev_skill returns error when target_files is empty."""
    result = be_dev_skill("task", [])

    assert result["success"] is False
    assert result["error"] is not None
    assert "target_files" in result["error"].lower()


def test_be_dev_skill_success_path(monkeypatch):
    """Test be_dev_skill success path with mocked Anthropic client."""
    class MockMessage:
        def __init__(self):
            self.content = [
                type('obj', (object,), {
                    'text': '{"changes": [{"file": "router.py", "content": "mock code"}], "notes": ["backend note"]}'
                })
            ]

    class MockClient:
        class messages:
            @staticmethod
            def create(**kwargs):
                return MockMessage()

    def mock_get_client():
        return MockClient()

    import agents.skills.be_dev_skill as be_module
    monkeypatch.setattr(be_module, "_get_client", mock_get_client)

    result = be_dev_skill("Implement API endpoint", ["routers/api.py"])

    assert result["success"] is True
    assert "changes" in result["data"]
    assert "router.py" in result["data"]["changes"]
    assert result["data"]["changes"]["router.py"] == "mock code"
    assert "notes" in result["data"]
