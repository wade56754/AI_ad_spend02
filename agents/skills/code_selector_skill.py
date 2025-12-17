"""
code_selector_skill.py - 选型评估 Skill

代码来源说明 (Code Sources):
================================================================================
本 Skill 主要为自研规则引擎，但借鉴了以下开源项目的设计理念：

1. MetaGPT (MIT License)
   - GitHub: https://github.com/geekan/MetaGPT
   - 借鉴内容:
     - 多维度评估决策框架
     - 角色化评审模式 (Product Mgr / Architect 评估思路)

2. Devika (MIT License)
   - GitHub: https://github.com/stitionai/devika
   - 借鉴内容:
     - 任务分解评估逻辑
     - 决策制定模式
================================================================================

职责: 从候选代码中选择最佳参考方案
核心: 四维评估 + 加权评分 + 适配方案生成

基准对齐:
- CODE_FACTORY_REFERENCE_PROJECTS.md v1.0
- Agent Layer Freeze v1.0
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import logging

from .code_searcher_skill import SearchCandidate

logger = logging.getLogger(__name__)


# ============================================================================
# 数据类型定义
# ============================================================================

@dataclass
class EvaluationScores:
    """
    评估得分

    设计借鉴: MetaGPT 的多维度评估框架
    """
    tech_stack_match: float = 0.0
    feature_coverage: float = 0.0
    adaptation_cost: float = 0.0
    code_quality: float = 0.0
    historical_bonus: float = 0.0

    @property
    def total(self) -> float:
        """计算总分 (不含权重)"""
        return (
            self.tech_stack_match +
            self.feature_coverage +
            self.adaptation_cost +
            self.code_quality +
            self.historical_bonus
        )

    def to_dict(self) -> Dict[str, float]:
        return {
            "tech_stack_match": self.tech_stack_match,
            "feature_coverage": self.feature_coverage,
            "adaptation_cost": self.adaptation_cost,
            "code_quality": self.code_quality,
            "historical_bonus": self.historical_bonus,
            "total": self.total,
        }


@dataclass
class AdaptationItem:
    """适配项"""
    type: str
    description: str
    effort: str  # "low" | "medium" | "high"

    def to_dict(self) -> Dict[str, str]:
        return {
            "type": self.type,
            "description": self.description,
            "effort": self.effort,
        }


@dataclass
class AdaptationPlan:
    """
    适配方案

    包含将参考代码适配到项目的完整计划
    """
    base_code: str
    source: str
    modifications_needed: List[AdaptationItem] = field(default_factory=list)
    estimated_adaptation_rate: str = "80%"
    adaptation_hint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_code": self.base_code,
            "source": self.source,
            "modifications_needed": [m.to_dict() for m in self.modifications_needed],
            "estimated_adaptation_rate": self.estimated_adaptation_rate,
            "adaptation_hint": self.adaptation_hint,
        }


@dataclass
class SelectionResult:
    """选型结果"""
    selected: SearchCandidate
    scores: EvaluationScores
    adaptation_plan: AdaptationPlan
    alternatives: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected": self.selected.to_dict(),
            "scores": self.scores.to_dict(),
            "adaptation_plan": self.adaptation_plan.to_dict(),
            "alternatives": self.alternatives,
        }


# ============================================================================
# CodeSelectorSkill 主类
# ============================================================================

class CodeSelectorSkill:
    """
    选型评估 Skill

    架构设计借鉴:
    - MetaGPT: 多维度评估决策框架
    - Devika: 任务分解评估逻辑
    """

    # 默认评估权重
    DEFAULT_WEIGHTS = {
        "tech_stack_match": 0.30,
        "feature_coverage": 0.30,
        "adaptation_cost": 0.25,
        "code_quality": 0.15,
    }

    # 技术栈兼容性映射
    TECH_STACK_COMPATIBILITY = {
        # 完全兼容
        ("fastapi", "fastapi"): 100,
        ("nextjs", "nextjs"): 100,
        ("react", "react"): 100,
        ("pydantic", "pydantic"): 100,
        # 高度兼容
        ("express", "fastapi"): 70,
        ("flask", "fastapi"): 75,
        ("vue", "react"): 60,
        # 部分兼容
        ("django", "fastapi"): 50,
        ("angular", "react"): 40,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        初始化选型器

        Args:
            weights: 自定义评估权重
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
        logger.info(f"CodeSelectorSkill initialized: weights={self.weights}")

    def select(
        self,
        candidates: List[SearchCandidate],
        requirement: str,
        historical_success: Optional[Dict[str, float]] = None,
        strict_mode: bool = False,
    ) -> Dict[str, Any]:
        """
        选择最佳参考代码

        Args:
            candidates: 候选代码列表
            requirement: 原始需求描述
            historical_success: 历史成功率 (用于学习优化)
            strict_mode: 严格模式 (技术栈不匹配直接淘汰)

        Returns:
            选型结果
        """
        logger.info(
            f"Selection started: {len(candidates)} candidates, "
            f"requirement='{requirement[:50]}...'"
        )

        try:
            # 1. 预筛选
            filtered = self._pre_filter(candidates, strict_mode)

            if not filtered:
                return {
                    "success": False,
                    "data": None,
                    "error": "没有符合条件的候选代码",
                }

            # 2. 多维度评估
            scored_candidates = []
            for candidate in filtered:
                scores = self._evaluate(candidate, requirement)

                # 应用历史成功率加成
                if historical_success and candidate.id in historical_success:
                    scores.historical_bonus = historical_success[candidate.id] * 10

                total = self._calculate_weighted_score(scores)
                scored_candidates.append((candidate, scores, total))

            # 3. 排序
            scored_candidates.sort(key=lambda x: x[2], reverse=True)

            # 4. 选出最佳
            best_candidate, best_scores, best_total = scored_candidates[0]

            # 5. 生成适配方案
            adaptation_plan = self._create_adaptation_plan(
                best_candidate, requirement
            )

            # 6. 备选方案
            alternatives = [
                {
                    "candidate_id": c[0].id,
                    "total_score": c[2],
                    "reason_not_selected": self._explain_not_selected(c, scored_candidates[0]),
                }
                for c in scored_candidates[1:3]  # 前 2 个备选
            ]

            result = SelectionResult(
                selected=best_candidate,
                scores=best_scores,
                adaptation_plan=adaptation_plan,
                alternatives=alternatives,
            )

            logger.info(
                f"Selection completed: selected={best_candidate.id}, "
                f"score={best_total:.2f}"
            )

            return {
                "success": True,
                "data": result.to_dict(),
                "error": None,
            }

        except Exception as e:
            logger.error(f"Selection failed: {e}", exc_info=True)
            return {
                "success": False,
                "data": None,
                "error": str(e),
            }

    # ========================================================================
    # 预筛选
    # ========================================================================

    def _pre_filter(
        self,
        candidates: List[SearchCandidate],
        strict_mode: bool = False,
    ) -> List[SearchCandidate]:
        """
        预筛选候选代码

        借鉴: Devika 的任务分解评估逻辑
        """
        filtered = []

        for candidate in candidates:
            # 1. 过滤低相关度
            if candidate.relevance_score < 40:
                logger.debug(f"Filtered out (low relevance): {candidate.id}")
                continue

            # 2. 严格模式: 过滤技术栈不兼容
            if strict_mode and candidate.tech_stack_match < 50:
                logger.debug(f"Filtered out (tech stack): {candidate.id}")
                continue

            filtered.append(candidate)

        logger.info(f"Pre-filter: {len(candidates)} → {len(filtered)} candidates")
        return filtered

    # ========================================================================
    # 多维度评估
    # ========================================================================

    def _evaluate(
        self,
        candidate: SearchCandidate,
        requirement: str,
    ) -> EvaluationScores:
        """
        多维度评估候选代码

        借鉴: MetaGPT 的多维度评估框架
        """
        scores = EvaluationScores()

        # 1. 技术栈匹配度 (直接使用候选的值)
        scores.tech_stack_match = candidate.tech_stack_match

        # 2. 功能覆盖度 (基于相关度推算)
        scores.feature_coverage = self._assess_feature_coverage(candidate, requirement)

        # 3. 适配成本 (基于来源推算)
        scores.adaptation_cost = self._assess_adaptation_cost(candidate)

        # 4. 代码质量 (基于来源和有无代码片段推算)
        scores.code_quality = self._assess_code_quality(candidate)

        return scores

    def _assess_feature_coverage(
        self,
        candidate: SearchCandidate,
        requirement: str,
    ) -> float:
        """评估功能覆盖度"""
        # 基于相关度分数推算
        base_score = candidate.relevance_score

        # 有适配提示加分
        if candidate.adaptation_hint:
            base_score = min(100, base_score + 10)

        # 有代码片段加分
        if candidate.snippet:
            base_score = min(100, base_score + 5)

        return base_score

    def _assess_adaptation_cost(self, candidate: SearchCandidate) -> float:
        """
        评估适配成本 (分数越高表示成本越低)

        优先级策略 (2025-12-18 更新):
        - GitHub 外部代码优先 (经过社区验证，质量可靠)
        - 本项目代码由 AI 生成，可靠性较低
        """
        cost_by_source = {
            "github": 90,          # GitHub 可靠代码，适配成本低
            "code_library": 80,    # 已验证的参考
            "local_project": 60,   # 本项目 AI 生成代码，需要更多验证
        }

        base_score = cost_by_source.get(candidate.source, 50)

        # 技术栈匹配度影响适配成本
        if candidate.tech_stack_match >= 90:
            base_score = min(100, base_score + 5)
        elif candidate.tech_stack_match < 70:
            base_score = max(30, base_score - 10)

        # 有代码示例的适配成本更低
        if candidate.snippet and len(candidate.snippet) > 100:
            base_score = min(100, base_score + 10)

        return base_score

    def _assess_code_quality(self, candidate: SearchCandidate) -> float:
        """
        评估代码质量

        优先级策略 (2025-12-18 更新):
        - GitHub 外部代码经过社区审查，质量更高
        - 本项目 AI 生成代码质量较低
        """
        # GitHub 代码经过社区审查
        if candidate.source == "github":
            base_score = 90
            # 有代码示例说明参考完整
            if candidate.snippet and len(candidate.snippet) > 100:
                base_score = min(100, base_score + 5)
            return base_score

        # 代码资料库已验证
        if candidate.source == "code_library":
            base_score = 75
            if candidate.snippet:
                base_score = min(100, base_score + 5)
            return base_score

        # 本项目 AI 生成代码
        return 60

    # ========================================================================
    # 评分计算
    # ========================================================================

    def _calculate_weighted_score(self, scores: EvaluationScores) -> float:
        """计算加权总分"""
        total = 0.0

        total += scores.tech_stack_match * self.weights.get("tech_stack_match", 0.30)
        total += scores.feature_coverage * self.weights.get("feature_coverage", 0.30)
        total += scores.adaptation_cost * self.weights.get("adaptation_cost", 0.25)
        total += scores.code_quality * self.weights.get("code_quality", 0.15)
        total += scores.historical_bonus  # 历史加成直接加

        return total

    # ========================================================================
    # 适配方案生成
    # ========================================================================

    def _create_adaptation_plan(
        self,
        candidate: SearchCandidate,
        requirement: str,
    ) -> AdaptationPlan:
        """
        创建适配方案

        标准适配检查项:
        1. 技术栈适配
        2. 项目规范适配
        3. SoT 合规适配
        4. 功能定制
        """
        modifications = []

        # 1. 技术栈适配
        if candidate.tech_stack_match < 100:
            effort = "low" if candidate.tech_stack_match > 90 else "medium"
            modifications.append(AdaptationItem(
                type="技术栈适配",
                description="检查 Pydantic/SQLAlchemy/FastAPI 版本兼容性",
                effort=effort,
            ))

        # 2. 项目规范适配
        if candidate.source != "local_project":
            modifications.append(AdaptationItem(
                type="项目规范适配",
                description="使用项目标准响应格式 (StandardResponse) 和错误码",
                effort="low",
            ))

        # 3. SoT 合规适配
        modifications.append(AdaptationItem(
            type="SoT 合规适配",
            description="检查字段/状态/类型定义是否符合 DATA_SCHEMA 和 STATE_MACHINE",
            effort="medium",
        ))

        # 4. 功能定制
        modifications.append(AdaptationItem(
            type="功能定制",
            description=f"按需求调整: {requirement[:50]}...",
            effort="medium",
        ))

        # 计算预估适配率
        adaptation_rate = self._estimate_adaptation_rate(candidate)

        return AdaptationPlan(
            base_code=candidate.path,
            source=candidate.source,
            modifications_needed=modifications,
            estimated_adaptation_rate=adaptation_rate,
            adaptation_hint=candidate.adaptation_hint,
        )

    def _estimate_adaptation_rate(self, candidate: SearchCandidate) -> str:
        """估算适配率 (保留多少原代码)"""
        if candidate.source == "local_project":
            return "90%+"

        if candidate.tech_stack_match >= 90:
            return "80-90%"
        elif candidate.tech_stack_match >= 70:
            return "60-80%"
        else:
            return "40-60%"

    # ========================================================================
    # 解释说明
    # ========================================================================

    def _explain_not_selected(
        self,
        candidate_tuple: tuple,
        best_tuple: tuple,
    ) -> str:
        """解释为什么没被选中"""
        candidate, scores, total = candidate_tuple
        best_candidate, best_scores, best_total = best_tuple

        # 分数差距较大
        if total < best_total - 10:
            return "综合评分较低"

        # 找出最大差距的维度
        dimension_diffs = [
            ("技术栈匹配", best_scores.tech_stack_match - scores.tech_stack_match),
            ("功能覆盖", best_scores.feature_coverage - scores.feature_coverage),
            ("适配成本", best_scores.adaptation_cost - scores.adaptation_cost),
            ("代码质量", best_scores.code_quality - scores.code_quality),
        ]

        max_diff = max(dimension_diffs, key=lambda x: x[1])

        if max_diff[1] > 5:
            return f"{max_diff[0]}评分较低"

        return "综合评分略低"


# ============================================================================
# Skill 入口函数
# ============================================================================

def code_selector_skill(
    candidates: List[Dict[str, Any]],
    requirement: str,
    weights: Optional[Dict[str, float]] = None,
    historical_success: Optional[Dict[str, float]] = None,
    strict_mode: bool = False,
) -> Dict[str, Any]:
    """
    选型评估 Skill 入口函数

    代码来源: 自研规则引擎，借鉴 MetaGPT + Devika 设计理念

    Args:
        candidates: 候选代码列表 (字典格式)
        requirement: 原始需求描述
        weights: 自定义评估权重
        historical_success: 历史成功率
        strict_mode: 严格模式

    Returns:
        选型结果
    """
    # 转换字典为 SearchCandidate 对象
    search_candidates = [
        SearchCandidate(
            id=c.get("id", f"candidate-{i}"),
            source=c.get("source", "unknown"),
            path=c.get("path", ""),
            relevance_score=c.get("relevance_score", 0),
            snippet=c.get("snippet", ""),
            match_reason=c.get("match_reason", ""),
            tech_stack_match=c.get("tech_stack_match", 80),
            adaptation_hint=c.get("adaptation_hint"),
        )
        for i, c in enumerate(candidates)
    ]

    selector = CodeSelectorSkill(weights=weights)
    return selector.select(
        candidates=search_candidates,
        requirement=requirement,
        historical_success=historical_success,
        strict_mode=strict_mode,
    )


__all__ = [
    "CodeSelectorSkill",
    "SelectionResult",
    "AdaptationPlan",
    "code_selector_skill",
]
