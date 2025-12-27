"""
阶段模块 - 10 阶段流水线

Phase 0: INIT - 初始化
Phase 1: RISK - 风险评估
Phase 2: PARSE - 需求解析
Phase 3: SEARCH - 代码搜索
Phase 4: SELECT - 代码选型
Phase 5: ADAPT - 代码适配
Phase 6: ASSEMBLE - 代码组装
Phase 7: VERIFY - 代码验证
Phase 8: TRACE - 来源追溯
Phase 9: OUTPUT - 输出生成
"""

from .base import PhaseBase, PhaseResult
from .context import PipelineContext

__all__ = [
    "PhaseBase",
    "PhaseResult",
    "PipelineContext",
]
