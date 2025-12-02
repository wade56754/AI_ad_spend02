"""
FEAgent - Frontend Development Agent

Phase 3.0A: Migrated to AgentProtocol + Registry system.

Orchestrates frontend code generation by delegating to fe_dev_skill.
Enforces SoT compliance by loading MASTER, API_SOT, FRONTEND_RULES, UI_DESIGN_SYSTEM.

Does NOT auto-write files; returns generated code for caller to review/write.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import logging

from agent_platform.core.protocol import AgentProtocol, AgentContext
from ..tools.types import AgentResponse

logger = logging.getLogger(__name__)


class FEAgent(AgentProtocol):
    """
    Frontend Development Agent.

    Generates Next.js/React/TypeScript code with Tailwind CSS and shadcn/ui.
    Enforces SoT compliance through fe_dev_skill's context loading.

    Request Fields:
        - task (required): Task description (e.g., "Add loading spinner to dashboard")
        - target_files (optional): List of frontend file paths to modify
        - ui_module (optional): UI module name (e.g., "daily-reports", "topups")
        - page_name (optional): Page name (e.g., "DashboardPage", "TopupListPage")

    Response Fields:
        - data.changes: Dict[file_path, new_content] if success=True
        - data.notes: List[str] with self-review notes from LLM
        - data.meta: Metadata including run_id, agent, version, skill_used
        - error: Error message if validation or LLM call fails
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

    @property
    def name(self) -> str:
        """Agent unique identifier."""
        return "fe"

    @property
    def description(self) -> str:
        """Agent description."""
        return "Frontend Next.js/React/TypeScript code generation with SoT compliance"

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
        Process frontend development request.

        Args:
            request: Request dictionary with fields:
                - task: Task description (required)
                - target_files: List of frontend file paths (optional)
                - ui_module: UI module name (optional)
                - page_name: Page name (optional)
            context: Optional execution context for tracing (auto-created if None)

        Returns:
            AgentResponse with changes, notes, and metadata
        """
        from ..tools.validation import validate_task_and_files
        from ..skills.fe_dev_skill import fe_dev_skill

        # Phase 3.0A: Ensure context exists for tracing
        context = context or AgentContext()
        run_id = context.run_id

        task = request.get("task", "")
        target_files = request.get("target_files", [])
        ui_module = request.get("ui_module")
        page_name = request.get("page_name")

        # Validate required fields
        validation_error = validate_task_and_files(task, target_files)
        if validation_error:
            logger.warning(
                f"[run_id={run_id}] FE Agent validation failed: {validation_error['error']}"
            )
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
                "error": validation_error.get("error", "Validation failed"),
            }

        # Build enhanced task description with optional context
        enhanced_task = task
        if ui_module:
            enhanced_task = f"[Module: {ui_module}] {enhanced_task}"
        if page_name:
            enhanced_task = f"[Page: {page_name}] {enhanced_task}"

        logger.info(
            f"[run_id={run_id}] FE Agent processing task: '{task[:50]}...' "
            f"(files: {len(target_files)}, module: {ui_module or 'N/A'})"
        )

        # Call fe_dev_skill
        # TODO Phase 4: Pass context to skill layer for complete tracing
        result = fe_dev_skill(enhanced_task, target_files)

        # Build AgentResponse
        if result["success"]:
            skill_data = result.get("data", {})
            changes_count = len(skill_data.get("changes", {}))
            logger.info(f"[run_id={run_id}] FE Agent completed: {changes_count} files generated")

            return {
                "success": True,
                "data": {
                    "changes": skill_data.get("changes", {}),
                    "notes": skill_data.get("notes", []),
                    "meta": {
                        "run_id": run_id,
                        "agent": self.name,
                        "version": self.version,
                        "skill_used": "fe_dev_skill",
                        "target_files": target_files,
                        "ui_module": ui_module,
                        "page_name": page_name,
                    },
                },
                "error": None,
            }
        else:
            logger.error(f"[run_id={run_id}] FE Agent failed: {result.get('error')}")

            return {
                "success": False,
                "data": {
                    "meta": {
                        "run_id": run_id,
                        "agent": self.name,
                        "version": self.version,
                        "skill_used": "fe_dev_skill",
                    },
                },
                "error": result.get("error", "Unknown error"),
            }
