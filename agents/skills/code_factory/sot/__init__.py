"""
SoT (Single Source of Truth) 模块 v7.0

提供:
- StructuredSotLoader: 结构化 YAML 配置加载 (推荐)
- SotLoader: 动态加载 SoT 文档 (兼容)
- SotParser: 解析 Markdown 表格 (兼容)
- DynamicWhitelist: 动态白名单管理

v7.0 变更:
- 新增 StructuredSotLoader 使用 YAML 配置
- 旧 SotLoader 保留用于向后兼容
"""

from .loader import SotLoader, LoadedSotData
from .parser import SotParser
from .whitelist import DynamicWhitelist

# v7.0: 结构化加载器 (推荐)
from .structured_loader import (
    StructuredSotLoader,
    SotConfig,
    RoleDefinition,
    StateDefinition,
    ErrorCodeDefinition,
    get_sot_config,
    validate_sot_config,
    is_valid_role,
    is_valid_daily_report_state,
    is_valid_error_code,
)

__all__ = [
    # v7.0 推荐接口
    "StructuredSotLoader",
    "SotConfig",
    "RoleDefinition",
    "StateDefinition",
    "ErrorCodeDefinition",
    "get_sot_config",
    "validate_sot_config",
    "is_valid_role",
    "is_valid_daily_report_state",
    "is_valid_error_code",
    # 兼容接口
    "SotLoader",
    "LoadedSotData",
    "SotParser",
    "DynamicWhitelist",
]
