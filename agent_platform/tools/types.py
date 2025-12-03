"""
TYPE SYSTEM SOURCE OF TRUTH (Types SoT) - agent_platform.tools.types
==============================================================================

CANONICAL SOURCE:
    This module is the Single Source of Truth for all agent/skill type
    definitions. All type imports should ultimately trace back to this file.

RE-EXPORT LAYER:
    agents/tools/types.py re-exports from this module for backward compatibility.
    New code should import directly from agent_platform.tools.types.

DESIGN RATIONALE:
    - Centralized type definitions prevent drift between CLI and MCP modes
    - TypedDict with inheritance pattern (P1-07 fix) enables proper required
      field enforcement while maintaining JSON serialization compatibility
    - error_kind enumeration aligns with AGENT_PLATFORM_OBSERVABILITY_SOT.md

MIGRATION GUIDE:
    Old import (deprecated but supported):
        from agents.tools.types import AgentResponse, SkillResult

    New import (recommended):
        from agent_platform.tools.types import AgentResponse, SkillResult

VERSION HISTORY:
    v1.0 (Phase 3.1, 2025-11-27):
        - Initial migration from agents/tools/types.py
        - Established as canonical source
        - Added error_kind field to AgentResponse

    v1.1 (Phase 3.2, 2025-11-28):
        - P1-07 fix: TypedDict inheritance for required fields
        - Added _AgentResponseRequired, _SkillResultRequired internal classes
        - Fixed Python 3.11 compatibility with typing_extensions

    v1.2 (Phase 3.3, 2025-12-03):
        - P2-03: Added comprehensive documentation
        - Documented version history and design rationale
        - Added migration guide for downstream consumers

EXPORTED TYPES:
    - AgentResponse: Standard return type for Agent.handle_request()
    - AgentResponseData: Type hints for AgentResponse.data field
    - SkillResult: Standard return type for Skill functions
    - SotViolationDict: Structure for SoT Guard violations
    - ReviewResult: Structure for code review results
    - ChangesDict, NotesType, MetaType: Common type aliases

基准对齐：
    - Agent Layer Freeze v1.0 (SUBAGENT_PROTOCOL.md)
    - MASTER.md v3.5
    - MCP Mode Phase 3.3
"""

from typing import Any, Optional, Dict, List
from typing_extensions import TypedDict  # Fix: Python 3.11 兼容


class AgentResponseData(TypedDict, total=False):
    """
    Data structure within AgentResponse.

    Different agents populate different fields:
    - BEAgent/FEAgent: changes, notes
    - TestAgent: prompt, executed, reason
    - DocAgent: action, doc_type, content, changes, notes, meta
    - ReviewAgent: passed, violations, warnings, notes
    - Orchestrator: flow, message, steps
    """
    # Code generation agents (FE/BE)
    changes: Dict[str, str]

    # Test agent
    prompt: str
    executed: bool
    reason: str

    # Doc agent
    action: str
    doc_type: str
    content: Optional[str]

    # Review agent
    passed: bool
    violations: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]

    # Orchestrator
    flow: str
    message: str
    steps: Dict[str, Any]

    # Common fields (all agents should include these)
    notes: List[str]
    meta: Dict[str, Any]


# Fix: P1-07 - 使用继承方式区分必需和可选字段
class _AgentResponseRequired(TypedDict):
    """AgentResponse 必需字段（内部使用）"""
    success: bool


class AgentResponse(_AgentResponseRequired, total=False):
    """
    Standard response structure for all Agent.handle_request() calls.

    # Fix: P1-07 - success 现在是真正的必需字段
    # Phase 3.1: 新增 error_kind 字段用于错误分类

    All agents MUST return responses conforming to this structure.

    Required Fields:
        success: Whether the operation completed successfully (MUST be present)

    Optional Fields:
        data: Operation result (structure varies by agent type, see AgentResponseData)
        error: Error message if success=False, None otherwise
        error_kind: Error classification (Phase 3.1), one of:
            - "OK": No error
            - "VALIDATION_ERROR": Input validation failed
            - "SOT_VIOLATION": SoT rule violation
            - "LLM_ERROR": LLM API error
            - "INFRA_ERROR": Infrastructure error
            - "AGENT_ERROR": Agent execution error
            - "UNKNOWN": Unclassified error

    Usage Examples:
        # Success response
        {
            "success": True,
            "data": {
                "changes": {"src/file.ts": "...content..."},
                "notes": ["Generated 1 file"],
                "meta": {"model": "claude-3-5-sonnet"}
            },
            "error": None,
            "error_kind": "OK"
        }

        # Error response
        {
            "success": False,
            "data": None,
            "error": "Missing required parameter: task",
            "error_kind": "VALIDATION_ERROR"
        }

    Alignment:
        - SUBAGENT_PROTOCOL.md: AgentProtocol.handle_request() return type
        - AGENT_ORCHESTRATION_PIPELINE.md: Step result structure
        - AGENT_PLATFORM_OBSERVABILITY_SOT.md: error_kind enumeration
    """

    data: Any  # Should conform to AgentResponseData when present
    error: Optional[str]
    error_kind: str  # Phase 3.1: Error classification


# Fix: P1-07 - 使用继承方式区分必需和可选字段
class _SkillResultRequired(TypedDict):
    """SkillResult 必需字段（内部使用）"""
    success: bool


class SkillResult(_SkillResultRequired, total=False):
    """
    Standard response structure for Skill functions.

    # Fix: P1-07 - success 现在是真正的必需字段

    Similar to AgentResponse but allows optional 'raw' field for debugging.
    Used when skills need to preserve raw API responses for error diagnosis.

    Required Fields:
        success: Whether the skill execution succeeded (MUST be present)

    Optional Fields:
        data: Skill output (e.g., generated code, prompts, analysis results)
        error: Error message if success=False, None otherwise
        raw: Raw response text from external APIs for debugging

    Usage:
        Skills are called by Agents and return SkillResult.
        Agents wrap this into AgentResponse before returning to callers.
    """

    data: Any
    error: Optional[str]
    raw: str


class SotViolationDict(TypedDict):
    """
    Structure for SoT Guard violation/warning entries.

    Used by CodeReviewAgent and sot_guard_skill.
    """
    file: str
    rule: str
    severity: str  # "P0" | "P1" | "P2"
    detail: str
    line: Optional[int]


class ReviewResult(TypedDict, total=False):
    """
    Result structure for code review operations.

    Used by CodeReviewAgent._full_review() and _quick_check().
    """
    passed: bool
    violations: List[SotViolationDict]
    warnings: List[SotViolationDict]


# Type aliases for common structures
ChangesDict = Dict[str, str]  # file_path -> file_content
NotesType = List[str]
MetaType = Dict[str, Any]


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
