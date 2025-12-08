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
        """TestAgent should generate prompt with executed=False.

        P1-03 增强：验证 prompt 具有实质内容和关键结构。
        """
        test_agent = create_agent("test")
        response = test_agent.handle_request({})

        # 基本响应结构验证
        assert response["success"] is True
        assert response["data"] is not None
        assert response["data"]["executed"] is False
        assert "prompt" in response["data"]

        prompt = response["data"]["prompt"]

        # P1-03: 验证 prompt 最小长度（防止空壳模板）
        # 正常 prompt 应包含 ROLE/CONTEXT/TASK/OUTPUT_FORMAT 等结构，至少数百字符
        assert len(prompt) >= 200, f"Prompt too short ({len(prompt)} chars), expected >= 200"

        # P1-03: 验证 prompt 包含关键结构片段（结构性检查，非逐行匹配）
        # 这些关键词来自 db_test_skill.py 生成的 prompt 模板
        structural_keywords = [
            "Supabase",        # 目标执行环境
            "SQL",             # 测试类型标识
        ]

        for keyword in structural_keywords:
            assert keyword in prompt, f"Prompt missing structural keyword: '{keyword}'"

        # P1-03: 验证 prompt 包含至少一个业务关键词（确保业务上下文存在）
        business_keywords = ["数据库", "测试", "不变量", "invariant", "test"]
        has_business_keyword = any(kw.lower() in prompt.lower() for kw in business_keywords)
        assert has_business_keyword, f"Prompt missing business context keywords"


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


class TestAutoFixFlow:
    """Tests for auto_fix flow (P1-01 fix)."""

    def test_missing_target_returns_error(self):
        """auto_fix flow should return error when target is missing."""
        orch_agent = create_agent("orch")
        response = orch_agent.handle_request({
            "flow": "auto_fix",
            "task": "test task",
            "target_files": ["file.py"],
        })

        assert response["success"] is False
        assert "target" in response["error"].lower()

    def test_invalid_target_returns_error(self):
        """auto_fix flow should return error for invalid target."""
        orch_agent = create_agent("orch")
        response = orch_agent.handle_request({
            "flow": "auto_fix",
            "target": "invalid",
            "task": "test task",
            "target_files": ["file.py"],
        })

        assert response["success"] is False
        assert "backend" in response["error"].lower() or "frontend" in response["error"].lower()

    def test_missing_task_returns_error(self):
        """auto_fix flow should return error when task is missing."""
        orch_agent = create_agent("orch")
        response = orch_agent.handle_request({
            "flow": "auto_fix",
            "target": "backend",
            "target_files": ["file.py"],
        })

        assert response["success"] is False
        assert "task" in response["error"].lower()

    def test_missing_target_files_returns_error(self):
        """auto_fix flow should return error when target_files is missing."""
        orch_agent = create_agent("orch")
        response = orch_agent.handle_request({
            "flow": "auto_fix",
            "target": "backend",
            "task": "test task",
        })

        assert response["success"] is False
        assert "target_files" in response["error"].lower()

    def test_success_on_first_iteration(self, monkeypatch):
        """auto_fix should succeed when first iteration passes."""
        def mock_be_handle_request(self, request):
            return {"success": True, "data": {"changes": {"file.py": "code"}}, "error": None}

        def mock_test_handle_request(self, request):
            return {"success": True, "data": {"prompt": "test", "executed": False}, "error": None}

        from agents.agent_core.be_agent import BEAgent
        from agents.agent_core.test_agent import TestAgent

        monkeypatch.setattr(BEAgent, "handle_request", mock_be_handle_request)
        monkeypatch.setattr(TestAgent, "handle_request", mock_test_handle_request)

        orch_agent = create_agent("orch")
        response = orch_agent.handle_request({
            "flow": "auto_fix",
            "target": "backend",
            "task": "test task",
            "target_files": ["file.py"],
        })

        assert response["success"] is True
        assert "gen_iter_1" in response["data"]["steps"]
        assert "test_iter_1" in response["data"]["steps"]
        assert response["data"]["steps"]["summary"]["data"]["iterations"] == 1
        assert response["data"]["steps"]["summary"]["data"]["test_passed"] is True

    def test_respects_max_retries(self, monkeypatch):
        """auto_fix should stop after max_retries iterations."""
        call_count = {"gen": 0, "test": 0}

        def mock_be_handle_request(self, request):
            call_count["gen"] += 1
            return {"success": True, "data": {"changes": {"file.py": "code"}}, "error": None}

        def mock_test_handle_request(self, request):
            call_count["test"] += 1
            return {"success": False, "data": None, "error": "Test failed"}

        from agents.agent_core.be_agent import BEAgent
        from agents.agent_core.test_agent import TestAgent

        monkeypatch.setattr(BEAgent, "handle_request", mock_be_handle_request)
        monkeypatch.setattr(TestAgent, "handle_request", mock_test_handle_request)

        orch_agent = create_agent("orch")
        response = orch_agent.handle_request({
            "flow": "auto_fix",
            "target": "backend",
            "task": "test task",
            "target_files": ["file.py"],
            "max_retries": 2,  # 2 retries = 3 total iterations
        })

        assert response["success"] is False
        assert call_count["gen"] == 3  # Initial + 2 retries
        assert call_count["test"] == 3
        assert response["data"]["steps"]["summary"]["data"]["iterations"] == 3

    def test_accumulates_fix_context(self, monkeypatch):
        """auto_fix should accumulate fix context across iterations."""
        received_tasks = []

        def mock_be_handle_request(self, request):
            received_tasks.append(request.get("task", ""))
            return {"success": True, "data": {"changes": {"file.py": "code"}}, "error": None}

        def mock_test_handle_request(self, request):
            # Fail first time, succeed second time
            if len(received_tasks) == 1:
                return {"success": False, "data": None, "error": "Type error on line 5"}
            return {"success": True, "data": {"prompt": "ok", "executed": False}, "error": None}

        from agents.agent_core.be_agent import BEAgent
        from agents.agent_core.test_agent import TestAgent

        monkeypatch.setattr(BEAgent, "handle_request", mock_be_handle_request)
        monkeypatch.setattr(TestAgent, "handle_request", mock_test_handle_request)

        orch_agent = create_agent("orch")
        response = orch_agent.handle_request({
            "flow": "auto_fix",
            "target": "backend",
            "task": "original task",
            "target_files": ["file.py"],
            "max_retries": 3,
        })

        assert response["success"] is True
        assert len(received_tasks) == 2

        # Second task should contain fix context
        assert "Auto-Fix Context" in received_tasks[1]
        assert "Type error" in received_tasks[1]

    def test_uses_frontend_agent_for_frontend_target(self, monkeypatch):
        """auto_fix should use FEAgent when target is frontend."""
        fe_called = {"value": False}
        be_called = {"value": False}

        def mock_be_handle_request(self, request):
            be_called["value"] = True
            return {"success": True, "data": {"changes": {}}, "error": None}

        def mock_fe_handle_request(self, request):
            fe_called["value"] = True
            return {"success": True, "data": {"changes": {"file.tsx": "code"}}, "error": None}

        def mock_test_handle_request(self, request):
            return {"success": True, "data": {"prompt": "ok", "executed": False}, "error": None}

        from agents.agent_core.be_agent import BEAgent
        from agents.agent_core.fe_agent import FEAgent
        from agents.agent_core.test_agent import TestAgent

        monkeypatch.setattr(BEAgent, "handle_request", mock_be_handle_request)
        monkeypatch.setattr(FEAgent, "handle_request", mock_fe_handle_request)
        monkeypatch.setattr(TestAgent, "handle_request", mock_test_handle_request)

        orch_agent = create_agent("orch")
        response = orch_agent.handle_request({
            "flow": "auto_fix",
            "target": "frontend",
            "task": "test task",
            "target_files": ["file.tsx"],
        })

        assert response["success"] is True
        assert fe_called["value"] is True
        assert be_called["value"] is False

    def test_summary_contains_expected_fields(self, monkeypatch):
        """auto_fix summary should contain all expected fields."""
        def mock_be_handle_request(self, request):
            return {"success": True, "data": {"changes": {"file.py": "code"}}, "error": None}

        def mock_test_handle_request(self, request):
            return {"success": True, "data": {"prompt": "ok", "executed": False}, "error": None}

        from agents.agent_core.be_agent import BEAgent
        from agents.agent_core.test_agent import TestAgent

        monkeypatch.setattr(BEAgent, "handle_request", mock_be_handle_request)
        monkeypatch.setattr(TestAgent, "handle_request", mock_test_handle_request)

        orch_agent = create_agent("orch")
        response = orch_agent.handle_request({
            "flow": "auto_fix",
            "target": "backend",
            "task": "test task",
            "target_files": ["file.py"],
            "max_retries": 2,
        })

        summary = response["data"]["steps"]["summary"]["data"]
        assert "target" in summary
        assert "iterations" in summary
        assert "max_retries" in summary
        assert "test_passed" in summary
        assert "files_generated" in summary
        assert "files_written" in summary
        assert "auto_write" in summary

        assert summary["target"] == "backend"
        assert summary["max_retries"] == 2
        assert summary["auto_write"] is False  # Default

    def test_no_infinite_loop_on_continuous_failure(self, monkeypatch):
        """auto_fix should not loop infinitely even if tests always fail."""
        iteration_count = {"value": 0}

        def mock_be_handle_request(self, request):
            iteration_count["value"] += 1
            if iteration_count["value"] > 100:
                raise RuntimeError("Infinite loop detected!")
            return {"success": True, "data": {"changes": {"file.py": "code"}}, "error": None}

        def mock_test_handle_request(self, request):
            return {"success": False, "data": None, "error": "Always fails"}

        from agents.agent_core.be_agent import BEAgent
        from agents.agent_core.test_agent import TestAgent

        monkeypatch.setattr(BEAgent, "handle_request", mock_be_handle_request)
        monkeypatch.setattr(TestAgent, "handle_request", mock_test_handle_request)

        orch_agent = create_agent("orch")
        response = orch_agent.handle_request({
            "flow": "auto_fix",
            "target": "backend",
            "task": "test task",
            "target_files": ["file.py"],
            "max_retries": 5,
        })

        assert response["success"] is False
        assert iteration_count["value"] == 6  # 1 initial + 5 retries
        assert iteration_count["value"] < 100  # Not infinite
