"""
refactor_skill.py - 代码重构 Skill（占位）

# Fix: P1-01 - 空桩文件改为明确的 NotImplementedError

此 Skill 计划用于代码重构辅助，当前尚未实现。
"""

from typing import Dict, Any, List


def refactor_skill(
    task: str,
    target_files: List[str],
    **kwargs: Any
) -> Dict[str, Any]:
    """
    代码重构 Skill（未实现）。

    计划功能：
    - 分析现有代码结构
    - 生成重构建议
    - 输出重构后的代码

    Raises:
        NotImplementedError: 功能尚未实现
    """
    # Fix: P1-01 - 明确抛出 NotImplementedError 而非空白文件
    raise NotImplementedError(
        "refactor_skill 尚未实现。"
        "若需代码重构功能，请先实现此 Skill 或使用 fe_dev_skill/be_dev_skill。"
    )
