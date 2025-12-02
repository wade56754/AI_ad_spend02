"""
Tests for Agent Platform CLI and HTTP endpoints.

Phase 3.0C: Tests for unified CLI and HTTP entry points.

Test coverage:
    - CLI argument parsing
    - CLI list/info/run/orch commands
    - HTTP /agents endpoints
    - HTTP /agents/run endpoint
    - HTTP /agents/orch endpoint
"""

import json
import pytest
from unittest.mock import patch, MagicMock

# ============================================================
# CLI Tests
# ============================================================


class TestCLIArgumentParsing:
    """Test CLI argument parsing."""

    def test_create_parser_returns_parser(self):
        """Parser creation should return ArgumentParser."""
        from agent_platform.cli import create_parser

        parser = create_parser()
        assert parser is not None
        assert parser.prog == "agent_platform"

    def test_list_command_parsed(self):
        """List command should be parsed correctly."""
        from agent_platform.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["list"])
        assert args.command == "list"

    def test_info_command_parsed(self):
        """Info command should parse agent name."""
        from agent_platform.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["info", "be"])
        assert args.command == "info"
        assert args.agent == "be"

    def test_run_command_parsed(self):
        """Run command should parse all arguments."""
        from agent_platform.cli import create_parser

        parser = create_parser()
        args = parser.parse_args([
            "run", "be",
            "--task", "Generate API",
            "--target-files", "routers/foo.py", "services/bar.py",
        ])
        assert args.command == "run"
        assert args.agent == "be"
        assert args.task == "Generate API"
        assert args.target_files == ["routers/foo.py", "services/bar.py"]

    def test_orch_command_parsed(self):
        """Orch command should parse flow and options."""
        from agent_platform.cli import create_parser

        parser = create_parser()
        args = parser.parse_args([
            "orch",
            "--flow", "be_then_test",
            "--task", "Implement feature",
            "--module", "finance",
            "--mode", "execute",
        ])
        assert args.command == "orch"
        assert args.flow == "be_then_test"
        assert args.task == "Implement feature"
        assert args.module == "finance"
        assert args.mode == "execute"

    def test_orch_flow_choices(self):
        """Orch flow should be restricted to valid choices."""
        from agent_platform.cli import create_parser

        parser = create_parser()

        # Valid flows should parse
        for flow in ["be_then_test", "backend_only", "frontend_only", "full_pipeline"]:
            args = parser.parse_args(["orch", "--flow", flow])
            assert args.flow == flow

    def test_global_options_parsed(self):
        """Global options should be parsed with any command."""
        from agent_platform.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["-v", "-o", "json", "--compact", "list"])
        assert args.verbose is True
        assert args.output == "json"
        assert args.compact is True


class TestCLIListCommand:
    """Test CLI list command execution."""

    def test_cmd_list_calls_registry(self):
        """List command should call registry and print agents."""
        from agent_platform.cli import cmd_list
        import argparse

        # Mock the registry
        with patch("agent_platform.cli._ensure_agents_registered"):
            with patch("agent_platform.cli.list_agents") as mock_list:
                mock_meta = MagicMock()
                mock_meta.name = "be"
                mock_meta.version = "1.0.0"
                mock_meta.description = "Backend agent"
                mock_meta.tags = ["backend", "codegen"]
                mock_list.return_value = [mock_meta]

                args = argparse.Namespace()
                result = cmd_list(args)

                assert result == 0
                mock_list.assert_called_once()

    def test_cmd_list_empty_registry(self):
        """List command should handle empty registry gracefully."""
        from agent_platform.cli import cmd_list
        import argparse

        with patch("agent_platform.cli._ensure_agents_registered"):
            with patch("agent_platform.cli.list_agents") as mock_list:
                mock_list.return_value = []

                args = argparse.Namespace()
                result = cmd_list(args)

                assert result == 0


class TestCLIInfoCommand:
    """Test CLI info command execution."""

    def test_cmd_info_found(self):
        """Info command should return 0 for existing agent."""
        from agent_platform.cli import cmd_info
        import argparse

        with patch("agent_platform.cli._ensure_agents_registered"):
            with patch("agent_platform.cli.get_registry") as mock_get_reg:
                mock_meta = MagicMock()
                mock_meta.name = "be"
                mock_meta.version = "1.0.0"
                mock_meta.description = "Backend agent"
                mock_meta.tags = ["backend"]

                mock_registry = MagicMock()
                mock_registry.get_agent_metadata.return_value = mock_meta
                mock_get_reg.return_value = mock_registry

                args = argparse.Namespace(agent="be")
                result = cmd_info(args)

                assert result == 0

    def test_cmd_info_not_found(self):
        """Info command should return 1 for non-existent agent."""
        from agent_platform.cli import cmd_info
        import argparse

        with patch("agent_platform.cli._ensure_agents_registered"):
            with patch("agent_platform.cli.get_registry") as mock_get_reg:
                mock_registry = MagicMock()
                mock_registry.get_agent_metadata.return_value = None
                mock_get_reg.return_value = mock_registry

                with patch("agent_platform.cli.list_agents", return_value=[]):
                    args = argparse.Namespace(agent="nonexistent")
                    result = cmd_info(args)

                    assert result == 1


class TestCLIRunCommand:
    """Test CLI run command execution."""

    def test_cmd_run_success(self):
        """Run command should execute agent and return 0 on success."""
        from agent_platform.cli import cmd_run
        import argparse

        with patch("agent_platform.cli._ensure_agents_registered"):
            with patch("agent_platform.cli.create_agent") as mock_create:
                mock_agent = MagicMock()
                mock_agent.handle_request.return_value = {
                    "success": True,
                    "data": {"changes": {}},
                    "error": None,
                }
                mock_create.return_value = mock_agent

                args = argparse.Namespace(
                    agent="be",
                    task="Test task",
                    target_files=["file.py"],
                    json=None,
                    verbose=False,
                    output="human",
                    compact=False,
                )
                result = cmd_run(args)

                assert result == 0
                mock_agent.handle_request.assert_called_once()

    def test_cmd_run_failure(self):
        """Run command should return 1 on agent failure."""
        from agent_platform.cli import cmd_run
        import argparse

        with patch("agent_platform.cli._ensure_agents_registered"):
            with patch("agent_platform.cli.create_agent") as mock_create:
                mock_agent = MagicMock()
                mock_agent.handle_request.return_value = {
                    "success": False,
                    "data": {},
                    "error": "Test error",
                }
                mock_create.return_value = mock_agent

                args = argparse.Namespace(
                    agent="be",
                    task="Test task",
                    target_files=[],
                    json=None,
                    verbose=False,
                    output="human",
                    compact=False,
                )
                result = cmd_run(args)

                assert result == 1


class TestCLIOrchCommand:
    """Test CLI orch command execution."""

    def test_cmd_orch_be_then_test_success(self):
        """Orch command should execute be_then_test flow."""
        from agent_platform.cli import cmd_orch
        import argparse

        with patch("agent_platform.cli._ensure_agents_registered"):
            with patch("agent_platform.cli.create_agent") as mock_create:
                mock_orch = MagicMock()
                mock_orch.handle_request.return_value = {
                    "success": True,
                    "data": {
                        "flow": "be_then_test",
                        "backend_result": {"success": True},
                        "test_result": {"success": True},
                        "meta": {"run_id": "test-123", "called_agents": ["be", "test"]},
                    },
                    "error": None,
                }
                mock_create.return_value = mock_orch

                args = argparse.Namespace(
                    flow="be_then_test",
                    task="Test task",
                    target_files=["file.py"],
                    module="test_module",
                    mode="dry-run",
                    json=None,
                    verbose=False,
                    output="human",
                    compact=False,
                )
                result = cmd_orch(args)

                assert result == 0

    def test_cmd_orch_execute_mode_sets_auto_write(self):
        """Execute mode should set auto_write=True in request."""
        from agent_platform.cli import cmd_orch
        import argparse

        with patch("agent_platform.cli._ensure_agents_registered"):
            with patch("agent_platform.cli.create_agent") as mock_create:
                mock_orch = MagicMock()
                mock_orch.handle_request.return_value = {
                    "success": True,
                    "data": {},
                    "error": None,
                }
                mock_create.return_value = mock_orch

                args = argparse.Namespace(
                    flow="backend_only",
                    task="Test",
                    target_files=[],
                    module=None,
                    mode="execute",
                    json=None,
                    verbose=False,
                    output="human",
                    compact=False,
                )
                cmd_orch(args)

                # Verify auto_write was set
                call_args = mock_orch.handle_request.call_args
                request = call_args[0][0]
                assert request.get("auto_write") is True


# ============================================================
# HTTP Endpoint Tests
# ============================================================


class TestHTTPListEndpoint:
    """Test HTTP GET /agents endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from backend.routers.agents import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/api/v1")
        return TestClient(app)

    def test_list_agents_success(self, client):
        """GET /agents should return list of agents."""
        with patch("backend.routers.agents._ensure_agents_registered"):
            with patch("backend.routers.agents.list_agents") as mock_list:
                mock_meta = MagicMock()
                mock_meta.name = "be"
                mock_meta.version = "1.0.0"
                mock_meta.description = "Backend agent"
                mock_meta.tags = ["backend"]
                mock_list.return_value = [mock_meta]

                response = client.get("/api/v1/agents")

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "agents" in data["data"]
                assert len(data["data"]["agents"]) == 1


class TestHTTPInfoEndpoint:
    """Test HTTP GET /agents/{name} endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from backend.routers.agents import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/api/v1")
        return TestClient(app)

    def test_get_agent_info_found(self, client):
        """GET /agents/{name} should return agent info."""
        with patch("backend.routers.agents._ensure_agents_registered"):
            with patch("backend.routers.agents.get_registry") as mock_get_reg:
                mock_meta = MagicMock()
                mock_meta.name = "be"
                mock_meta.version = "1.0.0"
                mock_meta.description = "Backend agent"
                mock_meta.tags = ["backend"]

                mock_registry = MagicMock()
                mock_registry.get_agent_metadata.return_value = mock_meta
                mock_get_reg.return_value = mock_registry

                response = client.get("/api/v1/agents/be")

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["name"] == "be"

    def test_get_agent_info_not_found(self, client):
        """GET /agents/{name} should return 404 for unknown agent."""
        with patch("backend.routers.agents._ensure_agents_registered"):
            with patch("backend.routers.agents.get_registry") as mock_get_reg:
                mock_registry = MagicMock()
                mock_registry.get_agent_metadata.return_value = None
                mock_registry.list_agents.return_value = []
                mock_get_reg.return_value = mock_registry

                response = client.get("/api/v1/agents/nonexistent")

                assert response.status_code == 404


class TestHTTPRunEndpoint:
    """Test HTTP POST /agents/run endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from backend.routers.agents import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/api/v1")
        return TestClient(app)

    def test_run_agent_success(self, client):
        """POST /agents/run should execute agent successfully."""
        with patch("backend.routers.agents._ensure_agents_registered"):
            with patch("backend.routers.agents.create_agent") as mock_create:
                mock_agent = MagicMock()
                mock_agent.handle_request.return_value = {
                    "success": True,
                    "data": {"changes": {"file.py": "content"}},
                    "error": None,
                }
                mock_create.return_value = mock_agent

                response = client.post(
                    "/api/v1/agents/run",
                    json={
                        "agent": "be",
                        "request": {
                            "task": "Generate API",
                            "target_files": ["routers/foo.py"],
                        },
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "run_id" in data["data"]

    def test_run_agent_not_found(self, client):
        """POST /agents/run should return 404 for unknown agent."""
        with patch("backend.routers.agents._ensure_agents_registered"):
            with patch("backend.routers.agents.create_agent") as mock_create:
                mock_create.side_effect = ValueError("Agent 'xyz' not found")

                response = client.post(
                    "/api/v1/agents/run",
                    json={
                        "agent": "xyz",
                        "request": {},
                    },
                )

                assert response.status_code == 404


class TestHTTPOrchEndpoint:
    """Test HTTP POST /agents/orch endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from backend.routers.agents import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/api/v1")
        return TestClient(app)

    def test_orch_be_then_test_success(self, client):
        """POST /agents/orch should execute be_then_test flow."""
        with patch("backend.routers.agents._ensure_agents_registered"):
            with patch("backend.routers.agents.create_agent") as mock_create:
                mock_orch = MagicMock()
                mock_orch.handle_request.return_value = {
                    "success": True,
                    "data": {
                        "flow": "be_then_test",
                        "backend_result": {"success": True},
                        "test_result": {"success": True},
                        "meta": {"run_id": "test-123"},
                    },
                    "error": None,
                }
                mock_create.return_value = mock_orch

                response = client.post(
                    "/api/v1/agents/orch",
                    json={
                        "flow": "be_then_test",
                        "task": "Implement feature",
                        "target_files": ["routers/foo.py"],
                        "module": "foo",
                        "mode": "dry-run",
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["flow"] == "be_then_test"

    def test_orch_execute_mode(self, client):
        """POST /agents/orch with mode=execute should set auto_write."""
        with patch("backend.routers.agents._ensure_agents_registered"):
            with patch("backend.routers.agents.create_agent") as mock_create:
                mock_orch = MagicMock()
                mock_orch.handle_request.return_value = {
                    "success": True,
                    "data": {},
                    "error": None,
                }
                mock_create.return_value = mock_orch

                client.post(
                    "/api/v1/agents/orch",
                    json={
                        "flow": "backend_only",
                        "mode": "execute",
                    },
                )

                # Verify auto_write was passed
                call_args = mock_orch.handle_request.call_args
                request = call_args[0][0]
                assert request.get("auto_write") is True

    def test_orch_flow_failure(self, client):
        """POST /agents/orch should return 400 on flow failure."""
        with patch("backend.routers.agents._ensure_agents_registered"):
            with patch("backend.routers.agents.create_agent") as mock_create:
                mock_orch = MagicMock()
                mock_orch.handle_request.return_value = {
                    "success": False,
                    "data": {},
                    "error": "BEAgent failed: validation error",
                }
                mock_create.return_value = mock_orch

                response = client.post(
                    "/api/v1/agents/orch",
                    json={
                        "flow": "be_then_test",
                        "task": "Bad task",
                    },
                )

                assert response.status_code == 400
                data = response.json()
                assert data["success"] is False


# ============================================================
# Integration Tests (with real registry)
# ============================================================


class TestCLIIntegration:
    """Integration tests for CLI with real agent registry."""

    def test_main_no_args_prints_help(self, capsys):
        """Main with no args should print help."""
        from agent_platform.cli import main

        result = main([])
        assert result == 0

    def test_main_list_with_registered_agents(self, capsys):
        """List command should show registered agents."""
        from agent_platform.cli import main
        from agents.plugin import register_all
        from agent_platform.core.registry import get_registry

        # Reset registry
        registry = get_registry()
        registry._agents.clear()
        registry._metadata.clear()

        # Register agents
        register_all()

        result = main(["list"])

        assert result == 0
        captured = capsys.readouterr()
        assert "be" in captured.out
        assert "orch" in captured.out
