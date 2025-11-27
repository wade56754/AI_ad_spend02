"""
orchestrator_agent.py

Global Orchestrator Agent.
- Does not generate code directly; coordinates BEAgent / FEAgent / TestAgent.
- Executes different flows in sequence to build an automation pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Callable
import logging

from ..tools.types import AgentResponse

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorResult:
    success: bool
    flow: str
    message: str
    steps: Dict[str, AgentResponse]


class OrchestratorAgent:
    """
    Orchestrator Agent: Coordinates BE/FE/Test agents in defined workflows.

    Supported flows:
        - "backend_only": Runs only backend code generation
        - "frontend_only": Runs only frontend code generation
        - "full_pipeline": Runs backend → frontend → test (sequentially)

    Request format:
        {
            "flow": "full_pipeline",  # Required: one of the flows above
            "backend_request": {...},  # Passed to be_agent.handle_request()
            "frontend_request": {...}, # Passed to fe_agent.handle_request()
            "test_request": {...},     # (Optional) Passed to test_agent.handle_request()
            "test_enabled": bool,      # (Default: True) Run test step in full_pipeline
        }

    Returns:
        AgentResponse with data.steps containing results from each executed agent.
        If any step fails, pipeline stops and returns partial results.
    """

    def __init__(
        self,
        base_path: Optional[Path] = None,
        supabase_project_id: Optional[str] = None,
    ) -> None:
        from ..agents_config import create_agent

        # 推断项目根路径：agents/ 的上一级
        self.base_path: Path = (
            base_path
            if base_path is not None
            else Path(__file__).resolve().parent.parent.parent
        )

        # 这里用 agents_config.create_agent 统一创建子 Agent
        self._backend_agent = create_agent("be", base_path=self.base_path)
        self._frontend_agent = create_agent("fe", base_path=self.base_path)
        self._test_agent = create_agent(
            "test",
            base_path=self.base_path,
            supabase_project_id=supabase_project_id,
        )

        # flow 路由表
        self._flow_handlers: Dict[
            str, Callable[[Dict[str, Any]], OrchestratorResult]
        ] = {
            "backend_only": self._run_backend_only,
            "frontend_only": self._run_frontend_only,
            "full_pipeline": self._run_full_pipeline,
        }

    # ------------------------------------------------------------------ #
    # 对外主入口
    # ------------------------------------------------------------------ #

    def handle_request(self, request: Dict[str, Any]) -> AgentResponse:
        """
        Orchestrator 入口。

        Args:
            request: 请求字典，至少包含 "flow" 字段

        Returns:
            {
              "success": bool,
              "data": {
                "flow": str,
                "message": str,
                "steps": {
                  "backend": { ... },
                  "frontend": { ... },
                  "test": { ... }
                }
              },
              "error": Optional[str],
            }
        """
        flow = (request.get("flow") or "").strip()
        if not flow:
            logger.warning("Orchestrator request missing 'flow' field")
            return {
                "success": False,
                "data": None,
                "error": "Missing 'flow' in orchestrator request",
            }

        handler = self._flow_handlers.get(flow)
        if handler is None:
            logger.error(f"Unknown flow: '{flow}'")
            return {
                "success": False,
                "data": {"flow": flow, "steps": {}},
                "error": f"Unknown flow: {flow}",
            }

        logger.info(f"Orchestrator starting flow: '{flow}'")

        try:
            result = handler(request)
        except Exception as exc:
            logger.exception(f"Orchestrator flow '{flow}' crashed: {exc}")
            return {
                "success": False,
                "data": {"flow": flow, "steps": {}},
                "error": f"Orchestrator flow '{flow}' failed: {exc}",
            }

        if result.success:
            logger.info(f"Orchestrator flow '{flow}' completed successfully")
        else:
            logger.error(f"Orchestrator flow '{flow}' failed: {result.message}")

        # dataclass → dict
        return {
            "success": result.success,
            "data": {
                "flow": result.flow,
                "message": result.message,
                "steps": result.steps,
            },
            "error": None if result.success else result.message,
        }

    # ------------------------------------------------------------------ #
    # 各种 flow 的实现
    # ------------------------------------------------------------------ #

    def _run_backend_only(self, request: Dict[str, Any]) -> OrchestratorResult:
        be_req: Dict[str, Any] = request.get("backend_request") or {}

        logger.info("Orchestrator: backend step started")
        be_result = self._backend_agent.handle_request(be_req)

        success = bool(be_result.get("success", False))
        msg = (
            "Backend flow completed"
            if success
            else f"Backend flow failed: {be_result.get('error')}"
        )
        logger.info(f"Orchestrator: backend step finished (success={success})")

        return OrchestratorResult(
            success=success,
            flow="backend_only",
            message=msg,
            steps={"backend": be_result},
        )

    def _run_frontend_only(self, request: Dict[str, Any]) -> OrchestratorResult:
        fe_req: Dict[str, Any] = request.get("frontend_request") or {}

        logger.info("Orchestrator: frontend step started")
        fe_result = self._frontend_agent.handle_request(fe_req)

        success = bool(fe_result.get("success", False))
        msg = (
            "Frontend flow completed"
            if success
            else f"Frontend flow failed: {fe_result.get('error')}"
        )
        logger.info(f"Orchestrator: frontend step finished (success={success})")

        return OrchestratorResult(
            success=success,
            flow="frontend_only",
            message=msg,
            steps={"frontend": fe_result},
        )

    def _run_full_pipeline(self, request: Dict[str, Any]) -> OrchestratorResult:
        """
        Simple pipeline: backend -> frontend -> test (optional).
        Backend / frontend must succeed before proceeding to the next step.
        """
        steps: Dict[str, Dict[str, Any]] = {}

        # 1. Backend
        be_req: Dict[str, Any] = request.get("backend_request") or {}
        logger.info("Orchestrator: backend step started")
        be_result = self._backend_agent.handle_request(be_req)
        steps["backend"] = be_result
        logger.info(f"Orchestrator: backend step finished (success={be_result.get('success', False)})")

        if not be_result.get("success", False):
            return OrchestratorResult(
                success=False,
                flow="full_pipeline",
                message=f"Backend step failed: {be_result.get('error')}",
                steps=steps,
            )

        # 2. Frontend
        fe_req: Dict[str, Any] = request.get("frontend_request") or {}
        logger.info("Orchestrator: frontend step started")
        fe_result = self._frontend_agent.handle_request(fe_req)
        steps["frontend"] = fe_result
        logger.info(f"Orchestrator: frontend step finished (success={fe_result.get('success', False)})")

        if not fe_result.get("success", False):
            return OrchestratorResult(
                success=False,
                flow="full_pipeline",
                message=f"Frontend step failed: {fe_result.get('error')}",
                steps=steps,
            )

        # 3. Test (optional via test_enabled)
        test_enabled = bool(request.get("test_enabled", True))
        if test_enabled:
            # TestAgent currently only generates prompt, actual execution via MCP
            test_req: Dict[str, Any] = request.get("test_request") or {}
            logger.info("Orchestrator: test step started")
            test_result = self._test_agent.handle_request(test_req)
            steps["test"] = test_result
            logger.info(f"Orchestrator: test step finished (success={test_result.get('success', False)})")

            if not test_result.get("success", False):
                return OrchestratorResult(
                    success=False,
                    flow="full_pipeline",
                    message=f"Test step failed: {test_result.get('error')}",
                    steps=steps,
                )

        return OrchestratorResult(
            success=True,
            flow="full_pipeline",
            message="Full pipeline completed successfully",
            steps=steps,
        )
