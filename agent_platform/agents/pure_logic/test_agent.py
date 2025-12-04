"""
TestAgentPure - MCP 安全的测试 Agent

Phase 2: 从 agents/agent_core/test_agent.py 迁移

功能:
- 生成 DB 测试提示词（db_test_skill）
- 生成 Backend pytest 测试提示词（backend_test_skill）
- 不直接执行测试，只生成提示词供 MCP/人工使用

MCP 安全性:
- mcp_safe=True: 不调用 LLM
- 所有操作都是文件读取和提示词组装

基准对齐:
- AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md Phase 2
- Agent Layer Freeze v1.0
"""

from pathlib import Path
from typing import Dict, Any, Optional
import logging

from agent_platform.core.protocol import AgentProtocol, AgentContext
from agent_platform.core.registry import register_agent

logger = logging.getLogger(__name__)


class TestAgentPure(AgentProtocol):
    """
    MCP 安全的测试 Agent

    生成测试提示词，不执行测试。
    - mode="db": 生成 DB 不变量测试提示词
    - mode="backend": 生成 Backend pytest 提示词
    """

    def __init__(self, base_path: Optional[Path] = None) -> None:
        self._base_path = base_path or Path.cwd()

    @property
    def name(self) -> str:
        return "test"

    @property
    def description(self) -> str:
        return "测试提示词生成 Agent（MCP 安全，不执行测试）"

    @property
    def version(self) -> str:
        return "2.0.0"  # Phase 2 版本

    def handle_request(
        self,
        request: Dict[str, Any],
        context: Optional[AgentContext] = None,
    ) -> Dict[str, Any]:
        """
        处理测试请求。

        Args:
            request: 请求字典，可包含：
                - mode: "db" | "backend"（默认 "db"）
                - scope: backend 测试范围
                - level: backend 测试级别

        Returns:
            {
                "success": bool,
                "data": {
                    "prompt": str,
                    "status": "prompt_generated",
                    "executed": False,  # 始终为 False
                    "reason": str,
                    "mode": str,
                },
                "error": Optional[str]
            }
        """
        context = context or AgentContext()
        run_id = context.run_id

        mode = (
            request.get("mode")
            or request.get("kind")
            or request.get("action")
            or "db"
        )
        mode = str(mode).lower().strip()

        logger.info(f"[run_id={run_id}] TestAgentPure: mode={mode}")

        if mode in ("db", "db_test", "db_invariants"):
            return self._handle_db_test(request, run_id)
        elif mode in ("backend", "backend_tests", "backend_pytest"):
            return self._handle_backend_test(request, run_id)
        else:
            return {
                "success": False,
                "data": {
                    "status": "failed",
                    "executed": False,
                    "reason": f"Unsupported test mode: {mode}",
                    "mode": mode,
                },
                "error": f"Unsupported test mode: {mode}. Use 'db' or 'backend'.",
            }

    def _handle_db_test(
        self, request: Dict[str, Any], run_id: str
    ) -> Dict[str, Any]:
        """处理 DB 测试请求"""
        try:
            # 延迟导入以避免循环依赖
            from agents.skills.db_test_skill import db_test_skill

            logger.info(f"[run_id={run_id}] Generating DB test prompt")
            result = db_test_skill()

            if result["success"]:
                prompt = result["data"]["prompt"]
                logger.info(
                    f"[run_id={run_id}] DB test prompt generated ({len(prompt)} chars)"
                )
                return {
                    "success": True,
                    "data": {
                        "prompt": prompt,
                        "status": "prompt_generated",
                        "executed": False,
                        "reason": (
                            "[NOT EXECUTED] DB 测试 prompt 已生成。"
                            "需要配置 Supabase MCP 或手动运行 SQL 查询。"
                        ),
                        "mode": "db",
                        "meta": {"run_id": run_id, "agent": self.name},
                    },
                    "error": None,
                }
            else:
                return {
                    "success": False,
                    "data": {
                        "status": "failed",
                        "executed": False,
                        "reason": "DB test skill 执行失败",
                        "mode": "db",
                    },
                    "error": result.get("error", "db_test_skill failed"),
                }
        except ImportError as e:
            logger.error(f"[run_id={run_id}] Import error: {e}")
            return {
                "success": False,
                "data": {"status": "failed", "executed": False, "mode": "db"},
                "error": f"Cannot import db_test_skill: {e}",
            }

    def _handle_backend_test(
        self, request: Dict[str, Any], run_id: str
    ) -> Dict[str, Any]:
        """处理 Backend pytest 测试请求"""
        try:
            from agents.skills.backend_test_skill import backend_test_skill

            scope = (request.get("scope") or "all").lower()
            level = (request.get("level") or "full").lower()

            logger.info(
                f"[run_id={run_id}] Generating Backend test prompt "
                f"(scope={scope}, level={level})"
            )
            result = backend_test_skill(scope=scope, level=level)

            if result["success"]:
                prompt = result["data"]["prompt"]
                logger.info(
                    f"[run_id={run_id}] Backend test prompt generated ({len(prompt)} chars)"
                )
                return {
                    "success": True,
                    "data": {
                        "prompt": prompt,
                        "status": "prompt_generated",
                        "executed": False,
                        "reason": (
                            "[NOT EXECUTED] Backend pytest prompt 已生成。"
                            "需要通过 shell 或 MCP 运行 pytest。"
                        ),
                        "mode": "backend",
                        "scope": scope,
                        "level": level,
                        "meta": {"run_id": run_id, "agent": self.name},
                    },
                    "error": None,
                }
            else:
                return {
                    "success": False,
                    "data": {
                        "status": "failed",
                        "executed": False,
                        "mode": "backend",
                        "scope": scope,
                        "level": level,
                    },
                    "error": result.get("error", "backend_test_skill failed"),
                }
        except ImportError as e:
            logger.error(f"[run_id={run_id}] Import error: {e}")
            return {
                "success": False,
                "data": {"status": "failed", "executed": False, "mode": "backend"},
                "error": f"Cannot import backend_test_skill: {e}",
            }


# ============================================================
# 自动注册到 Registry
# ============================================================

def _test_agent_factory(base_path: Optional[Path] = None, **_: Any) -> TestAgentPure:
    """TestAgentPure 工厂函数"""
    return TestAgentPure(base_path=base_path)


# Phase 2: 注册为 mcp_safe=True
register_agent(
    name="test",
    factory=_test_agent_factory,
    description="测试提示词生成 Agent（MCP 安全）",
    version="2.0.0",
    tags=["test", "mcp_safe", "pure_logic"],
    mcp_safe=True,
    override=True,  # 覆盖旧注册（如果有）
)
