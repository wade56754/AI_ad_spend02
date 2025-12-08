"""
Common type definitions for agents and skills.

Provides standardized return structures to ensure consistent API contracts
across Agent and Skill layers.

This is a copy from agents/tools/types.py for agent_platform independence.
"""

from typing import Any, Optional, Dict, List
from typing_extensions import TypedDict


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


class _AgentResponseRequired(TypedDict):
    """AgentResponse required fields (internal use)"""
    success: bool


class AgentResponse(_AgentResponseRequired, total=False):
    """
    Standard response structure for all Agent.handle_request() calls.

    All agents MUST return responses conforming to this structure.

    Required Fields:
        success: Whether the operation completed successfully (MUST be present)

    Optional Fields:
        data: Operation result (structure varies by agent type, see AgentResponseData)
        error: Error message if success=False, None otherwise

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
    """
    data: Any
    error: Optional[str]


class _SkillResultRequired(TypedDict):
    """SkillResult required fields (internal use)"""
    success: bool


class SkillResult(_SkillResultRequired, total=False):
    """
    Standard response structure for Skill functions.

    Similar to AgentResponse but allows optional 'raw' field for debugging.

    Required Fields:
        success: Whether the skill execution succeeded (MUST be present)

    Optional Fields:
        data: Skill output (e.g., generated code, prompts, analysis results)
        error: Error message if success=False, None otherwise
        raw: Raw response text from external APIs for debugging
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
