"""
Tests for SupabaseTool (P1-06 fix: unified response structure)

Validates that SupabaseTool methods return SkillResult structure.
"""

import pytest
from agents.tools.supabase_tool import SupabaseTool, SupabaseNotConfiguredError
from agents.tools.types import SkillResult


class TestSupabaseToolStructure:
    """Tests for SupabaseTool response structure compliance."""

    def test_execute_sql_returns_skill_result(self):
        """execute_sql should return SkillResult structure."""
        tool = SupabaseTool(project_id="test_project_123")
        result = tool.execute_sql("SELECT 1")

        # Should be a dict with SkillResult keys
        assert isinstance(result, dict)
        assert "success" in result
        assert "data" in result
        assert "error" in result
        assert "raw" in result

    def test_apply_migration_returns_skill_result(self):
        """apply_migration should return SkillResult structure."""
        tool = SupabaseTool(project_id="test_project_123")
        result = tool.apply_migration("migration_001", "CREATE TABLE test;")

        assert isinstance(result, dict)
        assert "success" in result
        assert "data" in result
        assert "error" in result
        assert "raw" in result

    def test_list_tables_returns_skill_result(self):
        """list_tables should return SkillResult structure."""
        tool = SupabaseTool(project_id="test_project_123")
        result = tool.list_tables()

        assert isinstance(result, dict)
        assert "success" in result
        assert "data" in result
        assert "error" in result
        assert "raw" in result


class TestSupabaseToolNotConfigured:
    """Tests for SupabaseTool behavior when MCP is not configured."""

    def test_execute_sql_not_configured_returns_error(self):
        """execute_sql should return error when MCP not configured."""
        # Ensure MCP is not configured
        SupabaseTool.set_configured(False)

        tool = SupabaseTool(project_id="test_project")
        result = tool.execute_sql("SELECT 1")

        assert result["success"] is False
        assert result["error"] is not None
        assert "未配置" in result["error"]
        assert result["data"] is None

    def test_apply_migration_not_configured_returns_error(self):
        """apply_migration should return error when MCP not configured."""
        SupabaseTool.set_configured(False)

        tool = SupabaseTool(project_id="test_project")
        result = tool.apply_migration("test_migration", "SQL")

        assert result["success"] is False
        assert result["error"] is not None
        assert result["data"] is None

    def test_list_tables_not_configured_returns_error(self):
        """list_tables should return error when MCP not configured."""
        SupabaseTool.set_configured(False)

        tool = SupabaseTool(project_id="test_project")
        result = tool.list_tables()

        assert result["success"] is False
        assert result["error"] is not None
        assert result["data"] is None

    def test_raw_field_contains_debug_info(self):
        """raw field should contain debug information."""
        SupabaseTool.set_configured(False)

        tool = SupabaseTool(project_id="test_project")
        result = tool.execute_sql("SELECT * FROM users LIMIT 10")

        assert "raw" in result
        assert "query_preview" in result["raw"]


class TestSupabaseToolProjectId:
    """Tests for project_id handling."""

    def test_missing_project_id_raises_error(self):
        """Methods should raise error when project_id is missing."""
        tool = SupabaseTool()  # No project_id

        with pytest.raises(RuntimeError, match="project_id 未配置"):
            tool.execute_sql("SELECT 1")

    def test_project_id_from_init(self):
        """project_id from init should be used."""
        SupabaseTool.set_configured(False)

        tool = SupabaseTool(project_id="init_project")
        result = tool.execute_sql("SELECT 1")

        # Should not raise, error should be about MCP not configured
        assert result["success"] is False
        assert "未配置" in result["error"]

    def test_project_id_override(self):
        """project_id passed to method should override init."""
        SupabaseTool.set_configured(False)

        tool = SupabaseTool(project_id="init_project")
        result = tool.execute_sql("SELECT 1", project_id="override_project")

        # Should not raise
        assert result["success"] is False


class TestSupabaseToolConfigurationState:
    """Tests for configuration state management."""

    def test_is_configured_default_false(self):
        """is_configured should return False by default."""
        SupabaseTool.set_configured(False)  # Reset
        assert SupabaseTool.is_configured() is False

    def test_set_configured_changes_state(self):
        """set_configured should change configuration state."""
        SupabaseTool.set_configured(True)
        assert SupabaseTool.is_configured() is True

        SupabaseTool.set_configured(False)
        assert SupabaseTool.is_configured() is False

    def test_get_status_reflects_configuration(self):
        """get_status should reflect current configuration."""
        SupabaseTool.set_configured(False)
        tool = SupabaseTool(project_id="test_project")

        status = tool.get_status()
        assert status["configured"] is False
        assert "未配置" in status["message"]

        SupabaseTool.set_configured(True)
        status = tool.get_status()
        assert status["configured"] is True
        assert "已配置" in status["message"]

        # Reset for other tests
        SupabaseTool.set_configured(False)
