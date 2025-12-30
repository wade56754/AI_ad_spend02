#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Risk Detector - 风险检测器存根模块

提供基本的风险检测功能。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class Risk:
    """风险信息"""
    id: str
    level: str  # low, medium, high, critical
    description: str
    file_path: Optional[str] = None


class RiskDetector:
    """风险检测器"""

    def __init__(self):
        self.risks: List[Risk] = []

    def detect(self, content: str, file_path: Optional[str] = None) -> List[Risk]:
        """检测内容中的风险"""
        # 简单的风险检测逻辑
        detected = []

        # 检测敏感词
        sensitive_patterns = [
            ("password", "medium", "Hardcoded password detected"),
            ("api_key", "high", "API key detected"),
            ("secret", "medium", "Secret value detected"),
            ("DELETE FROM", "high", "Destructive SQL detected"),
            ("DROP TABLE", "critical", "Destructive SQL detected"),
        ]

        content_lower = content.lower()
        for pattern, level, desc in sensitive_patterns:
            if pattern.lower() in content_lower:
                detected.append(Risk(
                    id=f"risk_{pattern}",
                    level=level,
                    description=desc,
                    file_path=file_path,
                ))

        self.risks.extend(detected)
        return detected

    def get_risks_by_level(self, level: str) -> List[Risk]:
        """按级别获取风险"""
        return [r for r in self.risks if r.level == level]

    def clear(self) -> None:
        """清空风险列表"""
        self.risks.clear()


# 单例实例
_detector: Optional[RiskDetector] = None


def get_detector() -> RiskDetector:
    """获取全局检测器实例"""
    global _detector
    if _detector is None:
        _detector = RiskDetector()
    return _detector


def generate_risk_report() -> str:
    """生成风险报告"""
    detector = get_detector()
    critical = len(detector.get_risks_by_level("critical"))
    high = len(detector.get_risks_by_level("high"))
    medium = len(detector.get_risks_by_level("medium"))
    low = len(detector.get_risks_by_level("low"))

    return f"Risks: Critical={critical} | High={high} | Medium={medium} | Low={low}"
