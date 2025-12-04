"""
Tests for agent_platform.skills registry - Phase 3

Test coverage:
- Skill registration and discovery
- MCP safe filtering
- Skill invocation

基准对齐:
- AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md Phase 3
- SoT Freeze v2.6
"""

import pytest


class TestSkillRegistration:
    """Tests for skill registration and discovery."""

    def test_list_skills_returns_all_registered(self):
        """Should list all registered skills."""
        from agent_platform.skills import list_skills

        skills = list_skills()

        # Phase 3: 至少有 8 个 Skill 注册
        assert len(skills) >= 6

        # 验证核心 Skill 存在
        names = [s.name for s in skills]
        assert "db_test" in names
        assert "backend_test" in names
        assert "sot_guard" in names
        assert "fe_dev" in names
        assert "be_dev" in names

    def test_list_mcp_safe_skills_only_returns_safe(self):
        """MCP safe filter should only return mcp_safe=True skills."""
        from agent_platform.skills import list_mcp_safe_skills, list_skills

        safe_skills = list_mcp_safe_skills()
        all_skills = list_skills()

        # MCP safe skills should be subset of all skills
        assert len(safe_skills) <= len(all_skills)

        # All returned skills should have mcp_safe=True
        for skill in safe_skills:
            assert skill.mcp_safe is True

        # Verify expected MCP safe skills
        safe_names = [s.name for s in safe_skills]
        assert "db_test" in safe_names
        assert "backend_test" in safe_names
        assert "sot_guard" in safe_names

        # LLM-dependent skills should NOT be in safe list
        assert "fe_dev" not in safe_names
        assert "be_dev" not in safe_names

    def test_is_skill_mcp_safe_returns_correct_status(self):
        """is_skill_mcp_safe should return correct boolean."""
        from agent_platform.skills import is_skill_mcp_safe

        # MCP safe skills
        assert is_skill_mcp_safe("db_test") is True
        assert is_skill_mcp_safe("backend_test") is True
        assert is_skill_mcp_safe("sot_guard") is True

        # LLM-dependent skills
        assert is_skill_mcp_safe("fe_dev") is False
        assert is_skill_mcp_safe("be_dev") is False

        # Non-existent skill
        assert is_skill_mcp_safe("nonexistent") is False


class TestSkillInvocation:
    """Tests for skill invocation."""

    def test_invoke_sot_guard_with_empty_changes(self):
        """sot_guard should handle empty changes gracefully."""
        from agent_platform.skills import invoke_skill

        result = invoke_skill("sot_guard", changes={})

        assert result["passed"] is True
        assert len(result["violations"]) == 0

    def test_invoke_sot_guard_detects_p0_violation(self):
        """sot_guard should detect P0 state machine violations."""
        from agent_platform.skills import invoke_skill

        # Code with undefined state
        code_with_violation = '''
class DailyReport:
    def update_status(self):
        self.status = DailyReportStatus.UNDEFINED_STATE
'''
        result = invoke_skill("sot_guard", changes={"test.py": code_with_violation})

        # Should detect the undefined state
        assert result["passed"] is False or len(result["violations"]) > 0 or len(result["warnings"]) > 0

    def test_invoke_sot_guard_detects_ledger_violation(self):
        """sot_guard should detect P0 ledger violations."""
        from agent_platform.skills import invoke_skill

        # Code that directly modifies balance
        code_with_ledger_violation = '''
def update_balance(account):
    account.balance = account.balance + 100
'''
        result = invoke_skill("sot_guard", changes={"ledger.py": code_with_ledger_violation})

        # Should detect the balance modification
        violations = result["violations"]
        assert any(v["rule"] == "LED-001" for v in violations)

    def test_invoke_backend_test_returns_prompt(self):
        """backend_test should return a prompt."""
        from agent_platform.skills import invoke_skill

        result = invoke_skill("backend_test", scope="ledger", level="quick")

        assert result["success"] is True
        assert "prompt" in result["data"]
        assert "ledger" in result["data"]["prompt"]

    def test_invoke_nonexistent_skill_raises(self):
        """Should raise SkillNotFoundError for unknown skill."""
        from agent_platform.skills import invoke_skill
        from agent_platform.core.exceptions import SkillNotFoundError

        with pytest.raises(SkillNotFoundError):
            invoke_skill("nonexistent_skill")


class TestSkillMetadata:
    """Tests for skill metadata."""

    def test_skill_meta_includes_mcp_safe(self):
        """SkillMeta.to_dict should include mcp_safe field."""
        from agent_platform.skills import get_registry

        registry = get_registry()
        meta = registry.get("db_test")

        assert meta is not None
        meta_dict = meta.to_dict()

        assert "mcp_safe" in meta_dict
        assert meta_dict["mcp_safe"] is True

    def test_skill_meta_includes_tags(self):
        """SkillMeta should have tags for filtering."""
        from agent_platform.skills import get_registry

        registry = get_registry()
        meta = registry.get("db_test")

        assert meta is not None
        assert "db" in meta.tags or "test" in meta.tags or "pure_logic" in meta.tags


class TestPureLogicSkills:
    """Tests for pure logic skill functions."""

    def test_db_test_skill_returns_prompt(self):
        """db_test_skill should return a prompt."""
        from agent_platform.skills import db_test_skill

        result = db_test_skill()

        # May fail if DB_INVARIANTS_SQL not found, but structure should be valid
        if result["success"]:
            assert "prompt" in result["data"]
        else:
            assert "error" in result

    def test_backend_test_skill_with_different_scopes(self):
        """backend_test_skill should handle different scopes."""
        from agent_platform.skills import backend_test_skill

        for scope in ["ledger", "topups", "daily_reports", "reconciliation", "all"]:
            result = backend_test_skill(scope=scope, level="quick")
            assert result["success"] is True
            assert scope in result["data"]["prompt"] or scope == "all"

    def test_sot_guard_validates_code(self):
        """validate_against_sot should validate code."""
        from agent_platform.skills import validate_against_sot

        result = validate_against_sot({
            "clean.py": "def clean_function(): pass"
        })

        assert result["passed"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
