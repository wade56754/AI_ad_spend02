"""
CodeReviewAgentPure - MCP 安全的代码审核 Agent

Phase 2: 从 agents/agent_core/code_review_agent.py 迁移

功能:
- 审核代码变更是否符合 SoT 规范
- 集成 sot_guard_skill 进行 P0/P1/P2 检查
- 不调用 LLM，纯规则检查

MCP 安全性:
- mcp_safe=True: 不调用 LLM
- 所有检查都是基于规则的静态分析

基准对齐:
- AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md Phase 2
- Agent Layer Freeze v1.0
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from agent_platform.core.protocol import AgentProtocol, AgentContext
from agent_platform.core.registry import register_agent

logger = logging.getLogger(__name__)


class CodeReviewAgentPure(AgentProtocol):
    """
    MCP 安全的代码审核 Agent

    执行 SoT 一致性检查，返回违规和警告列表。
    - action="review": 完整审核（P0/P1/P2）
    - action="quick_check": 快速检查（仅 P0）
    """

    def __init__(self, base_path: Optional[Path] = None) -> None:
        self._base_path = base_path or Path.cwd()

    @property
    def name(self) -> str:
        return "review"

    @property
    def description(self) -> str:
        return "代码审核 Agent（MCP 安全，SoT 一致性检查）"

    @property
    def version(self) -> str:
        return "2.0.0"

    def handle_request(
        self,
        request: Dict[str, Any],
        context: Optional[AgentContext] = None,
    ) -> Dict[str, Any]:
        """
        处理代码审核请求。

        Args:
            request: {
                "action": "review" | "quick_check",
                "changes": Dict[str, str],  # 文件路径 -> 内容
                "context": Optional[str]
            }

        Returns:
            {
                "success": bool,
                "data": {
                    "passed": bool,
                    "violations": List[Dict],
                    "warnings": List[Dict],
                    "notes": List[str],
                },
                "error": Optional[str]
            }
        """
        context_obj = context or AgentContext()
        run_id = context_obj.run_id

        action = request.get("action", "review")
        changes = request.get("changes", {})
        ctx_info = request.get("context")

        logger.info(
            f"[run_id={run_id}] CodeReviewAgentPure: "
            f"action={action}, files={len(changes)}"
        )

        try:
            if action == "review":
                return self._full_review(changes, ctx_info, run_id)
            elif action == "quick_check":
                return self._quick_check(changes, ctx_info, run_id)
            else:
                return {
                    "success": False,
                    "data": {
                        "passed": False,
                        "violations": [],
                        "warnings": [],
                        "notes": [],
                    },
                    "error": f"Unknown action: {action}. Use 'review' or 'quick_check'.",
                }
        except Exception as e:
            logger.error(f"[run_id={run_id}] CodeReviewAgentPure error: {e}")
            return {
                "success": False,
                "data": {
                    "passed": False,
                    "violations": [],
                    "warnings": [],
                    "notes": [],
                },
                "error": str(e),
            }

    def _full_review(
        self,
        changes: Dict[str, str],
        ctx_info: Optional[str],
        run_id: str,
    ) -> Dict[str, Any]:
        """完整代码审核（P0/P1/P2）"""
        if not changes:
            return {
                "success": True,
                "data": {
                    "passed": True,
                    "violations": [],
                    "warnings": [],
                    "notes": ["没有需要审核的代码变更"],
                    "meta": {"run_id": run_id, "agent": self.name},
                },
                "error": None,
            }

        try:
            from agents.skills.sot_guard_skill import validate_against_sot

            sot_result = validate_against_sot(changes)

            passed = sot_result["passed"]
            violations = sot_result["violations"]
            warnings = sot_result["warnings"]

            notes = [
                f"审核文件数: {len(changes)}",
                f"SoT 检查: {'PASS' if passed else 'FAIL'}",
                f"P0 违规: {len(violations)}",
                f"P1/P2 警告: {len(warnings)}",
            ]

            if ctx_info:
                notes.append(f"上下文: {ctx_info}")

            logger.info(
                f"[run_id={run_id}] Review completed: "
                f"passed={passed}, P0={len(violations)}, P1/P2={len(warnings)}"
            )

            return {
                "success": True,
                "data": {
                    "passed": passed,
                    "violations": violations,
                    "warnings": warnings,
                    "notes": notes,
                    "meta": {"run_id": run_id, "agent": self.name},
                },
                "error": None,
            }

        except ImportError as e:
            logger.error(f"[run_id={run_id}] Import error: {e}")
            return {
                "success": False,
                "data": {
                    "passed": False,
                    "violations": [],
                    "warnings": [],
                    "notes": [],
                },
                "error": f"Cannot import sot_guard_skill: {e}",
            }

    def _quick_check(
        self,
        changes: Dict[str, str],
        ctx_info: Optional[str],
        run_id: str,
    ) -> Dict[str, Any]:
        """快速检查（仅 P0）"""
        if not changes:
            return {
                "success": True,
                "data": {
                    "passed": True,
                    "violations": [],
                    "warnings": [],
                    "notes": ["没有需要检查的代码变更"],
                    "meta": {"run_id": run_id, "agent": self.name},
                },
                "error": None,
            }

        try:
            from agents.skills.sot_guard_skill import validate_against_sot

            sot_result = validate_against_sot(changes)

            passed = sot_result["passed"]
            violations = sot_result["violations"]

            notes = [
                f"快速检查文件数: {len(changes)}",
                f"P0 检查: {'PASS' if passed else 'FAIL'}",
                f"P0 违规: {len(violations)}",
                "(P1/P2 跳过)",
            ]

            return {
                "success": True,
                "data": {
                    "passed": passed,
                    "violations": violations,
                    "warnings": [],  # 快速检查不返回警告
                    "notes": notes,
                    "meta": {"run_id": run_id, "agent": self.name},
                },
                "error": None,
            }

        except ImportError as e:
            return {
                "success": False,
                "data": {
                    "passed": False,
                    "violations": [],
                    "warnings": [],
                    "notes": [],
                },
                "error": f"Cannot import sot_guard_skill: {e}",
            }


# ============================================================
# 自动注册到 Registry
# ============================================================

def _code_review_agent_factory(
    base_path: Optional[Path] = None, **_: Any
) -> CodeReviewAgentPure:
    """CodeReviewAgentPure 工厂函数"""
    return CodeReviewAgentPure(base_path=base_path)


register_agent(
    name="review",
    factory=_code_review_agent_factory,
    description="代码审核 Agent（MCP 安全，SoT 一致性检查）",
    version="2.0.0",
    tags=["review", "sot", "mcp_safe", "pure_logic"],
    mcp_safe=True,
    override=True,
)
