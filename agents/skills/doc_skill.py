"""
doc_skill.py - 文档生成 Skill（占位）

# Fix: P1-01 - 空桩文件改为明确的 NotImplementedError

此 Skill 计划用于文档生成，当前由 DocAgent 直接实现模板渲染。
若需独立 Skill，请在此实现。
"""

from typing import Dict, Any


def doc_skill(action: str, doc_type: str, **kwargs: Any) -> Dict[str, Any]:
    """
    文档生成 Skill（未实现）。

    当前文档生成功能由 DocAgent 直接实现。
    此 Skill 预留用于未来抽象。

    Raises:
        NotImplementedError: 功能尚未实现
    """
    # Fix: P1-01 - 明确抛出 NotImplementedError 而非空白文件
    raise NotImplementedError(
        "doc_skill 尚未实现。文档生成功能当前由 DocAgent 直接处理。"
        "若需使用独立 Skill，请先实现此函数。"
    )
