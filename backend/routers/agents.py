"""
Agent Platform HTTP API Router

Phase 3.0C: Provides HTTP endpoints for Agent Platform invocation.

Endpoints:
    GET  /api/v1/agents        - List all registered agents
    GET  /api/v1/agents/{name} - Get agent metadata
    POST /api/v1/agents/run    - Run any agent by name
    POST /api/v1/agents/orch   - Run OrchestratorAgent with specific flow

SoT Compliance:
    - Response format: StandardResponse (ERROR_CODES_SOT.md v2.1)
    - Error codes: SYS-001 (internal), VAL-001 (validation)
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.core.response import success_response, error_response

router = APIRouter(prefix="/agents", tags=["agents"])


# ============================================================
# Request/Response Models
# ============================================================


class AgentRunRequest(BaseModel):
    """Request model for running an agent."""

    agent: str = Field(..., description="Agent name (be, fe, test, orch, etc.)")
    request: Dict[str, Any] = Field(
        default_factory=dict,
        description="Agent request payload",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "agent": "be",
                "request": {
                    "task": "Generate topup API endpoint",
                    "target_files": ["routers/topup.py"],
                },
            }
        }


class OrchRunRequest(BaseModel):
    """Request model for running OrchestratorAgent."""

    flow: str = Field(..., description="Orchestrator flow to execute")
    task: Optional[str] = Field(None, description="Task description")
    target_files: Optional[List[str]] = Field(None, description="Target file paths")
    module: Optional[str] = Field(None, description="Module name for scoped operations")
    mode: str = Field("dry-run", description="Execution mode: dry-run or execute")
    extra: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional flow-specific parameters",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "flow": "be_then_test",
                "task": "Implement finance_profit API with tests",
                "target_files": [
                    "routers/finance_profit.py",
                    "tests/api/test_finance_profit.py",
                ],
                "module": "finance_profit",
                "mode": "dry-run",
            }
        }


class AgentMetaResponse(BaseModel):
    """Agent metadata response."""

    name: str
    version: str
    description: str
    tags: List[str]


# ============================================================
# Utility Functions
# ============================================================


def _ensure_agents_registered() -> None:
    """Ensure all business agents are registered."""
    from agent_platform.core.registry import get_registry
    from agents.plugin import register_all

    registry = get_registry()
    if registry.count == 0:
        register_all()


# ============================================================
# Endpoints
# ============================================================


@router.get("")
async def list_agents():
    """
    List all registered agents.

    Returns:
        List of agent metadata (name, version, description, tags)
    """
    _ensure_agents_registered()

    from agent_platform.core.registry import list_agents

    agents = list_agents()
    data = [
        {
            "name": meta.name,
            "version": meta.version,
            "description": meta.description,
            "tags": list(meta.tags) if meta.tags else [],
        }
        for meta in agents
    ]

    return success_response(
        data={"agents": data, "count": len(data)},
        message=f"Found {len(data)} registered agents",
    )


@router.get("/{agent_name}")
async def get_agent_info(agent_name: str):
    """
    Get metadata for a specific agent.

    Args:
        agent_name: Agent identifier (e.g., "be", "fe", "orch")

    Returns:
        Agent metadata or 404 if not found
    """
    _ensure_agents_registered()

    from agent_platform.core.registry import get_registry

    registry = get_registry()
    meta = registry.get_agent_metadata(agent_name)

    if meta is None:
        available = [a.name for a in registry.list_agents()]
        raise HTTPException(
            status_code=404,
            detail={
                "code": "AGENT_NOT_FOUND",
                "message": f"Agent '{agent_name}' not found",
                "available_agents": available,
            },
        )

    return success_response(
        data={
            "name": meta.name,
            "version": meta.version,
            "description": meta.description,
            "tags": list(meta.tags) if meta.tags else [],
        },
        message=f"Agent '{agent_name}' found",
    )


@router.post("/run")
async def run_agent(body: AgentRunRequest):
    """
    Run any agent by name with the given request payload.

    Args:
        body: AgentRunRequest with agent name and request dict

    Returns:
        Agent execution result (success, data, error)
    """
    _ensure_agents_registered()

    from agent_platform.core.protocol import AgentContext
    from agent_platform.core.registry import create_agent

    agent_name = body.agent
    request = body.request

    # Create agent
    try:
        agent = create_agent(agent_name)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "AGENT_NOT_FOUND",
                "message": str(e),
            },
        )

    # Execute with tracing context
    context = AgentContext()
    run_id = context.run_id

    try:
        result = agent.handle_request(request, context)
    except Exception as e:
        return error_response(
            code="SYS-001",
            message=f"Agent execution failed: {e}",
            status_code=500,
            details={"run_id": run_id, "agent": agent_name},
        )

    # Return result
    success = result.get("success", False)
    if success:
        return success_response(
            data={
                "run_id": run_id,
                "agent": agent_name,
                "result": result,
            },
            message=f"Agent '{agent_name}' executed successfully",
        )
    else:
        return error_response(
            code="AGENT_EXEC_FAILED",
            message=result.get("error", "Agent execution failed"),
            status_code=400,
            details={
                "run_id": run_id,
                "agent": agent_name,
                "result": result,
            },
        )


@router.post("/orch")
async def run_orchestrator(body: OrchRunRequest):
    """
    Run OrchestratorAgent with a specific flow.

    Supported flows:
        - be_then_test: BEAgent → TestAgent pipeline
        - backend_only: Run BEAgent only
        - frontend_only: Run FEAgent only
        - full_pipeline: Backend → Frontend → Test
        - frontend_restructure: SC-ORCH 7-step pipeline
        - gen_backend: Batch backend module generation
        - auto_fix: Generate → Test → Fix loop

    Args:
        body: OrchRunRequest with flow and parameters

    Returns:
        Orchestrator execution result with step details
    """
    _ensure_agents_registered()

    from agent_platform.core.protocol import AgentContext
    from agent_platform.core.registry import create_agent

    # Build orchestrator request
    request: Dict[str, Any] = {
        "flow": body.flow,
    }

    if body.task:
        request["task"] = body.task
    if body.target_files:
        request["target_files"] = body.target_files
    if body.module:
        request["module"] = body.module

    # Set auto_write based on mode
    request["auto_write"] = body.mode == "execute"

    # Merge extra params
    if body.extra:
        request.update(body.extra)

    # Create orchestrator
    try:
        orch = create_agent("orch")
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "ORCH_NOT_AVAILABLE",
                "message": f"Cannot create orchestrator: {e}",
            },
        )

    # Execute with tracing context
    context = AgentContext()
    run_id = context.run_id

    try:
        result = orch.handle_request(request, context)
    except Exception as e:
        return error_response(
            code="SYS-001",
            message=f"Orchestrator execution failed: {e}",
            status_code=500,
            details={"run_id": run_id, "flow": body.flow},
        )

    # Return result
    success = result.get("success", False)
    data = result.get("data", {})

    response_data = {
        "run_id": run_id,
        "flow": body.flow,
        "mode": body.mode,
        "result": result,
    }

    if success:
        return success_response(
            data=response_data,
            message=f"Orchestrator flow '{body.flow}' completed successfully",
        )
    else:
        return error_response(
            code="ORCH_FLOW_FAILED",
            message=result.get("error", f"Flow '{body.flow}' failed"),
            status_code=400,
            details=response_data,
        )
