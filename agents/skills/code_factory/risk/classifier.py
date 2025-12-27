"""
风险分类器

基准文档: MASTER.md v4.6
版本: v4.2

功能:
- 评估需求风险等级
- 识别高风险模块
- 生成风险报告
"""

from dataclasses import dataclass, field
from typing import List, Optional, Set
from enum import Enum

from .keywords import (
    HIGH_RISK_KEYWORDS,
    HIGH_RISK_MODULES,
    MEDIUM_RISK_KEYWORDS,
)


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"           # 低风险，可自动处理
    MEDIUM = "medium"     # 中等风险，需要确认
    HIGH = "high"         # 高风险，需要人工审核
    BLOCKED = "blocked"   # 阻断，禁止自动生成


@dataclass
class RiskAssessment:
    """风险评估结果"""

    level: RiskLevel
    score: int = 0  # 0-100

    # 触发因素
    matched_keywords: List[str] = field(default_factory=list)
    matched_modules: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)

    # 建议
    recommendations: List[str] = field(default_factory=list)

    @property
    def is_blocked(self) -> bool:
        return self.level == RiskLevel.BLOCKED

    @property
    def needs_confirmation(self) -> bool:
        return self.level in (RiskLevel.MEDIUM, RiskLevel.HIGH)

    def to_dict(self) -> dict:
        return {
            "level": self.level.value,
            "score": self.score,
            "matched_keywords": self.matched_keywords,
            "matched_modules": self.matched_modules,
            "reasons": self.reasons,
            "recommendations": self.recommendations,
        }

    def to_report(self) -> str:
        """生成风险报告"""
        lines = [
            "=" * 40,
            f"风险评估报告 - 等级: {self.level.value.upper()}",
            "=" * 40,
            f"风险分数: {self.score}/100",
            "",
        ]

        if self.matched_keywords:
            lines.append("匹配关键词:")
            for kw in self.matched_keywords:
                lines.append(f"  - {kw}")

        if self.matched_modules:
            lines.append("匹配模块:")
            for mod in self.matched_modules:
                lines.append(f"  - {mod}")

        if self.reasons:
            lines.append("")
            lines.append("风险原因:")
            for reason in self.reasons:
                lines.append(f"  - {reason}")

        if self.recommendations:
            lines.append("")
            lines.append("建议:")
            for rec in self.recommendations:
                lines.append(f"  - {rec}")

        return "\n".join(lines)


class RiskClassifier:
    """风险分类器"""

    def __init__(
        self,
        high_risk_keywords: Optional[Set[str]] = None,
        high_risk_modules: Optional[Set[str]] = None,
        medium_risk_keywords: Optional[Set[str]] = None,
    ):
        """初始化

        Args:
            high_risk_keywords: 高风险关键词
            high_risk_modules: 高风险模块
            medium_risk_keywords: 中等风险关键词
        """
        self.high_risk_keywords = high_risk_keywords or HIGH_RISK_KEYWORDS
        self.high_risk_modules = high_risk_modules or HIGH_RISK_MODULES
        self.medium_risk_keywords = medium_risk_keywords or MEDIUM_RISK_KEYWORDS

    def assess(
        self,
        requirement: str,
        module_id: Optional[str] = None,
    ) -> RiskAssessment:
        """评估风险

        Args:
            requirement: 需求描述
            module_id: 模块 ID

        Returns:
            RiskAssessment
        """
        assessment = RiskAssessment(level=RiskLevel.LOW)
        req_lower = requirement.lower()

        # 1. 检查高风险模块
        if module_id:
            if module_id.upper() in self.high_risk_modules:
                assessment.level = RiskLevel.BLOCKED
                assessment.score = 100
                assessment.matched_modules.append(module_id)
                assessment.reasons.append(f"模块 {module_id} 被标记为高风险")
                assessment.recommendations.append("请手动实现此模块，或联系架构师评审")
                return assessment

        # 2. 检查高风险关键词
        high_matches = []
        for keyword in self.high_risk_keywords:
            if keyword.lower() in req_lower:
                high_matches.append(keyword)

        if high_matches:
            assessment.matched_keywords.extend(high_matches)
            assessment.score += len(high_matches) * 20

            if len(high_matches) >= 2:
                assessment.level = RiskLevel.BLOCKED
                assessment.reasons.append(f"检测到多个高风险关键词: {', '.join(high_matches)}")
                assessment.recommendations.append("此需求涉及财务/安全核心，请手动实现")
            else:
                assessment.level = RiskLevel.HIGH
                assessment.reasons.append(f"检测到高风险关键词: {high_matches[0]}")
                assessment.recommendations.append("请仔细审核生成的代码")

        # 3. 检查中等风险关键词
        medium_matches = []
        for keyword in self.medium_risk_keywords:
            if keyword.lower() in req_lower:
                medium_matches.append(keyword)

        if medium_matches:
            assessment.matched_keywords.extend(medium_matches)
            assessment.score += len(medium_matches) * 10

            if assessment.level == RiskLevel.LOW:
                assessment.level = RiskLevel.MEDIUM
                assessment.reasons.append(f"检测到中等风险关键词: {', '.join(medium_matches)}")
                assessment.recommendations.append("建议在生成后进行代码审核")

        # 4. 评估需求复杂度
        complexity_indicators = [
            ("多个", 5), ("批量", 5), ("全部", 10),
            ("同时", 5), ("并且", 3), ("以及", 3),
        ]
        for indicator, points in complexity_indicators:
            if indicator in requirement:
                assessment.score += points

        # 确保分数在 0-100 范围内
        assessment.score = min(100, max(0, assessment.score))

        return assessment

    def is_safe(self, requirement: str, module_id: Optional[str] = None) -> bool:
        """快速检查是否安全

        Args:
            requirement: 需求描述
            module_id: 模块 ID

        Returns:
            True 如果是低风险或中等风险
        """
        assessment = self.assess(requirement, module_id)
        return assessment.level in (RiskLevel.LOW, RiskLevel.MEDIUM)

    def is_blocked(self, requirement: str, module_id: Optional[str] = None) -> bool:
        """快速检查是否被阻断

        Args:
            requirement: 需求描述
            module_id: 模块 ID

        Returns:
            True 如果被阻断
        """
        assessment = self.assess(requirement, module_id)
        return assessment.level == RiskLevel.BLOCKED
