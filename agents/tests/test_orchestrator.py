"""
Tests for OrchestratorAgent

Migrated from tests/agents_legacy/test_orchestrator_agent.py
Updated to align with new error handling strategy (P2-05: non-blocking failures).
"""

import pytest
from agents.agents_config import create_agent


class TestOrchestratorBasicFlow:
    """Basic flow validation tests."""

    def test_missing_flow_returns_error(self):
        """OrchestratorAgent should return error when flow is missing."""
        orch_agent = create_agent("orch")
        response = orch_agent.handle_request({})

        assert response["success"] is False
        assert response["error"] is not None
        assert "flow" in response["error"].lower()

    def test_invalid_flow_returns_error(self):
        """OrchestratorAgent should return error for unknown flow."""
        orch_agent = create_agent("orch")
        response = orch_agent.handle_request({"flow": "invalid_flow_name"})

        assert response["success"] is False
        assert response["error"] is not None
        assert "unknown flow" in response["error"].lower()


class TestBackendOnlyFlow:
    """Tests for backend_only flow."""

    def test_success_case(self, monkeypatch):
        """backend_only flow should succeed with valid backend result."""
        def mock_be_handle_request(self, request):
            return {"success": True, "data": {"changes": {"file.py": "code"}}, "error": None}

        from agents.agent_core.be_agent import BEAgent
        monkeypatch.setattr(BEAgent, "handle_request", mock_be_handle_request)

        orch_agent = create_agent("orch")
        response = orch_agent.handle_request({
            "flow": "backend_only",
            "backend_request": {"task": "test", "target_files": ["file.py"]}
        })

        assert response["success"] is True
        assert "backend" in response["data"]["steps"]
        assert response["data"]["steps"]["backend"]["success"] is True

    def test_failure_case(self, monkeypatch):
        """backend_only flow should fail when backend fails."""
        def mock_be_handle_request(self, request):
            return {"success": False, "data": None, "error": "Backend error"}

        from agents.agent_core.be_agent import BEAgent
        monkeypatch.setattr(BEAgent, "handle_request", mock_be_handle_request)

        orch_agent = create_agent("orch")
        response = orch_agent.handle_request({
            "flow": "backend_only",
            "backend_request": {"task": "test", "target_files": ["file.py"]}
        })

        assert response["success"] is False
        assert "backend" in response["data"]["steps"]


class TestFullPipelineFlow:
    """Tests for full_pipeline flow."""

    def test_all_success(self, monkeypatch):
        """full_pipeline should succeed when all steps succeed."""
        def mock_be_handle_request(self, request):
            return {"success": True, "data": {"changes": {}}, "error": None}

        def mock_fe_handle_request(self, request):
            return {"success": True, "data": {"changes": {}}, "error": None}

        def mock_test_handle_request(self, request):
            return {"success": True, "data": {"prompt": "test", "executed": False}, "error": None}

        from agents.agent_core.be_agent import BEAgent
        from agents.agent_core.fe_agent import FEAgent
        from agents.agent_core.test_agent import TestAgent

        monkeypatch.setattr(BEAgent, "handle_request", mock_be_handle_request)
        monkeypatch.setattr(FEAgent, "handle_request", mock_fe_handle_request)
        monkeypatch.setattr(TestAgent, "handle_request", mock_test_handle_request)

        orch_agent = create_agent("orch")
        response = orch_agent.handle_request({
            "flow": "full_pipeline",
            "backend_request": {"task": "test", "target_files": ["be.py"]},
            "frontend_request": {"task": "test", "target_files": ["fe.tsx"]},
            "test_enabled": True
        })

        assert response["success"] is True
        assert "backend" in response["data"]["steps"]
        assert "frontend" in response["data"]["steps"]
        assert "test" in response["data"]["steps"]


class TestAgentSmoke:
    """Smoke tests for basic agent behavior."""

    def test_fe_agent_missing_task_error(self):
        """FEAgent should return error when task is missing."""
        fe_agent = create_agent("fe")
        resp = fe_agent.handle_request({"target_files": ["dummy.tsx"]})
        assert resp["success"] is False
        assert isinstance(resp["error"], str)
        assert "task" in resp["error"].lower()

    def test_be_agent_missing_task_error(self):
        """BEAgent should return error when task is missing."""
        be_agent = create_agent("be")
        resp = be_agent.handle_request({"target_files": ["dummy.py"]})
        assert resp["success"] is False
        assert isinstance(resp["error"], str)
        assert "task" in resp["error"].lower()

    def test_test_agent_generates_prompt(self):
        """TestAgent should generate prompt with executed=False."""
        test_agent = create_agent("test")
        response = test_agent.handle_request({})

        assert response["success"] is True
        assert response["data"] is not None
        assert response["data"]["executed"] is False
        assert "prompt" in response["data"]
        assert len(response["data"]["prompt"]) > 0


class TestGenBackendFlow:
    """Tests for gen_backend flow."""

    def test_missing_task_returns_error(self):
        """gen_backend flow should return error when task is missing."""
        orch_agent = create_agent("orch")
        response = orch_agent.handle_request({"flow": "gen_backend"})

        assert response["success"] is False
        assert "task" in response["error"].lower()
        assert "Missing 'task' field" in response["data"]["errors"][0]

    def test_empty_module_list_returns_error(self):
        """gen_backend flow should return error for empty module list."""
        orch_agent = create_agent("orch")
        response = orch_agent.handle_request({"flow": "gen_backend", "task": "   ,  , "})

        assert response["success"] is False
        assert "No valid modules" in response["error"]

    def test_parses_comma_separated_modules(self, monkeypatch):
        """gen_backend flow should parse comma-separated module list."""
        call_count = {"value": 0}
        modules_called = []

        def mock_be_handle_request(self, request):
            call_count["value"] += 1
            modules_called.append(request.get("module"))
            return {"success": True, "data": {"changes": {}}, "error": None}

        from agents.agent_core.be_agent import BEAgent
        monkeypatch.setattr(BEAgent, "handle_request", mock_be_handle_request)

        orch_agent = create_agent("orch")
        response = orch_agent.handle_request({
            "flow": "gen_backend",
            "task": "daily_reports, topups, ledger"
        })

        assert response["success"] is True
        assert call_count["value"] == 3
        assert set(modules_called) == {"daily_reports", "topups", "ledger"}

    def test_aggregates_module_results(self, monkeypatch):
        """gen_backend flow should aggregate results from all modules."""
        def mock_be_handle_request(self, request):
            module = request.get("module")
            return {
                "success": True,
                "data": {"changes": {f"routers/{module}.py": f"# {module} router"}},
                "error": None
            }

        from agents.agent_core.be_agent import BEAgent
        monkeypatch.setattr(BEAgent, "handle_request", mock_be_handle_request)

        orch_agent = create_agent("orch")
        response = orch_agent.handle_request({
            "flow": "gen_backend",
            "task": "auth, projects"
        })

        assert response["success"] is True
        assert "module_auth" in response["data"]["steps"]
        assert "module_projects" in response["data"]["steps"]
        assert response["data"]["steps"]["summary"]["data"]["modules_success"] == 2
        assert response["data"]["steps"]["summary"]["data"]["modules_failed"] == 0

    def test_handles_partial_failure(self, monkeypatch):
        """gen_backend flow should handle partial module failures."""
        def mock_be_handle_request(self, request):
            module = request.get("module")
            if module == "daily_reports":
                return {"success": True, "data": {"changes": {}}, "error": None}
            else:
                return {"success": False, "data": None, "error": f"Failed to generate {module}"}

        from agents.agent_core.be_agent import BEAgent
        monkeypatch.setattr(BEAgent, "handle_request", mock_be_handle_request)

        orch_agent = create_agent("orch")
        response = orch_agent.handle_request({
            "flow": "gen_backend",
            "task": "daily_reports, topups"
        })

        assert response["success"] is False  # Partial failure = overall failure
        assert response["data"]["steps"]["summary"]["data"]["modules_success"] == 1
        assert response["data"]["steps"]["summary"]["data"]["modules_failed"] == 1
        assert len(response["data"]["errors"]) == 1

    def test_unknown_module_uses_default_files(self, monkeypatch):
        """gen_backend flow should use default file pattern for unknown modules."""
        captured_request = {}

        def mock_be_handle_request(self, request):
            captured_request.update(request)
            return {"success": True, "data": {"changes": {}}, "error": None}

        from agents.agent_core.be_agent import BEAgent
        monkeypatch.setattr(BEAgent, "handle_request", mock_be_handle_request)

        orch_agent = create_agent("orch")
        response = orch_agent.handle_request({
            "flow": "gen_backend",
            "task": "custom_module"
        })

        assert response["success"] is True
        assert "routers/custom_module.py" in captured_request["target_files"]
        assert "services/custom_module_service.py" in captured_request["target_files"]
        assert "schemas/custom_module.py" in captured_request["target_files"]

    def test_extra_prompt_passed_to_beagent(self, monkeypatch):
        """gen_backend flow should pass extra prompt to BEAgent."""
        captured_request = {}

        def mock_be_handle_request(self, request):
            captured_request.update(request)
            return {"success": True, "data": {"changes": {}}, "error": None}

        from agents.agent_core.be_agent import BEAgent
        monkeypatch.setattr(BEAgent, "handle_request", mock_be_handle_request)

        orch_agent = create_agent("orch")
        response = orch_agent.handle_request({
            "flow": "gen_backend",
            "task": "auth",
            "prompt": "Align with SoT v2.6"
        })

        assert response["success"] is True
        assert "Align with SoT v2.6" in captured_request["task"]
