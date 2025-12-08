from pathlib import Path
from typing import Dict, Any, Optional
import logging

from agent_platform.core.protocol import AgentProtocol, AgentContext
from ..tools.types import AgentResponse

logger = logging.getLogger(__name__)


class BEAgent(AgentProtocol):
    """
    Backend Development Agent.

    Orchestrates backend code generation by delegating to be_dev_skill.
    Enforces SoT (Source of Truth) compliance by loading DATA_SCHEMA,
    STATE_MACHINE, BUSINESS_RULES, API_SOT, and ERROR_CODES before generation.

    Does NOT auto-write files; returns generated code for caller to review/write.
    """

    def __init__(self, base_path: Optional[Path] = None) -> None:
        """
        Initialize Backend Agent.

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
        return "be"

    @property
    def description(self) -> str:
        """Agent description."""
        return "Backend FastAPI/SQLAlchemy code generation with SoT compliance"

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
        Process backend development request.

        Args:
            request: Request dictionary with fields:
                - task: Task description (e.g., "Implement topup list API with filters")
                - target_files: List of backend file paths to modify (relative to backend/)
            context: Optional execution context for tracing (auto-created if None)

        Returns:
            AgentResponse with:
                - data.changes: Dict[file_path, new_content] if success=True
                - data.notes: List[str] with self-review notes from LLM
                - data.meta: Metadata including run_id for tracing
                - error: Error message if validation or LLM call fails
        """
        from ..tools.validation import validate_task_and_files
        from ..skills.be_dev_skill import be_dev_skill

        # Phase 2.1: 确保 context 存在，用于追溯
        context = context or AgentContext()
        run_id = context.run_id

        task = request.get("task", "")
        target_files = request.get("target_files", [])

        # 参数校验（使用统一函数）
        validation_error = validate_task_and_files(task, target_files)
        if validation_error:
            logger.warning(
                f"[run_id={run_id}] BE Agent validation failed: {validation_error['error']}"
            )
            # Phase 2.1: 错误响应也需要包含 meta，便于 Orchestrator 追溯
            return {
                "success": False,
                "data": {
                    "meta": {
                        "run_id": run_id,
                        "agent": self.name,
                        "version": self.version,
                    },
                },
                "error": validation_error.get("error", "Validation failed"),
            }

        logger.info(
            f"[run_id={run_id}] BE Agent processing task: '{task[:50]}...' "
            f"(files: {len(target_files)})"
        )

        # 调用 skill（日志中已包含 run_id 用于追溯）
        # TODO Phase 3: 将 context 透传到 skill 层实现完整追溯链
        result = be_dev_skill(task, target_files)

        # Phase 2.1: 显式构造 AgentResponse，不泄露 SkillResult.raw
        if result["success"]:
            changes_count = len(result.get("data", {}).get("changes", {}))
            logger.info(f"[run_id={run_id}] BE Agent completed: {changes_count} files generated")

            # 构造标准 AgentResponse
            skill_data = result.get("data", {})
            return {
                "success": True,
                "data": {
                    "changes": skill_data.get("changes", {}),
                    "notes": skill_data.get("notes", []),
                    "meta": {
                        "run_id": run_id,
                        "agent": self.name,
                        "version": self.version,
                    },
                },
                "error": None,
            }
        else:
            logger.error(f"[run_id={run_id}] BE Agent failed: {result.get('error')}")

            # 错误响应，不暴露 raw 字段
            return {
                "success": False,
                "data": {
                    "meta": {
                        "run_id": run_id,
                        "agent": self.name,
                        "version": self.version,
                    },
                },
                "error": result.get("error", "Unknown error"),
            }

