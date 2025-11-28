"""
Common type definitions for agents and skills.

Provides standardized return structures to ensure consistent API contracts
across Agent and Skill layers.

基准对齐：
- Agent Layer Freeze v1.0 (SUBAGENT_PROTOCOL.md)
- MASTER.md v3.5
"""

from typing import Any, Optional, TypedDict, Dict, List


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


class AgentResponse(TypedDict, total=False):
    """
    Standard response structure for all Agent.handle_request() calls.

    All agents MUST return responses conforming to this structure.

    Required Fields:
        success: Whether the operation completed successfully
        error: Error message if success=False, None otherwise

    Optional Fields:
        data: Operation result (structure varies by agent type, see AgentResponseData)

    Usage Examples:
        # Success response
        {
            "success": True,
            "data": {
                "changes": {"src/file.ts": "...content..."},
                "notes": ["Generated 1 file"],
                "meta": {"model": "claude-3-5-sonnet"}
            },
            "error": None
        }

        # Error response
        {
            "success": False,
            "data": None,
            "error": "Missing required parameter: task"
        }

    Alignment:
        - SUBAGENT_PROTOCOL.md: AgentProtocol.handle_request() return type
        - AGENT_ORCHESTRATION_PIPELINE.md: Step result structure
    """

    success: bool
    data: Any  # Should conform to AgentResponseData when present
    error: Optional[str]


class SkillResult(TypedDict, total=False):
    """
    Standard response structure for Skill functions.

    Similar to AgentResponse but allows optional 'raw' field for debugging.
    Used when skills need to preserve raw API responses for error diagnosis.

    Required Fields:
        success: Whether the skill execution succeeded
        error: Error message if success=False, None otherwise

    Optional Fields:
        data: Skill output (e.g., generated code, prompts, analysis results)
        raw: Raw response text from external APIs for debugging

    Usage:
        Skills are called by Agents and return SkillResult.
        Agents wrap this into AgentResponse before returning to callers.
    """

    success: bool
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
