"""
验证模块

功能:
- 来源追溯
- SoT 合规验证
"""

from .tracer import SourceTracer, TraceResult, TraceItem

__all__ = [
    "SourceTracer",
    "TraceResult",
    "TraceItem",
]
