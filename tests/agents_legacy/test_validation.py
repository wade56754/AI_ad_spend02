"""
validation.py

提供通用参数校验函数，减少 Agent 和 Skill 中的重复代码。
"""

from typing import Dict, Any, List, Optional

from agents.tools.types import AgentResponse

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
    """
    # 校验 task
    if not task or not task.strip():
        return {
            "success": False,
            "data": None,
            "error": "Missing or empty 'task' field",
        }

    # 校验 target_files
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
