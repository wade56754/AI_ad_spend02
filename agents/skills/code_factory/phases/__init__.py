"""
阶段模块 v7.0 - 轻量流水线

5 阶段架构 (对齐 Superpowers):
1. CLARIFY - 需求澄清 (对接 brainstorming)
2. PLAN - 计划生成 (对接 writing-plans)
3. IMPLEMENT - TDD 实现 (对接 test-driven-development)
4. REVIEW - 两阶段审查 (规格 + 质量)
5. CONFIRM - 幻觉抑制确认

版本: v7.0
基准: MASTER.md v4.8, Superpowers
"""

from .base import PhaseBase, PhaseResult
from .context import PipelineContext

# CLARIFY 阶段
from .clarify import (
    ClarifyPhase,
    ClarifyResult,
    ClarifiedRequirement,
    ClarifyQuestion,
    ClarityLevel,
    QuestionCategory,
    clarify_requirement,
    auto_clarify,
)

# PLAN 阶段 (v7.0)
from .plan import PlanPhase, PlanResult

# IMPLEMENT 阶段 (v7.0)
from .implement import ImplementPhase, TDDViolation, TDDPhase, TDDCycleResult

# REVIEW 阶段 (v7.0)
from .review import ReviewPhase, SpecReviewResult, QualityReviewResult

# CONFIRM 阶段 (v7.0)
from .confirm import ConfirmPhase, ConfirmResult, TraceResult

__all__ = [
    # 基类
    "PhaseBase",
    "PhaseResult",
    "PipelineContext",
    
    # CLARIFY 阶段
    "ClarifyPhase",
    "ClarifyResult",
    "ClarifiedRequirement",
    "ClarifyQuestion",
    "ClarityLevel",
    "QuestionCategory",
    "clarify_requirement",
    "auto_clarify",
    
    # PLAN 阶段 (v7.0)
    "PlanPhase",
    "PlanResult",
    
    # IMPLEMENT 阶段 (v7.0)
    "ImplementPhase",
    "TDDViolation",
    "TDDPhase",
    "TDDCycleResult",
    
    # REVIEW 阶段 (v7.0)
    "ReviewPhase",
    "SpecReviewResult",
    "QualityReviewResult",
    
    # CONFIRM 阶段 (v7.0)
    "ConfirmPhase",
    "ConfirmResult",
    "TraceResult",
]
