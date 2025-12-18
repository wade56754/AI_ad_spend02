"""
代码选型器 - SELECT 阶段实现

职责: 从候选代码中选择最佳参考方案

评估维度:
1. 技术栈匹配度 (30%)
2. 功能覆盖度 (30%)
3. 适配成本 (25%)
4. 代码质量 (15%)

来源:
- MetaGPT: 多维度决策框架
- Devika: 任务评估逻辑
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from .searcher import SearchCandidate


class AdaptationEffort(Enum):
    """适配工作量"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class EvaluationScores:
    """评估分数"""
    tech_stack_match: float = 0.0
    feature_coverage: float = 0.0
    adaptation_cost: float = 0.0
    code_quality: float = 0.0
    total: float = 0.0

    def calculate_total(self, weights: Dict[str, float] = None) -> float:
        """计算加权总分"""
        weights = weights or {
            "tech_stack_match": 0.30,
            "feature_coverage": 0.30,
            "adaptation_cost": 0.25,
            "code_quality": 0.15,
        }
        self.total = (
            self.tech_stack_match * weights["tech_stack_match"] +
            self.feature_coverage * weights["feature_coverage"] +
            self.adaptation_cost * weights["adaptation_cost"] +
            self.code_quality * weights["code_quality"]
        )
        return self.total


@dataclass
class AdaptationItem:
    """适配项"""
    type: str
    description: str
    effort: str


@dataclass
class AdaptationPlan:
    """适配方案"""
    base_code: str
    source: str
    modifications_needed: List[AdaptationItem] = field(default_factory=list)
    estimated_adaptation_rate: str = "0%"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_code": self.base_code,
            "source": self.source,
            "modifications_needed": [
                {"type": m.type, "description": m.description, "effort": m.effort}
                for m in self.modifications_needed
            ],
            "estimated_adaptation_rate": self.estimated_adaptation_rate,
        }


@dataclass
class SelectionResult:
    """选型结果"""
    success: bool
    selected: SearchCandidate = None
    scores: EvaluationScores = None
    adaptation_plan: AdaptationPlan = None
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    error: str = None


class CodeSelector:
    """
    代码选型器

    评估流程:
    1. 预筛选 (相关度/技术栈)
    2. 多维评估 (四维打分)
    3. 排序选择 (最佳 + 备选)
    4. 方案生成 (适配计划)
    """

    # 项目技术栈
    PROJECT_TECH_STACK = {
        "backend": {
            "language": "python",
            "framework": "fastapi",
            "orm": "sqlalchemy",
            "validation": "pydantic",
            "versions": {
                "python": "3.11+",
                "fastapi": "0.100+",
                "pydantic": "2.0+",
                "sqlalchemy": "2.0+",
            }
        },
        "frontend": {
            "language": "typescript",
            "framework": "nextjs",
            "ui": "shadcn",
            "state": "tanstack-query",
            "versions": {
                "nextjs": "14+",
                "react": "18+",
            }
        }
    }

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)

    def select(
        self,
        candidates: List[SearchCandidate],
        requirement: str,
        weights: Dict[str, float] = None,
        strict_mode: bool = False,
    ) -> SelectionResult:
        """
        执行选型

        Args:
            candidates: 搜索候选列表
            requirement: 原始需求
            weights: 自定义权重
            strict_mode: 严格模式 (技术栈不匹配直接淘汰)

        Returns:
            SelectionResult
        """
        if not candidates:
            return SelectionResult(
                success=False,
                error="没有候选代码可供选择",
            )

        weights = weights or {
            "tech_stack_match": 0.30,
            "feature_coverage": 0.30,
            "adaptation_cost": 0.25,
            "code_quality": 0.15,
        }

        # Step 1: 预筛选
        filtered = self._pre_filter(candidates, strict_mode)
        if not filtered:
            return SelectionResult(
                success=False,
                error="所有候选代码都被预筛选过滤",
            )

        # Step 2: 多维评估
        evaluated = []
        for candidate in filtered:
            scores = self._evaluate(candidate, requirement)
            scores.calculate_total(weights)
            evaluated.append((candidate, scores))

        # Step 3: 排序
        evaluated.sort(key=lambda x: x[1].total, reverse=True)

        # Step 4: 选择最佳 + 备选
        best_candidate, best_scores = evaluated[0]
        alternatives = [
            {
                "candidate_id": c.id,
                "total_score": s.total,
                "reason_not_selected": self._get_not_selected_reason(s, best_scores),
            }
            for c, s in evaluated[1:3]  # 前 2 个备选
        ]

        # Step 5: 生成适配方案
        adaptation_plan = self._generate_adaptation_plan(best_candidate, requirement)

        return SelectionResult(
            success=True,
            selected=best_candidate,
            scores=best_scores,
            adaptation_plan=adaptation_plan,
            alternatives=alternatives,
        )

    def _pre_filter(
        self,
        candidates: List[SearchCandidate],
        strict_mode: bool,
    ) -> List[SearchCandidate]:
        """预筛选"""
        filtered = []

        for candidate in candidates:
            # 相关度过滤
            if candidate.relevance_score < 30:
                continue

            # 严格模式下技术栈过滤
            if strict_mode and candidate.tech_stack_match < 50:
                continue

            filtered.append(candidate)

        return filtered

    def _evaluate(
        self,
        candidate: SearchCandidate,
        requirement: str,
    ) -> EvaluationScores:
        """多维评估"""
        scores = EvaluationScores()

        # 1. 技术栈匹配度
        scores.tech_stack_match = self._eval_tech_stack(candidate)

        # 2. 功能覆盖度
        scores.feature_coverage = self._eval_feature_coverage(candidate, requirement)

        # 3. 适配成本 (越低越好，转换为分数)
        scores.adaptation_cost = self._eval_adaptation_cost(candidate)

        # 4. 代码质量
        scores.code_quality = self._eval_code_quality(candidate)

        return scores

    def _eval_tech_stack(self, candidate: SearchCandidate) -> float:
        """评估技术栈匹配度"""
        # 使用候选项的 tech_stack_match 作为基础
        base_score = candidate.tech_stack_match

        # 根据来源调整
        source_bonus = {
            "local_project": 5,
            "code_library": 0,
            "github": -10,
        }.get(candidate.source, 0)

        # 根据语言调整
        language_match = 0
        if candidate.language == "python":
            language_match = 100
        elif candidate.language in ["typescript", "javascript"]:
            language_match = 100

        return min(100, base_score + source_bonus + language_match * 0.1)

    def _eval_feature_coverage(
        self,
        candidate: SearchCandidate,
        requirement: str,
    ) -> float:
        """评估功能覆盖度"""
        # 基于相关度分数
        base_score = candidate.relevance_score

        # 检查代码内容中的功能指标
        content = candidate.full_content.lower() if candidate.full_content else candidate.snippet.lower()

        feature_indicators = [
            ("class ", 10),
            ("def ", 10),
            ("async def", 15),
            ("return", 5),
            ("import", 5),
            ("from ", 5),
        ]

        bonus = 0
        for indicator, points in feature_indicators:
            if indicator in content:
                bonus += points

        return min(100, base_score * 0.7 + bonus)

    def _eval_adaptation_cost(self, candidate: SearchCandidate) -> float:
        """评估适配成本 (转换为分数: 成本低 = 分数高)"""
        # 本项目代码成本最低
        if candidate.source == "local_project":
            return 95

        # 代码资料库次之
        if candidate.source == "code_library":
            return 85

        # 外部代码成本高
        base = 70

        # 根据技术栈调整
        if candidate.tech_stack_match >= 80:
            base += 10
        elif candidate.tech_stack_match < 50:
            base -= 20

        return max(0, min(100, base))

    def _eval_code_quality(self, candidate: SearchCandidate) -> float:
        """评估代码质量"""
        content = candidate.full_content if candidate.full_content else candidate.snippet

        score = 50  # 基础分

        # 类型提示
        if ": " in content and "->" in content:
            score += 15

        # 文档字符串
        if '"""' in content or "'''" in content:
            score += 10

        # 错误处理
        if "try:" in content or "except" in content:
            score += 10

        # 导入规范
        if "from typing import" in content:
            score += 5

        # 代码长度适中
        lines = len(content.split("\n"))
        if 20 < lines < 200:
            score += 10

        return min(100, score)

    def _get_not_selected_reason(
        self,
        scores: EvaluationScores,
        best_scores: EvaluationScores,
    ) -> str:
        """获取未选择原因"""
        reasons = []

        if scores.tech_stack_match < best_scores.tech_stack_match - 10:
            reasons.append("技术栈匹配度较低")
        if scores.feature_coverage < best_scores.feature_coverage - 10:
            reasons.append("功能覆盖不足")
        if scores.adaptation_cost < best_scores.adaptation_cost - 10:
            reasons.append("适配成本较高")
        if scores.code_quality < best_scores.code_quality - 10:
            reasons.append("代码质量较差")

        if not reasons:
            reasons.append("综合评分略低")

        return "；".join(reasons)

    def _generate_adaptation_plan(
        self,
        candidate: SearchCandidate,
        requirement: str,
    ) -> AdaptationPlan:
        """生成适配方案"""
        modifications = []
        content = candidate.full_content if candidate.full_content else candidate.snippet

        # 检测需要的技术栈适配
        tech_adaptations = self._detect_tech_adaptations(content)
        modifications.extend(tech_adaptations)

        # 检测需要的项目规范适配
        standard_adaptations = self._detect_standard_adaptations(content)
        modifications.extend(standard_adaptations)

        # 估算适配率
        total_effort = sum(
            {"low": 1, "medium": 2, "high": 3}.get(m.effort, 2)
            for m in modifications
        )
        adaptation_rate = f"{min(95, max(30, 100 - total_effort * 5))}%"

        return AdaptationPlan(
            base_code=candidate.path,
            source=candidate.source,
            modifications_needed=modifications,
            estimated_adaptation_rate=adaptation_rate,
        )

    def _detect_tech_adaptations(self, content: str) -> List[AdaptationItem]:
        """检测技术栈适配需求"""
        adaptations = []

        # Pydantic v1 → v2
        if "class Config:" in content:
            adaptations.append(AdaptationItem(
                type="tech_stack",
                description="Pydantic v1 → v2: class Config → model_config",
                effort="low",
            ))

        if "@validator" in content:
            adaptations.append(AdaptationItem(
                type="tech_stack",
                description="Pydantic v1 → v2: @validator → @field_validator",
                effort="low",
            ))

        # SQLAlchemy 1 → 2
        if "session.query(" in content:
            adaptations.append(AdaptationItem(
                type="tech_stack",
                description="SQLAlchemy 1 → 2: session.query() → session.execute(select())",
                effort="medium",
            ))

        if "Column(" in content and "mapped_column" not in content:
            adaptations.append(AdaptationItem(
                type="tech_stack",
                description="SQLAlchemy 1 → 2: Column → mapped_column",
                effort="low",
            ))

        return adaptations

    def _detect_standard_adaptations(self, content: str) -> List[AdaptationItem]:
        """检测项目规范适配需求"""
        adaptations = []

        # 响应格式
        if "return {" in content and "success_response" not in content:
            adaptations.append(AdaptationItem(
                type="project_standard",
                description="响应格式: 使用 success_response() 包装",
                effort="low",
            ))

        # 错误处理
        if "HTTPException" in content and "BusinessError" not in content:
            adaptations.append(AdaptationItem(
                type="project_standard",
                description="错误处理: 使用 BusinessError + ERROR_CODES_SOT",
                effort="medium",
            ))

        # 导入路径
        if "from app." in content or "from src." in content:
            adaptations.append(AdaptationItem(
                type="project_standard",
                description="导入路径: 调整为 from backend.",
                effort="low",
            ))

        return adaptations
