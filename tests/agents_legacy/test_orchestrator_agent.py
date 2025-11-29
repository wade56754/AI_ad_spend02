"""Unit tests for OrchestratorAgent."""

import pytest
from agents.agents_config import create_agent


def test_orchestrator_handle_request_missing_flow():
    """Test that OrchestratorAgent returns error when flow is missing."""
    orch_agent = create_agent("orch")
    response = orch_agent.handle_request({})

    assert response["success"] is False
    assert response["error"] is not None
    assert "flow" in response["error"].lower()


def test_orchestrator_handle_request_invalid_flow():
    """Test that OrchestratorAgent returns error for unknown flow."""
    orch_agent = create_agent("orch")
    response = orch_agent.handle_request({"flow": "invalid_flow_name"})

    assert response["success"] is False
    assert response["error"] is not None
    assert "unknown flow" in response["error"].lower()


def test_orchestrator_backend_only_flow_success(monkeypatch):
    """Test backend_only flow with successful backend execution."""
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


def test_orchestrator_backend_only_flow_failure(monkeypatch):
    """Test backend_only flow with failed backend execution."""
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
    assert response["data"]["steps"]["backend"]["success"] is False


def test_orchestrator_full_pipeline_all_success(monkeypatch):
    """Test full_pipeline with all steps successful."""
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


def test_orchestrator_full_pipeline_backend_fails(monkeypatch):
    """Test full_pipeline stops when backend fails."""
    def mock_be_handle_request(self, request):
        return {"success": False, "data": None, "error": "Backend failed"}

    from agents.agent_core.be_agent import BEAgent
    monkeypatch.setattr(BEAgent, "handle_request", mock_be_handle_request)

    orch_agent = create_agent("orch")
    response = orch_agent.handle_request({
        "flow": "full_pipeline",
        "backend_request": {"task": "test", "target_files": ["be.py"]},
        "frontend_request": {"task": "test", "target_files": ["fe.tsx"]}
    })

    assert response["success"] is False
    assert "backend" in response["data"]["steps"]
    assert "frontend" not in response["data"]["steps"]
    assert "test" not in response["data"]["steps"]


def test_orchestrator_full_pipeline_frontend_fails(monkeypatch):
    """Test full_pipeline stops when frontend fails."""
    def mock_be_handle_request(self, request):
        return {"success": True, "data": {"changes": {}}, "error": None}

    def mock_fe_handle_request(self, request):
        return {"success": False, "data": None, "error": "Frontend failed"}

    from agents.agent_core.be_agent import BEAgent
    from agents.agent_core.fe_agent import FEAgent

    monkeypatch.setattr(BEAgent, "handle_request", mock_be_handle_request)
    monkeypatch.setattr(FEAgent, "handle_request", mock_fe_handle_request)

    orch_agent = create_agent("orch")
    response = orch_agent.handle_request({
        "flow": "full_pipeline",
        "backend_request": {"task": "test", "target_files": ["be.py"]},
        "frontend_request": {"task": "test", "target_files": ["fe.tsx"]}
    })

    assert response["success"] is False
    assert "backend" in response["data"]["steps"]
    assert "frontend" in response["data"]["steps"]
    assert "test" not in response["data"]["steps"]


def test_orchestrator_frontend_restructure_flow_no_exception(monkeypatch):
    """Test frontend_restructure flow runs without exception."""
    def mock_doc_handle_request(self, request):
        return {
            "success": True,
            "action": request.get("action", "generate"),
            "doc_type": request.get("doc_type", "module"),
            "content": "# Generated Doc",
            "changes": [],
            "notes": ["Generated successfully"],
            "error": None,
        }

    def mock_fe_handle_request(self, request):
        return {
            "success": True,
            "data": {"changes": {"file.ts": "code"}, "notes": []},
            "error": None,
        }

    def mock_review_handle_request(self, request):
        return {
            "success": True,
            "passed": True,
            "violations": [],
            "warnings": [],
            "notes": ["Review passed"],
            "error": None,
        }

    from agents.agent_core.doc_agent import DocAgent
    from agents.agent_core.fe_agent import FEAgent
    from agents.agent_core.code_review_agent import CodeReviewAgent

    monkeypatch.setattr(DocAgent, "handle_request", mock_doc_handle_request)
    monkeypatch.setattr(FEAgent, "handle_request", mock_fe_handle_request)
    monkeypatch.setattr(CodeReviewAgent, "handle_request", mock_review_handle_request)

    orch_agent = create_agent("orch")
    response = orch_agent.handle_request({
        "flow": "frontend_restructure",
        "task": "重构前端结构",
        "spec_version": "v1.0",
    })

    # Should complete without exception
    assert response["success"] is True
    assert response["data"]["flow"] == "frontend_restructure"
    assert "doc_spec" in response["data"]["steps"]
    assert "frontend" in response["data"]["steps"]
    assert "doc_manifest" in response["data"]["steps"]
    assert "review" in response["data"]["steps"]
    assert "summary" in response["data"]["steps"]


def test_orchestrator_frontend_restructure_flow_review_failure(monkeypatch):
    """Test frontend_restructure flow fails when SoT Guard finds P0 violations."""
    def mock_doc_handle_request(self, request):
        return {
            "success": True,
            "action": "generate",
            "doc_type": "module",
            "content": "# Doc",
            "changes": [],
            "notes": [],
            "error": None,
        }

    def mock_fe_handle_request(self, request):
        return {
            "success": True,
            "data": {"changes": {"file.ts": "bad code"}, "notes": []},
            "error": None,
        }

    def mock_review_handle_request(self, request):
        return {
            "success": True,
            "passed": False,  # P0 violations found
            "violations": [{"rule": "SM-DR-001", "detail": "Invalid state"}],
            "warnings": [],
            "notes": ["P0 violation found"],
            "error": None,
        }

    from agents.agent_core.doc_agent import DocAgent
    from agents.agent_core.fe_agent import FEAgent
    from agents.agent_core.code_review_agent import CodeReviewAgent

    monkeypatch.setattr(DocAgent, "handle_request", mock_doc_handle_request)
    monkeypatch.setattr(FEAgent, "handle_request", mock_fe_handle_request)
    monkeypatch.setattr(CodeReviewAgent, "handle_request", mock_review_handle_request)

    orch_agent = create_agent("orch")
    response = orch_agent.handle_request({
        "flow": "frontend_restructure",
        "task": "重构前端结构",
    })

    # Should fail due to P0 violation
    assert response["success"] is False
    assert "P0 violations" in response["error"]
    assert "review" in response["data"]["steps"]


def test_orchestrator_frontend_restructure_dry_run_no_files_written(monkeypatch, tmp_path):
    """Test frontend_restructure with auto_write=False does not write files to disk."""
    def mock_doc_handle_request(self, request):
        return {
            "success": True,
            "action": request.get("action", "generate"),
            "doc_type": request.get("doc_type", "module"),
            "content": "# Generated Doc",
            "changes": [],
            "notes": ["Generated successfully"],
            "error": None,
        }

    def mock_fe_handle_request(self, request):
        # Return fake changes that would be written if auto_write=True
        return {
            "success": True,
            "data": {
                "changes": {
                    "src/lib/api/apiFetch.ts": "// apiFetch content",
                    "src/lib/api/apiTypes.ts": "// apiTypes content",
                },
                "notes": []
            },
            "error": None,
        }

    def mock_review_handle_request(self, request):
        return {
            "success": True,
            "passed": True,
            "violations": [],
            "warnings": [],
            "notes": ["Review passed"],
            "error": None,
        }

    from agents.agent_core.doc_agent import DocAgent
    from agents.agent_core.fe_agent import FEAgent
    from agents.agent_core.code_review_agent import CodeReviewAgent

    monkeypatch.setattr(DocAgent, "handle_request", mock_doc_handle_request)
    monkeypatch.setattr(FEAgent, "handle_request", mock_fe_handle_request)
    monkeypatch.setattr(CodeReviewAgent, "handle_request", mock_review_handle_request)

    # Create orchestrator with tmp_path as base_path
    orch_agent = create_agent("orch", base_path=tmp_path)

    # Run with auto_write=False (default)
    response = orch_agent.handle_request({
        "flow": "frontend_restructure",
        "task": "重构前端结构",
        "auto_write": False,
    })

    # Should succeed
    assert response["success"] is True
    assert response["data"]["flow"] == "frontend_restructure"

    # Check summary
    summary = response["data"]["steps"]["summary"]["data"]
    assert summary["auto_write"] is False
    assert summary["files_generated"] == 2
    assert summary["files_written"] == 0

    # Verify no files were written to disk
    frontend_dir = tmp_path / "frontend"
    assert not frontend_dir.exists() or len(list(frontend_dir.rglob("*"))) == 0

    # Verify dry-run message in response
    assert "dry-run" in response["message"]
