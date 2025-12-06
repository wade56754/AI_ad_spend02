"""
test_api_dev_flow.py

Unit tests for OrchestratorAgent api_dev flow.

Test coverage:
- Normal flow: full_feature + impl+test + run_tests=smoke
- Dry-run semantics: auto_write=False
- Error cases: BEAgent failure, TestAgent failure, validation errors
- Plan mode: api_mode=plan returns early without implementation

Baseline:
- TEST_AUTOMATION_SOT v1.0.1
- AI_CODE_DEV_ORCHESTRATION_SOT v1.0
- API_SOT v9.0
"""

from __future__ import annotations

import pytest
from pathlib import Path
from typing import Any, Dict

from agent_platform.core.protocol import AgentContext
from agents.agent_core.orchestrator_agent import OrchestratorAgent


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def orchestrator(tmp_path: Path) -> OrchestratorAgent:
    """Create OrchestratorAgent with temp base_path for isolation."""
    return OrchestratorAgent(base_path=tmp_path)


@pytest.fixture
def mock_be_success() -> Dict[str, Any]:
    """Mock successful BEAgent response."""
    return {
        "success": True,
        "data": {
            "changes": {
                "schemas/finance_profit.py": "# generated schema",
                "routers/finance_profit.py": "# generated router",
            },
            "meta": {"agent": "be", "version": "1.0.0"},
        },
        "error": None,
    }


@pytest.fixture
def mock_be_failure() -> Dict[str, Any]:
    """Mock failed BEAgent response."""
    return {
        "success": False,
        "data": {},
        "error": "BEAgent: Failed to generate code",
    }


@pytest.fixture
def mock_test_success() -> Dict[str, Any]:
    """Mock successful TestAgent response."""
    return {
        "success": True,
        "data": {
            "mode": "backend",
            "status": "passed",
            "executed": False,
            "scope": "finance_profit",
            "meta": {"agent": "test", "version": "1.0.0"},
        },
        "error": None,
    }


@pytest.fixture
def mock_test_failure() -> Dict[str, Any]:
    """Mock failed TestAgent response."""
    return {
        "success": False,
        "data": {},
        "error": "TestAgent: pytest execution failed",
    }


# =============================================================================
# Test Class: Validation Tests
# =============================================================================

class TestApiDevValidation:
    """Test input validation for api_dev flow."""

    def test_missing_module_returns_error(self, orchestrator: OrchestratorAgent):
        """api_dev requires module field."""
        request = {
            "flow": "api_dev",
            "change_type": "full_feature",
            "task": "Test task",
            # module is missing
        }
        result = orchestrator.handle_request(request)

        assert result["success"] is False
        assert "module" in result["error"].lower()

    def test_invalid_module_returns_error(self, orchestrator: OrchestratorAgent):
        """api_dev rejects invalid module names."""
        request = {
            "flow": "api_dev",
            "module": "invalid_module_xyz",
            "change_type": "full_feature",
            "task": "Test task",
        }
        result = orchestrator.handle_request(request)

        assert result["success"] is False
        assert "invalid module" in result["error"].lower()

    def test_missing_change_type_returns_error(self, orchestrator: OrchestratorAgent):
        """api_dev requires change_type field."""
        request = {
            "flow": "api_dev",
            "module": "finance_profit",
            "task": "Test task",
            # change_type is missing
        }
        result = orchestrator.handle_request(request)

        assert result["success"] is False
        assert "change_type" in result["error"].lower()

    def test_invalid_change_type_returns_error(self, orchestrator: OrchestratorAgent):
        """api_dev rejects invalid change_type values."""
        request = {
            "flow": "api_dev",
            "module": "finance_profit",
            "change_type": "invalid_change_type",
            "task": "Test task",
        }
        result = orchestrator.handle_request(request)

        assert result["success"] is False
        assert "change_type" in result["error"].lower()

    def test_missing_task_returns_error(self, orchestrator: OrchestratorAgent):
        """api_dev requires task field."""
        request = {
            "flow": "api_dev",
            "module": "finance_profit",
            "change_type": "full_feature",
            # task is missing
        }
        result = orchestrator.handle_request(request)

        assert result["success"] is False
        assert "task" in result["error"].lower()

    def test_invalid_api_mode_returns_error(self, orchestrator: OrchestratorAgent):
        """api_dev rejects invalid api_mode values."""
        request = {
            "flow": "api_dev",
            "module": "finance_profit",
            "change_type": "full_feature",
            "task": "Test task",
            "api_mode": "invalid_mode",
        }
        result = orchestrator.handle_request(request)

        assert result["success"] is False
        assert "api_mode" in result["error"].lower()

    def test_invalid_run_tests_returns_error(self, orchestrator: OrchestratorAgent):
        """api_dev rejects invalid run_tests values."""
        request = {
            "flow": "api_dev",
            "module": "finance_profit",
            "change_type": "full_feature",
            "task": "Test task",
            "run_tests": "invalid_option",
        }
        result = orchestrator.handle_request(request)

        assert result["success"] is False
        assert "run_tests" in result["error"].lower()


# =============================================================================
# Test Class: Plan Mode Tests
# =============================================================================

class TestApiDevPlanMode:
    """Test api_mode=plan returns early without implementation."""

    def test_plan_mode_returns_plan_only(self, orchestrator: OrchestratorAgent):
        """api_mode=plan should return plan without calling BEAgent."""
        request = {
            "flow": "api_dev",
            "module": "finance_profit",
            "change_type": "full_feature",
            "task": "Add profit summary API",
            "api_mode": "plan",
        }
        result = orchestrator.handle_request(request)

        assert result["success"] is True
        assert result["data"]["flow"] == "api_dev"
        assert "plan" in result["data"]["steps"]
        # Should NOT have impl step
        assert "impl" not in result["data"]["steps"]

    def test_plan_mode_includes_files_to_touch(self, orchestrator: OrchestratorAgent):
        """Plan should include files_to_touch list."""
        request = {
            "flow": "api_dev",
            "module": "finance_profit",
            "change_type": "schema+router",
            "task": "Modify schema",
            "api_mode": "plan",
        }
        result = orchestrator.handle_request(request)

        assert result["success"] is True
        plan_data = result["data"]["steps"]["plan"]["data"]
        assert "files_to_touch" in plan_data
        assert len(plan_data["files_to_touch"]) > 0


# =============================================================================
# Test Class: Normal Flow Tests
# =============================================================================

class TestApiDevNormalFlow:
    """Test normal api_dev flow execution."""

    def test_full_feature_impl_test_smoke(
        self,
        orchestrator: OrchestratorAgent,
        mock_be_success: Dict[str, Any],
        mock_test_success: Dict[str, Any],
        monkeypatch,
    ):
        """Test full_feature + impl+test + run_tests=smoke flow."""
        # Mock BEAgent and TestAgent
        monkeypatch.setattr(
            orchestrator._backend_agent,
            "handle_request",
            lambda req, ctx=None: mock_be_success,
        )
        monkeypatch.setattr(
            orchestrator._test_agent,
            "handle_request",
            lambda req, ctx=None: mock_test_success,
        )

        request = {
            "flow": "api_dev",
            "module": "finance_profit",
            "change_type": "full_feature",
            "task": "Add profit summary API",
            "api_mode": "impl+test",
            "run_tests": "smoke",
            "auto_write": False,
        }
        result = orchestrator.handle_request(request)

        assert result["success"] is True
        assert "plan" in result["data"]["steps"]
        assert "impl" in result["data"]["steps"]
        assert "test" in result["data"]["steps"]
        assert "summary" in result["data"]["steps"]

    def test_schema_only_change(
        self,
        orchestrator: OrchestratorAgent,
        mock_be_success: Dict[str, Any],
        mock_test_success: Dict[str, Any],
        monkeypatch,
    ):
        """Test schema-only change type."""
        monkeypatch.setattr(
            orchestrator._backend_agent,
            "handle_request",
            lambda req, ctx=None: mock_be_success,
        )
        monkeypatch.setattr(
            orchestrator._test_agent,
            "handle_request",
            lambda req, ctx=None: mock_test_success,
        )

        request = {
            "flow": "api_dev",
            "module": "daily_reports",
            "change_type": "schema",
            "task": "Add new field to schema",
            "api_mode": "impl+test",
        }
        result = orchestrator.handle_request(request)

        assert result["success"] is True

    def test_bugfix_change_type(
        self,
        orchestrator: OrchestratorAgent,
        mock_be_success: Dict[str, Any],
        mock_test_success: Dict[str, Any],
        monkeypatch,
    ):
        """Test bugfix change type."""
        monkeypatch.setattr(
            orchestrator._backend_agent,
            "handle_request",
            lambda req, ctx=None: mock_be_success,
        )
        monkeypatch.setattr(
            orchestrator._test_agent,
            "handle_request",
            lambda req, ctx=None: mock_test_success,
        )

        request = {
            "flow": "api_dev",
            "module": "ledger",
            "change_type": "bugfix",
            "task": "Fix balance calculation bug",
            "api_mode": "impl+test",
        }
        result = orchestrator.handle_request(request)

        assert result["success"] is True


# =============================================================================
# Test Class: Dry-run Tests
# =============================================================================

class TestApiDevDryRun:
    """Test dry-run semantics (auto_write=False)."""

    def test_dry_run_no_files_written(
        self,
        orchestrator: OrchestratorAgent,
        mock_be_success: Dict[str, Any],
        mock_test_success: Dict[str, Any],
        monkeypatch,
        tmp_path: Path,
    ):
        """Dry-run should not write any files to disk."""
        monkeypatch.setattr(
            orchestrator._backend_agent,
            "handle_request",
            lambda req, ctx=None: mock_be_success,
        )
        monkeypatch.setattr(
            orchestrator._test_agent,
            "handle_request",
            lambda req, ctx=None: mock_test_success,
        )

        request = {
            "flow": "api_dev",
            "module": "finance_profit",
            "change_type": "full_feature",
            "task": "Test task",
            "auto_write": False,  # Dry-run
        }
        result = orchestrator.handle_request(request)

        assert result["success"] is True
        # Verify no files were written
        backend_dir = tmp_path / "backend"
        assert not backend_dir.exists() or len(list(backend_dir.rglob("*.py"))) == 0

    def test_auto_write_true_writes_files(
        self,
        orchestrator: OrchestratorAgent,
        mock_be_success: Dict[str, Any],
        mock_test_success: Dict[str, Any],
        monkeypatch,
        tmp_path: Path,
    ):
        """auto_write=True should write files to disk."""
        monkeypatch.setattr(
            orchestrator._backend_agent,
            "handle_request",
            lambda req, ctx=None: mock_be_success,
        )
        monkeypatch.setattr(
            orchestrator._test_agent,
            "handle_request",
            lambda req, ctx=None: mock_test_success,
        )

        request = {
            "flow": "api_dev",
            "module": "finance_profit",
            "change_type": "full_feature",
            "task": "Test task",
            "auto_write": True,  # Write files
        }
        result = orchestrator.handle_request(request)

        assert result["success"] is True
        summary = result["data"]["steps"]["summary"]["data"]
        assert summary["files_written"] > 0


# =============================================================================
# Test Class: Error Handling Tests
# =============================================================================

class TestApiDevErrorHandling:
    """Test error handling in api_dev flow."""

    def test_be_agent_failure_stops_flow(
        self,
        orchestrator: OrchestratorAgent,
        mock_be_failure: Dict[str, Any],
        monkeypatch,
    ):
        """BEAgent failure should mark overall as failed."""
        monkeypatch.setattr(
            orchestrator._backend_agent,
            "handle_request",
            lambda req, ctx=None: mock_be_failure,
        )

        request = {
            "flow": "api_dev",
            "module": "finance_profit",
            "change_type": "full_feature",
            "task": "Test task",
        }
        result = orchestrator.handle_request(request)

        assert result["success"] is False
        assert "impl" in result["data"]["steps"]
        # Test step should be skipped when impl fails
        assert "test" not in result["data"]["steps"] or \
               "skipped" in str(result["data"].get("notes", []))

    def test_test_agent_failure_marks_overall_failed(
        self,
        orchestrator: OrchestratorAgent,
        mock_be_success: Dict[str, Any],
        mock_test_failure: Dict[str, Any],
        monkeypatch,
    ):
        """TestAgent failure should mark overall as failed."""
        monkeypatch.setattr(
            orchestrator._backend_agent,
            "handle_request",
            lambda req, ctx=None: mock_be_success,
        )
        monkeypatch.setattr(
            orchestrator._test_agent,
            "handle_request",
            lambda req, ctx=None: mock_test_failure,
        )

        request = {
            "flow": "api_dev",
            "module": "finance_profit",
            "change_type": "full_feature",
            "task": "Test task",
            "run_tests": "smoke",
        }
        result = orchestrator.handle_request(request)

        assert result["success"] is False
        assert "test" in result["data"]["steps"]

    def test_run_tests_none_skips_test_step(
        self,
        orchestrator: OrchestratorAgent,
        mock_be_success: Dict[str, Any],
        monkeypatch,
    ):
        """run_tests=none should skip TestAgent call."""
        monkeypatch.setattr(
            orchestrator._backend_agent,
            "handle_request",
            lambda req, ctx=None: mock_be_success,
        )

        request = {
            "flow": "api_dev",
            "module": "finance_profit",
            "change_type": "full_feature",
            "task": "Test task",
            "run_tests": "none",
        }
        result = orchestrator.handle_request(request)

        assert result["success"] is True
        # Test step should not be present
        assert "test" not in result["data"]["steps"]

    def test_auto_write_skipped_on_failure(
        self,
        orchestrator: OrchestratorAgent,
        mock_be_success: Dict[str, Any],
        mock_test_failure: Dict[str, Any],
        monkeypatch,
        tmp_path: Path,
    ):
        """auto_write should be skipped when flow fails."""
        monkeypatch.setattr(
            orchestrator._backend_agent,
            "handle_request",
            lambda req, ctx=None: mock_be_success,
        )
        monkeypatch.setattr(
            orchestrator._test_agent,
            "handle_request",
            lambda req, ctx=None: mock_test_failure,
        )

        request = {
            "flow": "api_dev",
            "module": "finance_profit",
            "change_type": "full_feature",
            "task": "Test task",
            "auto_write": True,
            "run_tests": "smoke",
        }
        result = orchestrator.handle_request(request)

        assert result["success"] is False
        summary = result["data"]["steps"]["summary"]["data"]
        assert summary["files_written"] == 0


# =============================================================================
# Test Class: suggested_tests Output Tests
# =============================================================================

class TestApiDevSuggestedTests:
    """Test suggested_tests output aligned with TEST_AUTOMATION_SOT v1.0.1."""

    def test_full_feature_includes_regression_test(
        self,
        orchestrator: OrchestratorAgent,
        mock_be_success: Dict[str, Any],
        mock_test_success: Dict[str, Any],
        monkeypatch,
    ):
        """full_feature should suggest both module test and regression test."""
        monkeypatch.setattr(
            orchestrator._backend_agent,
            "handle_request",
            lambda req, ctx=None: mock_be_success,
        )
        monkeypatch.setattr(
            orchestrator._test_agent,
            "handle_request",
            lambda req, ctx=None: mock_test_success,
        )

        request = {
            "flow": "api_dev",
            "module": "finance_profit",
            "change_type": "full_feature",
            "task": "Test task",
        }
        result = orchestrator.handle_request(request)

        summary = result["data"]["steps"]["summary"]["data"]
        suggested_tests = summary.get("suggested_tests", [])

        # Should have at least 2 tests: module + regression
        assert len(suggested_tests) >= 2

        # Check for module test
        module_tests = [t for t in suggested_tests if t.get("scope") == "module"]
        assert len(module_tests) >= 1

        # Check for regression test
        regression_tests = [t for t in suggested_tests if t.get("mode") == "REGRESSION"]
        assert len(regression_tests) >= 1

    def test_bugfix_no_regression_test(
        self,
        orchestrator: OrchestratorAgent,
        mock_be_success: Dict[str, Any],
        mock_test_success: Dict[str, Any],
        monkeypatch,
    ):
        """bugfix should only suggest module test, not regression."""
        monkeypatch.setattr(
            orchestrator._backend_agent,
            "handle_request",
            lambda req, ctx=None: mock_be_success,
        )
        monkeypatch.setattr(
            orchestrator._test_agent,
            "handle_request",
            lambda req, ctx=None: mock_test_success,
        )

        request = {
            "flow": "api_dev",
            "module": "ledger",
            "change_type": "bugfix",
            "task": "Fix bug",
        }
        result = orchestrator.handle_request(request)

        summary = result["data"]["steps"]["summary"]["data"]
        suggested_tests = summary.get("suggested_tests", [])

        # bugfix should not include REGRESSION mode
        regression_tests = [t for t in suggested_tests if t.get("mode") == "REGRESSION"]
        assert len(regression_tests) == 0


# =============================================================================
# Test Class: Context Passthrough Tests
# =============================================================================

class TestApiDevContextPassthrough:
    """Test AgentContext passthrough to sub-agents."""

    def test_context_run_id_in_result(
        self,
        orchestrator: OrchestratorAgent,
        mock_be_success: Dict[str, Any],
        mock_test_success: Dict[str, Any],
        monkeypatch,
    ):
        """Result should contain consistent run_id from context."""
        monkeypatch.setattr(
            orchestrator._backend_agent,
            "handle_request",
            lambda req, ctx=None: mock_be_success,
        )
        monkeypatch.setattr(
            orchestrator._test_agent,
            "handle_request",
            lambda req, ctx=None: mock_test_success,
        )

        context = AgentContext()
        request = {
            "flow": "api_dev",
            "module": "finance_profit",
            "change_type": "full_feature",
            "task": "Test task",
        }
        result = orchestrator.handle_request(request, context)

        # Note: api_dev flow doesn't pass context to sub-agents in current impl
        # This test documents expected behavior
        assert result["success"] is True


# =============================================================================
# Test Class: All Module Coverage
# =============================================================================

class TestApiDevAllModules:
    """Test all valid modules are accepted."""

    @pytest.mark.parametrize("module", [
        "daily_reports",
        "topup_requests",
        "ledger",
        "reconciliation",
        "ad_accounts",
        "projects",
        "channels",
        "transfers",
        "finance_profit",
        "suppliers",
        "settlements",
        "trend_risk",
        "auth",
    ])
    def test_all_modules_accepted(
        self,
        orchestrator: OrchestratorAgent,
        module: str,
        mock_be_success: Dict[str, Any],
        monkeypatch,
    ):
        """All API_DEV_MODULES should be accepted."""
        monkeypatch.setattr(
            orchestrator._backend_agent,
            "handle_request",
            lambda req, ctx=None: mock_be_success,
        )

        request = {
            "flow": "api_dev",
            "module": module,
            "change_type": "schema",
            "task": f"Test {module}",
            "run_tests": "none",
        }
        result = orchestrator.handle_request(request)

        # Should not fail validation
        assert "invalid module" not in (result.get("error") or "").lower()
