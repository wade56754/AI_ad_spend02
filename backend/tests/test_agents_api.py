"""
Agent Platform API 测试
Version: 1.1
Author: Claude Code (AI 代码工厂)

SoT References:
- API_SOT.md v9.0 第12H章 Agents API
- AUTH_SPEC.md v2.0 (角色权限 - admin only)

注意: Agents API 依赖 agent_platform 模块，测试时需要 mock 相关依赖
"""

import pytest
import sys
from unittest.mock import patch, MagicMock, Mock


# ============================================================================
# Mock agent_platform 模块（在导入 router 之前）
# ============================================================================

# 创建 mock 模块结构
mock_agent_platform = MagicMock()
mock_registry_module = MagicMock()
mock_protocol_module = MagicMock()

# 设置 mock agent metadata
mock_be_meta = Mock()
mock_be_meta.name = "be"
mock_be_meta.version = "1.0.0"
mock_be_meta.description = "Backend Agent for code generation"
mock_be_meta.tags = ["backend", "code-gen"]

mock_fe_meta = Mock()
mock_fe_meta.name = "fe"
mock_fe_meta.version = "1.0.0"
mock_fe_meta.description = "Frontend Agent"
mock_fe_meta.tags = ["frontend"]

# 设置 list_agents 返回值
mock_registry_module.list_agents.return_value = [mock_be_meta, mock_fe_meta]

# 设置 get_registry 返回值
mock_registry = Mock()
mock_registry.count = 2
mock_registry.get_agent_metadata.return_value = mock_be_meta
mock_registry.list_agents.return_value = [mock_be_meta, mock_fe_meta]
mock_registry_module.get_registry.return_value = mock_registry

# 设置 create_agent
mock_agent = Mock()
mock_agent.handle_request.return_value = {"success": True, "data": {"result": "ok"}}
mock_registry_module.create_agent.return_value = mock_agent

# 设置 AgentContext
mock_context = Mock()
mock_context.run_id = "test-run-123"
mock_protocol_module.AgentContext.return_value = mock_context

# 设置 agents.plugin
mock_agents_plugin = MagicMock()
mock_agents_plugin.register_all.return_value = None

# 注入 mock 模块到 sys.modules
sys.modules['agent_platform'] = mock_agent_platform
sys.modules['agent_platform.core'] = MagicMock()
sys.modules['agent_platform.core.registry'] = mock_registry_module
sys.modules['agent_platform.core.protocol'] = mock_protocol_module
sys.modules['agents'] = MagicMock()
sys.modules['agents.plugin'] = mock_agents_plugin


class TestAgentsList:
    """Agent 列表 API 测试"""

    def test_list_agents_success(self, client, admin_headers):
        """测试获取 Agent 列表 - 成功"""
        response = client.get("/api/v1/agents", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "agents" in data["data"]
        assert "count" in data["data"]
        assert data["data"]["count"] >= 1

    def test_list_agents_returns_metadata(self, client, admin_headers):
        """测试获取 Agent 列表 - 验证元数据结构"""
        response = client.get("/api/v1/agents", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()

        # 验证 agent 元数据结构
        if data["data"]["count"] > 0:
            agent = data["data"]["agents"][0]
            assert "name" in agent
            assert "version" in agent
            assert "description" in agent
            assert "tags" in agent


class TestAgentGet:
    """Agent 详情 API 测试"""

    def test_get_agent_success(self, client, admin_headers):
        """测试获取 Agent 详情 - 成功"""
        response = client.get("/api/v1/agents/be", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "be"

    def test_get_agent_not_found(self, client, admin_headers):
        """测试获取 Agent 详情 - 不存在"""
        # 修改 mock 使其返回 None
        mock_registry.get_agent_metadata.return_value = None

        response = client.get("/api/v1/agents/nonexistent", headers=admin_headers)

        assert response.status_code == 404

        # 恢复 mock
        mock_registry.get_agent_metadata.return_value = mock_be_meta


class TestAgentRun:
    """Agent 执行 API 测试"""

    def test_run_agent_success(self, client, admin_headers):
        """测试执行 Agent - 成功"""
        # 确保 mock 返回成功
        mock_agent.handle_request.return_value = {
            "success": True,
            "data": {"generated_code": "..."}
        }

        request_body = {
            "agent": "be",
            "request": {
                "task": "Generate API endpoint",
                "target_files": ["routers/test.py"]
            }
        }

        response = client.post(
            "/api/v1/agents/run",
            json=request_body,
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "run_id" in data["data"]

    def test_run_agent_not_found(self, client, admin_headers):
        """测试执行 Agent - Agent 不存在"""
        # 修改 mock 使其抛出异常
        mock_registry_module.create_agent.side_effect = ValueError("Agent 'unknown' not found")

        request_body = {
            "agent": "unknown",
            "request": {}
        }

        response = client.post(
            "/api/v1/agents/run",
            json=request_body,
            headers=admin_headers
        )

        assert response.status_code == 404

        # 恢复 mock
        mock_registry_module.create_agent.side_effect = None
        mock_registry_module.create_agent.return_value = mock_agent

    def test_run_agent_execution_error(self, client, admin_headers):
        """测试执行 Agent - 执行错误"""
        # 修改 mock 使其抛出异常
        mock_agent.handle_request.side_effect = Exception("Execution failed")

        request_body = {
            "agent": "be",
            "request": {"task": "test"}
        }

        response = client.post(
            "/api/v1/agents/run",
            json=request_body,
            headers=admin_headers
        )

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False

        # 恢复 mock
        mock_agent.handle_request.side_effect = None
        mock_agent.handle_request.return_value = {"success": True, "data": {}}

    def test_run_agent_missing_agent_field(self, client, admin_headers):
        """测试执行 Agent - 缺少 agent 字段"""
        request_body = {
            "request": {"task": "test"}
        }

        response = client.post(
            "/api/v1/agents/run",
            json=request_body,
            headers=admin_headers
        )

        assert response.status_code == 422  # Validation error

    def test_run_agent_failure_response(self, client, admin_headers):
        """测试执行 Agent - 执行返回失败"""
        mock_agent.handle_request.return_value = {
            "success": False,
            "error": "Task failed"
        }

        request_body = {
            "agent": "be",
            "request": {"task": "failing task"}
        }

        response = client.post(
            "/api/v1/agents/run",
            json=request_body,
            headers=admin_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

        # 恢复 mock
        mock_agent.handle_request.return_value = {"success": True, "data": {}}


class TestOrchestratorRun:
    """Orchestrator 执行 API 测试"""

    def test_run_orchestrator_success(self, client, admin_headers):
        """测试执行 Orchestrator - 成功"""
        # 设置 orchestrator mock
        mock_orch = Mock()
        mock_orch.handle_request.return_value = {
            "success": True,
            "data": {
                "steps_completed": 2,
                "artifacts": []
            }
        }
        mock_registry_module.create_agent.return_value = mock_orch

        request_body = {
            "flow": "be_then_test",
            "task": "Implement new API",
            "target_files": ["routers/new_api.py"],
            "module": "new_api",
            "mode": "dry-run"
        }

        response = client.post(
            "/api/v1/agents/orch",
            json=request_body,
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["flow"] == "be_then_test"
        assert data["data"]["mode"] == "dry-run"

        # 恢复 mock
        mock_registry_module.create_agent.return_value = mock_agent

    def test_run_orchestrator_not_available(self, client, admin_headers):
        """测试执行 Orchestrator - Orchestrator 不可用"""
        mock_registry_module.create_agent.side_effect = ValueError("Cannot create orchestrator")

        request_body = {
            "flow": "be_then_test"
        }

        response = client.post(
            "/api/v1/agents/orch",
            json=request_body,
            headers=admin_headers
        )

        assert response.status_code == 500

        # 恢复 mock
        mock_registry_module.create_agent.side_effect = None
        mock_registry_module.create_agent.return_value = mock_agent

    def test_run_orchestrator_flow_failed(self, client, admin_headers):
        """测试执行 Orchestrator - 流程失败"""
        mock_orch = Mock()
        mock_orch.handle_request.return_value = {
            "success": False,
            "error": "Step 2 failed"
        }
        mock_registry_module.create_agent.return_value = mock_orch

        request_body = {
            "flow": "full_pipeline",
            "mode": "execute"
        }

        response = client.post(
            "/api/v1/agents/orch",
            json=request_body,
            headers=admin_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

        # 恢复 mock
        mock_registry_module.create_agent.return_value = mock_agent

    def test_run_orchestrator_missing_flow(self, client, admin_headers):
        """测试执行 Orchestrator - 缺少 flow 字段"""
        request_body = {
            "task": "test task"
        }

        response = client.post(
            "/api/v1/agents/orch",
            json=request_body,
            headers=admin_headers
        )

        assert response.status_code == 422  # Validation error

    def test_run_orchestrator_execute_mode(self, client, admin_headers):
        """测试执行 Orchestrator - execute 模式"""
        mock_orch = Mock()
        mock_orch.handle_request.return_value = {
            "success": True,
            "data": {"files_written": 3}
        }
        mock_registry_module.create_agent.return_value = mock_orch

        request_body = {
            "flow": "backend_only",
            "mode": "execute"  # 非 dry-run
        }

        response = client.post(
            "/api/v1/agents/orch",
            json=request_body,
            headers=admin_headers
        )

        assert response.status_code == 200

        # 验证 auto_write 被设置为 True
        call_args = mock_orch.handle_request.call_args[0][0]
        assert call_args.get("auto_write") is True

        # 恢复 mock
        mock_registry_module.create_agent.return_value = mock_agent
