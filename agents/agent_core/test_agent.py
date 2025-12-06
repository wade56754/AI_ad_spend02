from pathlib import Path
from typing import Dict, Any, Optional
import logging

from agent_platform.core.protocol import AgentProtocol, AgentContext
from ..tools.types import AgentResponse

logger = logging.getLogger(__name__)


class TestAgent(AgentProtocol):
    """
    TestAgent：统一对接两类测试 Skill

    - mode="db"（默认）：
        生成 Supabase MCP 使用的数据库不变量测试提示词（db_test_skill）
    - mode="backend"：
        生成后端 pytest 测试流程的提示词（backend_test_skill）

    注意：本 Agent 不直接执行测试，只负责生成提示词。
    返回值中的 executed 字段始终为 False。
    """

    def __init__(
        self,
        base_path: Optional[Path] = None,
        project_id: Optional[str] = None,
    ) -> None:
        self.base_path = base_path or Path(__file__).resolve().parent.parent.parent
        self.project_id = project_id

    # ------------------------------------------------------------------ #
    # AgentProtocol Properties
    # ------------------------------------------------------------------ #

    @property
    def name(self) -> str:
        """Agent unique identifier."""
        return "test"

    @property
    def description(self) -> str:
        """Agent description."""
        return "Test prompt generator for DB invariants and backend pytest"

    @property
    def version(self) -> str:
        """Agent version."""
        return "1.0.0"

    # ------------------------------------------------------------------ #
    # Main Entry Point
    # ------------------------------------------------------------------ #

    def handle_request(
        self,
        request: Dict[str, Any],
        context: Optional[AgentContext] = None,
    ) -> AgentResponse:
        """
        处理测试请求（符合 AgentProtocol）。

        Args:
            request: 请求字典，可包含：
                - mode: "db" | "backend"（默认 "db"）
                - scope: backend 测试范围（仅 mode="backend" 时使用）
                - level: backend 测试级别（仅 mode="backend" 时使用）

        Returns:
            {
                "success": bool,        # True = prompt 生成成功，不代表测试已执行或通过
                "data": {
                    "prompt": str,       # 给 MCP / 人类使用的提示词
                    "status": str,       # "prompt_generated" | "executed" | "failed"
                    "executed": bool,    # 是否已执行测试（当前版本始终为 False）
                    "reason": str,       # 未执行原因说明（人类可读）
                    ...                  # 其他元信息（mode/scope/level）
                },
                "error": Optional[str]
            }

        Note:
            当前版本只生成 prompt，不直接执行测试。
            success=True 表示「prompt 生成成功」，而非「测试通过」。
            调用方应检查 data.status 和 data.executed 字段判断实际状态。
        """
        mode = (
            request.get("mode")
            or request.get("kind")
            or request.get("action")
            or "db"
        )
        mode = str(mode).lower().strip()

        # Ensure context exists for run_id tracking
        if context is None:
            context = AgentContext()

        if mode in ("db", "db_test", "db_invariants"):
            return self._handle_db_test(request, context)
        elif mode in ("backend", "backend_tests", "backend_pytest"):
            return self._handle_backend_test(request, context)
        else:
            msg = f"Unsupported test mode: {mode}"
            logger.error(msg)
            return {
                "success": False,
                "data": {
                    "status": "failed",
                    "executed": False,
                    "meta": {
                        "run_id": context.run_id,
                        "agent": self.name,
                        "version": self.version,
                    },
                },
                "error": msg,
            }

    # ------- DB 测试（原有逻辑抽出来） -------

    def _handle_db_test(
        self,
        request: Dict[str, Any],
        context: AgentContext,
    ) -> AgentResponse:
        from ..skills.db_test_skill import db_test_skill

        logger.info("Test Agent generating DB test prompt")

        # TODO: 预留参数透传位点，未来可扩展 db_test_skill 签名
        # target = request.get("target")  # e.g., "supabase" | "local"
        # env = request.get("env")        # e.g., "test" | "staging"
        # result = db_test_skill(target=target, env=env)
        result = db_test_skill()

        # Clarify that tests were NOT executed (only prompt was generated)
        # success=True 仅表示 prompt 生成成功，不代表测试已执行或通过
        if result["success"]:
            prompt = result["data"]["prompt"]
            prompt_len = len(prompt)
            logger.info(f"Test Agent completed: DB test prompt generated ({prompt_len} chars)")
            return {
                "success": True,
                "data": {
                    "prompt": prompt,
                    # status 字段：明确语义，避免 success=True 被误解为「测试通过」
                    "status": "prompt_generated",
                    "executed": False,  # Always False until actual MCP integration
                    "reason": (
                        "[NOT EXECUTED] DB 测试 prompt 已生成，但测试尚未执行。"
                        "需要配置 Supabase MCP 或手动运行 prompt 中的 SQL 查询。"
                    ),
                    "mode": "db",
                    "meta": {
                        "run_id": context.run_id,
                        "agent": self.name,
                        "version": self.version,
                        "skill_used": "db_test_skill",
                    },
                },
                "error": None,
            }
        else:
            logger.error(f"DB Test Skill failed: {result.get('error')}")
            return {
                "success": False,
                "data": {
                    "status": "failed",
                    "executed": False,
                    "reason": "DB test skill 执行失败，prompt 未生成",
                    "mode": "db",
                    "meta": {
                        "run_id": context.run_id,
                        "agent": self.name,
                        "version": self.version,
                        "skill_used": "db_test_skill",
                    },
                },
                "error": result.get("error") or "db_test_skill failed",
            }

    # ------- Backend pytest 测试（新逻辑） -------

    def _handle_backend_test(
        self,
        request: Dict[str, Any],
        context: AgentContext,
    ) -> AgentResponse:
        from ..skills.backend_test_skill import backend_test_skill

        scope = (request.get("scope") or "all").lower()
        level = (request.get("level") or "full").lower()

        logger.info(
            f"Test Agent generating Backend pytest test prompt "
            f"(scope={scope}, level={level})"
        )

        result = backend_test_skill(scope=scope, level=level)

        # success=True 仅表示 prompt 生成成功，不代表测试已执行或通过
        if result["success"]:
            prompt = result["data"]["prompt"]
            prompt_len = len(prompt)
            logger.info(
                f"Test Agent completed: Backend test prompt generated "
                f"({prompt_len} chars, scope={scope}, level={level})"
            )
            return {
                "success": True,
                "data": {
                    "prompt": prompt,
                    # status 字段：明确语义，避免 success=True 被误解为「测试通过」
                    "status": "prompt_generated",
                    "executed": False,
                    "reason": (
                        "[NOT EXECUTED] Backend pytest prompt 已生成，但测试尚未执行。"
                        "需要在 backend/ 目录下通过 shell 或 MCP 运行 pytest 命令。"
                    ),
                    "mode": "backend",
                    "scope": scope,
                    "level": level,
                    "meta": {
                        "run_id": context.run_id,
                        "agent": self.name,
                        "version": self.version,
                        "skill_used": "backend_test_skill",
                    },
                },
                "error": None,
            }
        else:
            logger.error(f"Backend Test Skill failed: {result.get('error')}")
            return {
                "success": False,
                "data": {
                    "status": "failed",
                    "executed": False,
                    "reason": "Backend test skill 执行失败，prompt 未生成",
                    "mode": "backend",
                    "scope": scope,
                    "level": level,
                    "meta": {
                        "run_id": context.run_id,
                        "agent": self.name,
                        "version": self.version,
                        "skill_used": "backend_test_skill",
                    },
                },
                "error": result.get("error") or "backend_test_skill failed",
            }
