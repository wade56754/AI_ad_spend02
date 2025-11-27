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
