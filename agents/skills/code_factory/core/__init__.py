"""
AI 代码工厂 v4.4 - 核心模块

包含:
- factory.py: 主编排器 (含 Phase 6 CONFIRM)
- config.py: 配置类
- feature_flags.py: 功能开关
- exceptions.py: 自定义异常
- constants.py: 常量定义
"""

from .config import FactoryConfig
from .feature_flags import FeatureFlags, get_flags
from .exceptions import (
    CodeFactoryError,
    SotVersionMismatchError,
    RiskBlockedError,
    TraceFailedError,
    EditRejectedError,
)
from .constants import VERSION, PHASE_NAMES

__all__ = [
    "FactoryConfig",
    "FeatureFlags",
    "get_flags",
    "CodeFactoryError",
    "SotVersionMismatchError",
    "RiskBlockedError",
    "TraceFailedError",
    "EditRejectedError",
    "VERSION",
    "PHASE_NAMES",
]
