"""
风险评估模块

功能:
- 识别高风险模块
- 检测高风险关键词
- 阻断危险操作
"""

from .classifier import RiskClassifier, RiskLevel, RiskAssessment
from .keywords import HIGH_RISK_KEYWORDS, HIGH_RISK_MODULES

__all__ = [
    "RiskClassifier",
    "RiskLevel",
    "RiskAssessment",
    "HIGH_RISK_KEYWORDS",
    "HIGH_RISK_MODULES",
]
