from pathlib import Path
from typing import Dict, Any, Optional
import logging

from ..tools.types import AgentResponse

logger = logging.getLogger(__name__)

class FEAgent:
    """
    Frontend Development Agent.

    Orchestrates frontend code generation by delegating to fe_dev_skill.
    Enforces UI design system and frontend rules from FRONTEND_RULES and
    UI_DESIGN_SYSTEM SoT documents.

    Does NOT auto-write files; returns generated code for caller to review/write.
    """

    def __init__(self, base_path: Optional[Path] = None) -> None:
        """
        Initialize Frontend Agent.

        Args:
            base_path: Project root directory (defaults to auto-detected path)
        """
        self.base_path = (
            base_path
            if base_path is not None
            else Path(__file__).resolve().parent.parent.parent
        )

    def handle_request(self, request: Dict[str, Any]) -> AgentResponse:
        """
        Process frontend development request.

        Args:
            request: Request dictionary with fields:
                - task: Task description (e.g., "Refactor project list page with filters")
                - target_files: List of frontend file paths to modify (relative to frontend/)

        Returns:
            AgentResponse with:
                - data.changes: Dict[file_path, new_content] if success=True
                - data.notes: List[str] with self-review notes from LLM
                - error: Error message if validation or LLM call fails
        """
        from ..tools.validation import validate_task_and_files
        from ..skills.fe_dev_skill import fe_dev_skill

        task = request.get("task", "")
        target_files = request.get("target_files", [])

        # 参数校验（使用统一函数）
        validation_error = validate_task_and_files(task, target_files)
        if validation_error:
            logger.warning(f"FE Agent validation failed: {validation_error['error']}")
            return validation_error

        logger.info(
            f"FE Agent processing task: '{task[:50]}...' "
            f"(files: {len(target_files)})"
        )

        # 调用 skill
        result = fe_dev_skill(task, target_files)

        if result["success"]:
            changes_count = len(result.get("data", {}).get("changes", {}))
            logger.info(f"FE Agent completed: {changes_count} files generated")
        else:
            logger.error(f"FE Agent failed: {result.get('error')}")

        return result

