"""Unit tests for db_test_skill."""

import pytest
from agents.skills.db_test_skill import db_test_skill


def test_db_test_skill_generates_prompt():
    """Test that db_test_skill generates a prompt successfully."""
    result = db_test_skill()

    assert result["success"] is True
    assert "prompt" in result["data"]
    assert isinstance(result["data"]["prompt"], str)
    assert len(result["data"]["prompt"]) > 0


def test_db_test_skill_prompt_contains_role():
    """Test that generated prompt contains expected ROLE section."""
    result = db_test_skill()

    assert result["success"] is True
    assert "<ROLE>" in result["data"]["prompt"]
    assert "数据库不变量测试" in result["data"]["prompt"] or "Agent" in result["data"]["prompt"]


def test_db_test_skill_prompt_structure():
    """Test that prompt has expected structure with CONTEXT and INSTRUCTIONS."""
    result = db_test_skill()

    assert result["success"] is True
    prompt = result["data"]["prompt"]
    assert "<CONTEXT>" in prompt
    assert "<TASK>" in prompt or "步骤" in prompt or "TASK" in prompt
