"""
Common type definitions for agents and skills.

Re-exports from agent_platform.tools.types to maintain a single source of truth.
This ensures type consistency between agent_platform and agents packages.

SoT: agent_platform/tools/types.py (canonical version)
Phase 3.1: SoT direction reversed - platform layer is now canonical

基准对齐：
- Agent Layer Freeze v1.0 (SUBAGENT_PROTOCOL.md)
- MASTER.md v3.5

Note: This file re-exports from agent_platform to ensure:
  1. Platform layer (agent_platform) does not depend on business layer (agents)
  2. Future extraction of agent_platform as a standalone package is possible
  3. Backward compatibility - existing imports from agents.tools.types still work
"""

# Re-export all types from canonical source (agent_platform)
from agent_platform.tools.types import (
    AgentResponse,
    AgentResponseData,
    SkillResult,
    SotViolationDict,
    ReviewResult,
    ChangesDict,
    NotesType,
    MetaType,
)

__all__ = [
    "AgentResponse",
    "AgentResponseData",
    "SkillResult",
    "SotViolationDict",
    "ReviewResult",
    "ChangesDict",
    "NotesType",
    "MetaType",
]
