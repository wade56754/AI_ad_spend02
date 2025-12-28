"""
Guardrails 模块 - 编辑防护和错误恢复

借鉴 SWE-agent 的编辑前检查模式:
- 编辑前 ruff + ast 检查
- 失败自动修复
- 最多 3 次重试
"""

from .recovery_loop import EditGuardrails, EditResult, EditStatus
from .stats_tracker import GuardrailsStats

__all__ = [
    "EditGuardrails",
    "EditResult",
    "EditStatus",
    "GuardrailsStats",
]
