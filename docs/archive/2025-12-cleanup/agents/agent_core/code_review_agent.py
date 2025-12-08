"""
CodeReviewAgent - 代码审核 Agent

职责：
- 审核生成的代码是否符合 SoT 规范
- 检查代码质量和安全问题
- 集成 sot_guard_skill 进行 P0/P1/P2 检查

输入:
    request = {
        "action": str,              # "review" | "quick_check"
        "changes": Dict[str, str],  # 文件路径 -> 文件内容
        "context": Optional[str]    # 额外上下文
    }

输出:
    {
        "success": bool,
        "passed": bool,             # 是否通过审核
        "violations": List[Dict],   # P0 违规列表
        "warnings": List[Dict],     # P1/P2 警告列表
        "notes": List[str],
        "error": Optional[str]
    }
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

from ..skills.sot_guard_skill import validate_against_sot

logger = logging.getLogger(__name__)


class CodeReviewAgent:
    """代码审核 Agent"""

    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.cwd()
        logger.info(f"CodeReviewAgent initialized: base_path={self.base_path}")

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理代码审核请求。

        Args:
            request: 包含 action, changes, context 的字典

        Returns:
            统一结构的响应
        """
        action = request.get("action", "review")
        changes = request.get("changes", {})
        context = request.get("context")

        logger.info(f"CodeReviewAgent request: action={action}, files={len(changes)}")

        try:
            if action == "review":
                return self._full_review(changes, context)
            elif action == "quick_check":
                return self._quick_check(changes, context)
            else:
                return {
                    "success": False,
                    "passed": False,
                    "violations": [],
                    "warnings": [],
                    "notes": [],
                    "error": f"Unknown action: {action}. Supported: review, quick_check",
                }
        except Exception as e:
            logger.error(f"CodeReviewAgent error: {e}")
            return {
                "success": False,
                "passed": False,
                "violations": [],
                "warnings": [],
                "notes": [],
                "error": str(e),
            }

    def _full_review(
        self,
        changes: Dict[str, str],
        context: Optional[str],
    ) -> Dict[str, Any]:
        """
        完整代码审核。

        执行:
        1. SoT 一致性检查 (sot_guard_skill)
        2. 代码质量检查 (TODO)
        3. 安全检查 (TODO)
        """
        if not changes:
            return {
                "success": True,
                "passed": True,
                "violations": [],
                "warnings": [],
                "notes": ["没有需要审核的代码变更"],
                "error": None,
            }

        # 1. SoT 一致性检查
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

        if context:
            notes.append(f"上下文: {context}")

        return {
            "success": True,
            "passed": passed,
            "violations": violations,
            "warnings": warnings,
            "notes": notes,
            "error": None,
        }

    def _quick_check(
        self,
        changes: Dict[str, str],
        context: Optional[str],
    ) -> Dict[str, Any]:
        """
        快速代码检查（仅 P0 级别）。

        比 full_review 更快，只检查最关键的 P0 违规。
        """
        if not changes:
            return {
                "success": True,
                "passed": True,
                "violations": [],
                "warnings": [],
                "notes": ["没有需要检查的代码变更"],
                "error": None,
            }

        # 调用 sot_guard，但只关注 P0
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
            "passed": passed,
            "violations": violations,
            "warnings": [],  # 快速检查不返回警告
            "notes": notes,
            "error": None,
        }
