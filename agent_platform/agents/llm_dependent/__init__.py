"""
agent_platform.agents.llm_dependent - LLM 依赖的 Agent

Phase 2: Agent 层迁移
- 此目录包含 mcp_safe=False 的 Agent（调用 LLM）
- MCP 模式下这些 Agent 不会被暴露

LLM 依赖的 Agent:
- fe: 前端代码生成（调用 fe_dev_skill -> LLM）
- be: 后端代码生成（调用 be_dev_skill -> LLM）
- orch: 流程编排（协调其他 Agent，间接调用 LLM）

设计原则:
- 这些 Agent 的实现仍在 agents/agent_core/
- 此处只是注册到新 registry（mcp_safe=False）
- 保持与旧 agents/ 的兼容

基准对齐:
- AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md Phase 2
"""

from pathlib import Path
from typing import Any, Optional
import logging

from agent_platform.core.registry import register_agent

logger = logging.getLogger(__name__)


# ============================================================
# FE Agent (mcp_safe=False)
# ============================================================

def _fe_agent_factory(base_path: Optional[Path] = None, **kwargs: Any):
    """FEAgent 工厂（委托给 agents.agent_core.fe_agent）"""
    from agents.agent_core.fe_agent import FEAgent
    return FEAgent(base_path=base_path)


register_agent(
    name="fe",
    factory=_fe_agent_factory,
    description="前端代码生成 Agent（调用 LLM）",
    version="1.0.0",
    tags=["fe", "frontend", "llm_dependent"],
    mcp_safe=False,  # 调用 LLM
    override=True,
)


# ============================================================
# BE Agent (mcp_safe=False)
# ============================================================

def _be_agent_factory(base_path: Optional[Path] = None, **kwargs: Any):
    """BEAgent 工厂（委托给 agents.agent_core.be_agent）"""
    from agents.agent_core.be_agent import BEAgent
    return BEAgent(base_path=base_path)


register_agent(
    name="be",
    factory=_be_agent_factory,
    description="后端代码生成 Agent（调用 LLM）",
    version="1.0.0",
    tags=["be", "backend", "llm_dependent"],
    mcp_safe=False,
    override=True,
)


# ============================================================
# Orchestrator Agent (mcp_safe=False)
# ============================================================

def _orch_agent_factory(
    base_path: Optional[Path] = None,
    supabase_project_id: Optional[str] = None,
    **kwargs: Any,
):
    """OrchestratorAgent 工厂"""
    from agents.agent_core.orchestrator_agent import OrchestratorAgent
    return OrchestratorAgent(
        base_path=base_path,
        supabase_project_id=supabase_project_id,
    )


register_agent(
    name="orch",
    factory=_orch_agent_factory,
    description="流程编排 Agent（协调其他 Agent）",
    version="1.0.0",
    tags=["orch", "orchestrator", "llm_dependent"],
    mcp_safe=False,  # 间接调用 LLM
    override=True,
)


logger.info("LLM-dependent agents registered: fe, be, orch (mcp_safe=False)")
