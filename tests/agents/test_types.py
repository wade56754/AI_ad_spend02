"""
Common type definitions for agents and skills.

Provides standardized return structures to ensure consistent API contracts
across Agent and Skill layers.
"""

from typing import Any, Optional, TypedDict, Dict


class AgentResponse(TypedDict):
    """
    Standard response structure for all Agent.handle_request() calls.

    Fields:
        success: Whether the operation completed successfully
        data: Operation result (structure varies by agent type)
              - For BEAgent/FEAgent: {"changes": Dict[str, str], "notes": List[str]}
              - For TestAgent: {"prompt": str, "executed": bool, "reason": str}
              - For Orchestrator: {"flow": str, "message": str, "steps": Dict}
        error: Error message if success=False, None otherwise
    """

    success: bool
    data: Any
    error: Optional[str]


class SkillResult(TypedDict, total=False):
    """
    Standard response structure for Skill functions.

    Similar to AgentResponse but allows optional 'raw' field for debugging.
    Used when skills need to preserve raw API responses for error diagnosis.

    Fields:
        success: Whether the skill execution succeeded
        data: Skill output (e.g., generated code, prompts, analysis results)
        error: Error message if success=False, None otherwise
        raw: (Optional) Raw response text from external APIs for debugging
    """

    success: bool
    data: Any
    error: Optional[str]
    raw: str
