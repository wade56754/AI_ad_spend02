"""
Validation Tools - 通用参数校验工具

提供通用参数校验函数，减少 Agent 和 Skill 中的重复代码。
This is a copy from agents/tools/validation.py for agent_platform independence.
"""

from typing import Any, Dict, List, Optional

from .types import AgentResponse


def validate_task_and_files(
    task: str, target_files: List[str]
) -> Optional[AgentResponse]:
    """
    Validate task description and target file list.

    Args:
        task: Task description string
        target_files: List of file paths to modify

    Returns:
        None if validation passes (caller should proceed)
        AgentResponse with success=False if validation fails (caller should return immediately)

    Example:
        error = validate_task_and_files(task, files)
        if error:
            return error
        # proceed with task...
    """
    # Validate task
    if not task or not task.strip():
        return {
            "success": False,
            "data": None,
            "error": "Missing or empty 'task' field",
        }

    # Validate target_files
    if not target_files or not isinstance(target_files, list):
        return {
            "success": False,
            "data": None,
            "error": "Missing or invalid 'target_files' field (must be non-empty list)",
        }

    if not all(isinstance(item, str) and item.strip() for item in target_files):
        return {
            "success": False,
            "data": None,
            "error": "target_files must contain only non-empty strings",
        }

    return None


def validate_required_fields(
    data: Dict[str, Any],
    required: List[str],
) -> Optional[AgentResponse]:
    """
    Validate that required fields are present in data.

    Args:
        data: Dictionary to validate
        required: List of required field names

    Returns:
        None if validation passes
        AgentResponse with success=False if validation fails
    """
    missing = [f for f in required if f not in data or data[f] is None]
    if missing:
        return {
            "success": False,
            "data": None,
            "error": f"Missing required fields: {', '.join(missing)}",
        }
    return None


def validate_string_field(
    value: Any,
    field_name: str,
    min_length: int = 1,
    max_length: Optional[int] = None,
) -> Optional[AgentResponse]:
    """
    Validate a string field.

    Args:
        value: Value to validate
        field_name: Name of the field (for error messages)
        min_length: Minimum length (default 1)
        max_length: Maximum length (optional)

    Returns:
        None if validation passes
        AgentResponse with success=False if validation fails
    """
    if not isinstance(value, str):
        return {
            "success": False,
            "data": None,
            "error": f"'{field_name}' must be a string",
        }

    if len(value.strip()) < min_length:
        return {
            "success": False,
            "data": None,
            "error": f"'{field_name}' must be at least {min_length} characters",
        }

    if max_length and len(value) > max_length:
        return {
            "success": False,
            "data": None,
            "error": f"'{field_name}' must be at most {max_length} characters",
        }

    return None


__all__ = [
    "validate_task_and_files",
    "validate_required_fields",
    "validate_string_field",
]
