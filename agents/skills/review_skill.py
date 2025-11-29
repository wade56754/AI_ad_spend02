"""
review_skill.py - 代码审核 Skill（占位）

# Fix: P1-01 - 空桩文件改为明确的 NotImplementedError

此 Skill 计划用于代码审核，当前由 CodeReviewAgent + sot_guard_skill 实现。
若需独立 Skill，请在此实现。
"""

from typing import Dict, Any


def review_skill(changes: Dict[str, str], **kwargs: Any) -> Dict[str, Any]:
    """
    代码审核 Skill（未实现）。

    当前代码审核功能由 CodeReviewAgent 调用 sot_guard_skill 实现。
    此 Skill 预留用于未来抽象。

    Raises:
        NotImplementedError: 功能尚未实现
    """
    # Fix: P1-01 - 明确抛出 NotImplementedError 而非空白文件
    raise NotImplementedError(
        "review_skill 尚未实现。代码审核功能当前由 CodeReviewAgent + sot_guard_skill 处理。"
        "若需使用独立 Skill，请先实现此函数。"
    )
