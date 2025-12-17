"""
Agent Management HTTP API Router

Provides HTTP endpoints for Agent management (CRUD + lifecycle operations).

Endpoints:
    GET    /api/v1/agents           - List all agents (with pagination)
    GET    /api/v1/agents/{id}      - Get agent details
    POST   /api/v1/agents           - Create new agent
    PUT    /api/v1/agents/{id}      - Update agent
    DELETE /api/v1/agents/{id}      - Delete agent
    POST   /api/v1/agents/{id}/start - Start agent
    POST   /api/v1/agents/{id}/stop  - Stop agent

SoT Compliance:
    - Response format: StandardResponse (ERROR_CODES_SOT.md v2.1)
    - Error codes: BIZ_002 (not found), BIZ_003 (already exists), SYS_001 (internal)
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.core.response import success_response, error_response, paginated_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


# ============================================================
# Enums
# ============================================================


class AgentStatus(str, Enum):
    """Agent status enum."""
    CREATED = "created"      # Agent created but never started
    RUNNING = "running"      # Agent is running
    STOPPED = "stopped"      # Agent was stopped
    ERROR = "error"          # Agent encountered an error


class AgentType(str, Enum):
    """Agent type enum."""
    BACKEND = "backend"           # Backend code generation agent
    FRONTEND = "frontend"         # Frontend code generation agent
    TEST = "test"                 # Test generation agent
    ORCHESTRATOR = "orchestrator" # Orchestration agent
    CUSTOM = "custom"             # Custom user-defined agent


# ============================================================
# Request/Response Models
# ============================================================


class AgentCreateRequest(BaseModel):
    """Request model for creating an agent."""

    name: str = Field(..., min_length=1, max_length=100, description="Agent name")
    description: Optional[str] = Field(None, max_length=500, description="Agent description")
    agent_type: AgentType = Field(default=AgentType.CUSTOM, description="Agent type")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Agent configuration")
    tags: Optional[List[str]] = Field(default_factory=list, description="Agent tags")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "my-backend-agent",
                "description": "Custom backend code generator",
                "agent_type": "backend",
                "config": {"model": "gpt-4", "temperature": 0.7},
                "tags": ["backend", "code-gen"]
            }
        }


class AgentUpdateRequest(BaseModel):
    """Request model for updating an agent."""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Agent name")
    description: Optional[str] = Field(None, max_length=500, description="Agent description")
    config: Optional[Dict[str, Any]] = Field(None, description="Agent configuration")
    tags: Optional[List[str]] = Field(None, description="Agent tags")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "updated-agent-name",
                "description": "Updated description",
                "config": {"model": "gpt-4-turbo"},
                "tags": ["updated", "backend"]
            }
        }


class AgentResponse(BaseModel):
    """Agent response model."""

    id: str
    name: str
    description: Optional[str]
    agent_type: AgentType
    status: AgentStatus
    config: Dict[str, Any]
    tags: List[str]
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    stopped_at: Optional[str] = None


class AgentLifecycleResponse(BaseModel):
    """Response model for agent lifecycle operations (start/stop)."""

    id: str
    name: str
    status: AgentStatus
    message: str


# ============================================================
# In-Memory Storage (to be replaced with database later)
# ============================================================


class AgentStore:
    """
    In-memory agent storage.

    Note: This is a simple implementation for development/testing.
    In production, this should be replaced with database persistence.
    """

    def __init__(self):
        self._agents: Dict[str, Dict[str, Any]] = {}
        self._initialize_default_agents()

    def _initialize_default_agents(self):
        """Initialize with some default agents."""
        default_agents = [
            {
                "name": "backend-agent",
                "description": "Backend code generation agent",
                "agent_type": AgentType.BACKEND,
                "config": {"model": "gpt-4"},
                "tags": ["backend", "code-gen"],
            },
            {
                "name": "frontend-agent",
                "description": "Frontend code generation agent",
                "agent_type": AgentType.FRONTEND,
                "config": {"model": "gpt-4"},
                "tags": ["frontend", "code-gen"],
            },
            {
                "name": "test-agent",
                "description": "Test generation agent",
                "agent_type": AgentType.TEST,
                "config": {"model": "gpt-4"},
                "tags": ["test", "code-gen"],
            },
        ]

        for agent_data in default_agents:
            agent_id = str(uuid4())
            now = datetime.utcnow().isoformat()
            self._agents[agent_id] = {
                "id": agent_id,
                "name": agent_data["name"],
                "description": agent_data["description"],
                "agent_type": agent_data["agent_type"],
                "status": AgentStatus.CREATED,
                "config": agent_data["config"],
                "tags": agent_data["tags"],
                "created_at": now,
                "updated_at": now,
                "started_at": None,
                "stopped_at": None,
            }

    def list_all(self, page: int = 1, page_size: int = 20,
                 status: Optional[AgentStatus] = None,
                 agent_type: Optional[AgentType] = None) -> tuple:
        """List agents with optional filtering."""
        agents = list(self._agents.values())

        # Apply filters
        if status:
            agents = [a for a in agents if a["status"] == status]
        if agent_type:
            agents = [a for a in agents if a["agent_type"] == agent_type]

        total = len(agents)

        # Apply pagination
        start = (page - 1) * page_size
        end = start + page_size
        paginated = agents[start:end]

        return paginated, total

    def get_by_id(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get agent by name."""
        for agent in self._agents.values():
            if agent["name"] == name:
                return agent
        return None

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent."""
        agent_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        agent = {
            "id": agent_id,
            "name": data["name"],
            "description": data.get("description"),
            "agent_type": data.get("agent_type", AgentType.CUSTOM),
            "status": AgentStatus.CREATED,
            "config": data.get("config", {}),
            "tags": data.get("tags", []),
            "created_at": now,
            "updated_at": now,
            "started_at": None,
            "stopped_at": None,
        }

        self._agents[agent_id] = agent
        return agent

    def update(self, agent_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing agent."""
        if agent_id not in self._agents:
            return None

        agent = self._agents[agent_id]

        # Update fields if provided
        if data.get("name") is not None:
            agent["name"] = data["name"]
        if data.get("description") is not None:
            agent["description"] = data["description"]
        if data.get("config") is not None:
            agent["config"] = data["config"]
        if data.get("tags") is not None:
            agent["tags"] = data["tags"]

        agent["updated_at"] = datetime.utcnow().isoformat()

        return agent

    def delete(self, agent_id: str) -> bool:
        """Delete an agent."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False

    def start(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Start an agent."""
        if agent_id not in self._agents:
            return None

        agent = self._agents[agent_id]

        # Can only start if not already running
        if agent["status"] == AgentStatus.RUNNING:
            return None

        agent["status"] = AgentStatus.RUNNING
        agent["started_at"] = datetime.utcnow().isoformat()
        agent["stopped_at"] = None
        agent["updated_at"] = datetime.utcnow().isoformat()

        return agent

    def stop(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Stop an agent."""
        if agent_id not in self._agents:
            return None

        agent = self._agents[agent_id]

        # Can only stop if running
        if agent["status"] != AgentStatus.RUNNING:
            return None

        agent["status"] = AgentStatus.STOPPED
        agent["stopped_at"] = datetime.utcnow().isoformat()
        agent["updated_at"] = datetime.utcnow().isoformat()

        return agent


# Global store instance
_agent_store = AgentStore()


def get_agent_store() -> AgentStore:
    """Dependency to get agent store."""
    return _agent_store


# ============================================================
# Endpoints
# ============================================================


@router.get("")
async def list_agents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    status: Optional[AgentStatus] = Query(None, description="Filter by status"),
    agent_type: Optional[AgentType] = Query(None, description="Filter by agent type"),
    store: AgentStore = Depends(get_agent_store),
):
    """
    List all agents with pagination and optional filtering.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        status: Optional status filter
        agent_type: Optional agent type filter

    Returns:
        Paginated list of agents
    """
    try:
        agents, total = store.list_all(
            page=page,
            page_size=page_size,
            status=status,
            agent_type=agent_type,
        )

        return paginated_response(
            data=agents,
            page=page,
            page_size=page_size,
            total=total,
        )
    except Exception as e:
        logger.error(f"Failed to list agents: {e}", exc_info=True)
        return error_response(
            code="SYS_001",
            message="Failed to list agents",
            status_code=500,
        )


@router.get("/{agent_id}")
async def get_agent(
    agent_id: str,
    store: AgentStore = Depends(get_agent_store),
):
    """
    Get agent details by ID.

    Args:
        agent_id: Agent UUID

    Returns:
        Agent details or 404 if not found
    """
    agent = store.get_by_id(agent_id)

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "BIZ_002",
                "message": f"Agent '{agent_id}' not found",
            },
        )

    return success_response(
        data=agent,
        message="Agent found",
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_agent(
    request: AgentCreateRequest,
    store: AgentStore = Depends(get_agent_store),
):
    """
    Create a new agent.

    Args:
        request: Agent creation request

    Returns:
        Created agent details
    """
    # Check if agent with same name already exists
    existing = store.get_by_name(request.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "BIZ_003",
                "message": f"Agent with name '{request.name}' already exists",
            },
        )

    try:
        agent = store.create({
            "name": request.name,
            "description": request.description,
            "agent_type": request.agent_type,
            "config": request.config,
            "tags": request.tags,
        })

        logger.info(f"Created agent: {agent['id']} ({agent['name']})")

        return success_response(
            data=agent,
            message="Agent created successfully",
            status_code=201,
        )
    except Exception as e:
        logger.error(f"Failed to create agent: {e}", exc_info=True)
        return error_response(
            code="SYS_001",
            message="Failed to create agent",
            status_code=500,
        )


@router.put("/{agent_id}")
async def update_agent(
    agent_id: str,
    request: AgentUpdateRequest,
    store: AgentStore = Depends(get_agent_store),
):
    """
    Update an existing agent.

    Args:
        agent_id: Agent UUID
        request: Agent update request

    Returns:
        Updated agent details
    """
    # Check if agent exists
    existing = store.get_by_id(agent_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "BIZ_002",
                "message": f"Agent '{agent_id}' not found",
            },
        )

    # Check name uniqueness if name is being changed
    if request.name and request.name != existing["name"]:
        name_exists = store.get_by_name(request.name)
        if name_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "BIZ_003",
                    "message": f"Agent with name '{request.name}' already exists",
                },
            )

    try:
        agent = store.update(agent_id, {
            "name": request.name,
            "description": request.description,
            "config": request.config,
            "tags": request.tags,
        })

        logger.info(f"Updated agent: {agent_id}")

        return success_response(
            data=agent,
            message="Agent updated successfully",
        )
    except Exception as e:
        logger.error(f"Failed to update agent: {e}", exc_info=True)
        return error_response(
            code="SYS_001",
            message="Failed to update agent",
            status_code=500,
        )


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    store: AgentStore = Depends(get_agent_store),
):
    """
    Delete an agent.

    Args:
        agent_id: Agent UUID

    Returns:
        Success message
    """
    # Check if agent exists
    existing = store.get_by_id(agent_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "BIZ_002",
                "message": f"Agent '{agent_id}' not found",
            },
        )

    # Cannot delete running agent
    if existing["status"] == AgentStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "BIZ_001",
                "message": "Cannot delete a running agent. Stop it first.",
            },
        )

    try:
        store.delete(agent_id)
        logger.info(f"Deleted agent: {agent_id}")

        return success_response(
            message="Agent deleted successfully",
        )
    except Exception as e:
        logger.error(f"Failed to delete agent: {e}", exc_info=True)
        return error_response(
            code="SYS_001",
            message="Failed to delete agent",
            status_code=500,
        )


@router.post("/{agent_id}/start")
async def start_agent(
    agent_id: str,
    store: AgentStore = Depends(get_agent_store),
):
    """
    Start an agent.

    Args:
        agent_id: Agent UUID

    Returns:
        Agent lifecycle response with new status
    """
    # Check if agent exists
    existing = store.get_by_id(agent_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "BIZ_002",
                "message": f"Agent '{agent_id}' not found",
            },
        )

    # Check if already running
    if existing["status"] == AgentStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "BIZ_001",
                "message": f"Agent '{existing['name']}' is already running",
            },
        )

    try:
        agent = store.start(agent_id)
        logger.info(f"Started agent: {agent_id} ({agent['name']})")

        return success_response(
            data={
                "id": agent["id"],
                "name": agent["name"],
                "status": agent["status"],
                "started_at": agent["started_at"],
            },
            message=f"Agent '{agent['name']}' started successfully",
        )
    except Exception as e:
        logger.error(f"Failed to start agent: {e}", exc_info=True)
        return error_response(
            code="SYS_001",
            message="Failed to start agent",
            status_code=500,
        )


@router.post("/{agent_id}/stop")
async def stop_agent(
    agent_id: str,
    store: AgentStore = Depends(get_agent_store),
):
    """
    Stop an agent.

    Args:
        agent_id: Agent UUID

    Returns:
        Agent lifecycle response with new status
    """
    # Check if agent exists
    existing = store.get_by_id(agent_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "BIZ_002",
                "message": f"Agent '{agent_id}' not found",
            },
        )

    # Check if not running
    if existing["status"] != AgentStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "BIZ_001",
                "message": f"Agent '{existing['name']}' is not running (current status: {existing['status']})",
            },
        )

    try:
        agent = store.stop(agent_id)
        logger.info(f"Stopped agent: {agent_id} ({agent['name']})")

        return success_response(
            data={
                "id": agent["id"],
                "name": agent["name"],
                "status": agent["status"],
                "stopped_at": agent["stopped_at"],
            },
            message=f"Agent '{agent['name']}' stopped successfully",
        )
    except Exception as e:
        logger.error(f"Failed to stop agent: {e}", exc_info=True)
        return error_response(
            code="SYS_001",
            message="Failed to stop agent",
            status_code=500,
        )
