"""
TestAgent - Test Generation and Execution Prompt Agent

Phase 3.0A: Migrated to AgentProtocol + Registry system.

Orchestrates test prompt generation by delegating to db_test_skill or backend_test_skill.
Does NOT directly execute tests; generates prompts for MCP/shell/human execution.

Returns:
    success=True indicates prompt was generated successfully (NOT that tests passed).
    Check data.executed and data.status for actual execution state.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import logging

from agent_platform.core.protocol import AgentProtocol, AgentContext
from ..tools.types import AgentResponse

logger = logging.getLogger(__name__)


class TestAgent(AgentProtocol):
    """
    Test Generation and Execution Prompt Agent.

    Unified interface for two types of test skills:
    - mode="db" (default): Generates Supabase MCP database invariant test prompts
    - mode="backend": Generates backend pytest execution prompts

    Request Fields:
        - mode: "db" | "backend" (default: "db")
        - scope: Backend test scope, e.g., "ledger" | "topups" | "all" (backend mode only)
        - level: Backend test level, "quick" | "full" (backend mode only)
        - target_module: Optional target module name for focused testing
        - target_tests: Optional list of specific test files/functions

    Response Fields:
        - data.prompt: Generated prompt for MCP/shell/human execution
        - data.status: "prompt_generated" | "executed" | "failed"
        - data.executed: Whether tests were actually executed (always False in current version)
        - data.reason: Human-readable explanation of status
        - data.meta: Metadata including run_id, agent, version

    Note:
        success=True means prompt generation succeeded, NOT that tests passed.
        Check data.executed and data.status for actual execution state.
    """

    def __init__(self, base_path: Optional[Path] = None) -> None:
        """
        Initialize Test Agent.

        Args:
            base_path: Project root directory (defaults to auto-detected path)
        """
        self.base_path = (
            base_path
            if base_path is not None
            else Path(__file__).resolve().parent.parent.parent
        )

    @property
    def name(self) -> str:
        """Agent unique identifier."""
        return "test"

    @property
    def description(self) -> str:
        """Agent description."""
        return "Test prompt generation for pytest and database invariant validation"

    @property
    def version(self) -> str:
        """Agent version."""
        return "1.0.0"

    def handle_request(
        self,
        request: Dict[str, Any],
        context: Optional[AgentContext] = None,
    ) -> AgentResponse:
        """
        Process test generation request.

        Args:
            request: Request dictionary with fields:
                - mode: "db" | "backend" (default: "db")
                - scope: Backend test scope (backend mode only)
                - level: Backend test level (backend mode only)
                - target_module: Optional target module
                - target_tests: Optional list of test files
            context: Optional execution context for tracing (auto-created if None)

        Returns:
            AgentResponse with generated prompt and metadata
        """
        # Phase 3.0A: Ensure context exists for tracing
        context = context or AgentContext()
        run_id = context.run_id

        mode = (
            request.get("mode")
            or request.get("kind")
            or request.get("action")
            or "db"
        )
        mode = str(mode).lower().strip()

        logger.info(f"[run_id={run_id}] Test Agent processing mode: {mode}")

        if mode in ("db", "db_test", "db_invariants"):
            return self._handle_db_test(request, run_id)
        elif mode in ("backend", "backend_tests", "backend_pytest"):
            return self._handle_backend_test(request, run_id)
        else:
            msg = f"Unsupported test mode: {mode}"
            logger.error(f"[run_id={run_id}] {msg}")
            return {
                "success": False,
                "data": {
                    "meta": {
                        "run_id": run_id,
                        "agent": self.name,
                        "version": self.version,
                        "skill_used": None,
                    },
                },
                "error": msg,
            }

    def _handle_db_test(self, request: Dict[str, Any], run_id: str) -> AgentResponse:
        """Handle DB invariant test prompt generation."""
        from ..skills.db_test_skill import db_test_skill

        logger.info(f"[run_id={run_id}] Test Agent generating DB test prompt")

        result = db_test_skill()

        if result["success"]:
            prompt = result["data"]["prompt"]
            prompt_len = len(prompt)
            logger.info(f"[run_id={run_id}] Test Agent completed: DB test prompt ({prompt_len} chars)")

            return {
                "success": True,
                "data": {
                    "prompt": prompt,
                    "status": "prompt_generated",
                    "executed": False,
                    "reason": (
                        "[NOT EXECUTED] DB 测试 prompt 已生成，但测试尚未执行。"
                        "需要配置 Supabase MCP 或手动运行 prompt 中的 SQL 查询。"
                    ),
                    "mode": "db",
                    "meta": {
                        "run_id": run_id,
                        "agent": self.name,
                        "version": self.version,
                        "skill_used": "db_test_skill",
                    },
                },
                "error": None,
            }
        else:
            logger.error(f"[run_id={run_id}] DB Test Skill failed: {result.get('error')}")
            return {
                "success": False,
                "data": {
                    "status": "failed",
                    "executed": False,
                    "reason": "DB test skill 执行失败，prompt 未生成",
                    "mode": "db",
                    "meta": {
                        "run_id": run_id,
                        "agent": self.name,
                        "version": self.version,
                        "skill_used": "db_test_skill",
                    },
                },
                "error": result.get("error") or "db_test_skill failed",
            }

    def _handle_backend_test(self, request: Dict[str, Any], run_id: str) -> AgentResponse:
        """Handle backend pytest prompt generation."""
        from ..skills.backend_test_skill import backend_test_skill

        scope = (request.get("scope") or "all").lower()
        level = (request.get("level") or "full").lower()
        target_module = request.get("target_module")
        target_tests = request.get("target_tests", [])

        logger.info(
            f"[run_id={run_id}] Test Agent generating Backend pytest prompt "
            f"(scope={scope}, level={level})"
        )

        result = backend_test_skill(scope=scope, level=level)

        if result["success"]:
            prompt = result["data"]["prompt"]
            prompt_len = len(prompt)
            logger.info(
                f"[run_id={run_id}] Test Agent completed: Backend test prompt "
                f"({prompt_len} chars, scope={scope}, level={level})"
            )

            return {
                "success": True,
                "data": {
                    "prompt": prompt,
                    "status": "prompt_generated",
                    "executed": False,
                    "reason": (
                        "[NOT EXECUTED] Backend pytest prompt 已生成，但测试尚未执行。"
                        "需要在 backend/ 目录下通过 shell 或 MCP 运行 pytest 命令。"
                    ),
                    "mode": "backend",
                    "scope": scope,
                    "level": level,
                    "target_module": target_module,
                    "target_tests": target_tests,
                    "meta": {
                        "run_id": run_id,
                        "agent": self.name,
                        "version": self.version,
                        "skill_used": "backend_test_skill",
                    },
                },
                "error": None,
            }
        else:
            logger.error(f"[run_id={run_id}] Backend Test Skill failed: {result.get('error')}")
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
                        "run_id": run_id,
                        "agent": self.name,
                        "version": self.version,
                        "skill_used": "backend_test_skill",
                    },
                },
                "error": result.get("error") or "backend_test_skill failed",
            }
