"""
AI_ad_spend02 Agent Plugin Registration

This module provides the entry point for registering all business agents
to the agent_platform registry.

Usage:
    # In backend/main.py startup
    from agents.plugin import register_all
    register_all()

    # Or register individual agents
    from agents.plugin import register_demo, register_all_business_agents
    register_demo()  # For testing
"""

from typing import Any, Dict, Optional
import logging

from agent_platform.core.protocol import AgentProtocol, AgentContext
from agent_platform.core.registry import register_agent, get_registry

logger = logging.getLogger(__name__)


# ============================================================
# Demo Agent (for testing the platform skeleton)
# ============================================================


class DemoAgent(AgentProtocol):
    """
    Demo Agent for testing the agent_platform skeleton.

    Simply echoes back the request with some metadata.
    """

    @property
    def name(self) -> str:
        return "demo"

    @property
    def description(self) -> str:
        return "Demo agent that echoes requests (for testing)"

    @property
    def version(self) -> str:
        return "1.0.0"

    def handle_request(
        self,
        request: Dict[str, Any],
        context: Optional[AgentContext] = None,
    ) -> Dict[str, Any]:
        """
        Echo back the request with metadata.

        Args:
            request: Any request dict
            context: Optional execution context

        Returns:
            Standard AgentResponse with echoed data
        """
        context = context or AgentContext()

        return {
            "success": True,
            "data": {
                "echo": request,
                "agent": self.name,
                "version": self.version,
                "run_id": context.run_id,
                "notes": ["Demo agent processed request successfully"],
            },
            "error": None,
        }


# ============================================================
# Registration Functions
# ============================================================


def register_demo() -> None:
    """
    Register only the Demo agent.

    Use this for basic platform testing without loading all business agents.
    """
    register_agent(
        "demo",
        DemoAgent,
        description="Demo agent that echoes requests (for testing)",
        version="1.0.0",
        tags=["demo", "testing"],
    )
    logger.info("Registered demo agent")


def register_all_business_agents() -> None:
    """
    Register all AI_ad_spend business agents.

    Currently registered (Phase 3.0B):
    - be: Backend FastAPI code generation
    - fe: Frontend Next.js/React code generation
    - test: Test prompt generation (pytest + DB invariants)
    - orch: Orchestrator (BE→Test pipeline with context passthrough)

    Pending migration (Phase 3.1+):
    - doc: Documentation generation
    - review: Code review with SoT compliance
    """
    # Phase 2: BEAgent migrated to AgentProtocol
    from .agent_core.be_agent import BEAgent

    register_agent(
        "be",
        BEAgent,
        description="Backend FastAPI/SQLAlchemy code generation with SoT compliance",
        version="1.0.0",
        tags=["codegen", "backend", "sot"],
    )
    logger.info("Registered be agent")

    # Phase 3.0A: FEAgent migrated to AgentProtocol
    from .agent_core.fe_agent import FEAgent

    register_agent(
        "fe",
        FEAgent,
        description="Frontend Next.js/React/TypeScript code generation with SoT compliance",
        version="1.0.0",
        tags=["codegen", "frontend", "nextjs"],
    )
    logger.info("Registered fe agent")

    # Phase 3.0A: TestAgent migrated to AgentProtocol
    from .agent_core.test_agent import TestAgent

    register_agent(
        "test",
        TestAgent,
        description="Test prompt generation for pytest and database invariant validation",
        version="1.0.0",
        tags=["test", "pytest", "qa"],
    )
    logger.info("Registered test agent")

    # Phase 3.0B: OrchestratorAgent migrated to AgentProtocol
    from .agent_core.orchestrator_agent import OrchestratorAgent

    register_agent(
        "orch",
        OrchestratorAgent,
        description="Multi-Agent workflow orchestrator (backend/frontend/test coordination)",
        version="1.0.0",
        tags=["orchestrator", "multi-agent", "backend", "test"],
    )
    logger.info("Registered orch agent")

    # TODO: Migrate remaining agents in future phases
    # from .agent_core.doc_agent import DocAgent
    # from .agent_core.code_review_agent import CodeReviewAgent


def register_all() -> None:
    """
    Register all agents (demo + business agents).

    Call this function in backend/main.py startup to initialize
    the agent registry.

    Example:
        # backend/main.py
        from contextlib import asynccontextmanager
        from fastapi import FastAPI

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            from agents.plugin import register_all
            register_all()
            yield
            # Shutdown

        app = FastAPI(lifespan=lifespan)
    """
    # Always register demo agent
    register_demo()

    # Register business agents (Phase 2)
    register_all_business_agents()

    registry = get_registry()
    logger.info(f"Agent registration complete. Total agents: {registry.count}")
    logger.info(f"Available agents: {[m.name for m in registry.list_agents()]}")


# ============================================================
# Exports
# ============================================================

# Phase 2.1: 统一导出策略
# - 不再支持 `from agents.plugin import BEAgent` 懒加载
# - Agent 实例应通过 register_all() + create_agent("be") 获取
# - 这样可以避免循环导入问题，并确保 Agent 在注册后才能使用

__all__ = [
    # Demo Agent（仅用于测试，可直接导出）
    "DemoAgent",
    # 注册函数
    "register_demo",
    "register_all_business_agents",
    "register_all",
    # 不再导出 BEAgent，使用 create_agent("be") 代替
]
