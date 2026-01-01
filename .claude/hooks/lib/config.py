#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置模块 - SoT 版本和角色定义

从 CLAUDE.md 和 SoT 文档同步的配置信息
支持从 sot-validator.yaml 动态加载配置

Version: 2.0.0
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Set

# YAML 支持 (可选)
try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# =============================================================================
# 项目根目录
# =============================================================================

PROJECT_ROOT = Path(
    __file__
).parent.parent.parent.parent  # .claude/hooks/lib → project root


# =============================================================================
# YAML 配置加载
# =============================================================================

_config_cache: Dict[str, Any] | None = None


def load_yaml_config() -> Dict[str, Any]:
    """
    加载 sot-validator.yaml 配置文件

    Returns:
        配置字典，如果文件不存在或无法加载则返回空字典
    """
    global _config_cache

    if _config_cache is not None:
        return _config_cache

    config_path = PROJECT_ROOT / ".claude" / "sot-validator.yaml"

    if not YAML_AVAILABLE:
        _config_cache = {}
        return _config_cache

    if not config_path.exists():
        _config_cache = {}
        return _config_cache

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            _config_cache = yaml.safe_load(f) or {}
    except Exception:
        _config_cache = {}

    return _config_cache


def get_config_value(path: str, default: Any = None) -> Any:
    """
    获取配置值 (支持点分路径)

    Args:
        path: 配置路径，如 "validation_rules.roles.whitelist"
        default: 默认值

    Returns:
        配置值
    """
    config = load_yaml_config()
    keys = path.split(".")
    value = config

    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default

    return value


# =============================================================================
# SoT 版本 (同步自 CLAUDE.md / sot-validator.yaml)
# =============================================================================

SOT_VERSIONS: Dict[str, str] = {
    "MASTER.md": "v4.8",
    "BUSINESS_RULES.md": "v4.8",
    "DATA_SCHEMA.md": "v5.7",
    "STATE_MACHINE.md": "v2.8",
}


def get_sot_versions() -> Dict[str, str]:
    """获取 SoT 文档版本"""
    return SOT_VERSIONS.copy()


# =============================================================================
# 角色定义 (PRD v2.2 / MASTER.md v4.6)
# =============================================================================

# 业务层合法角色列表 - 6 个核心角色
VALID_ROLES: Set[str] = {
    "ceo",  # 老板 - 资金安全、公司盈亏、最终决策
    "project_owner",  # 项目负责人 - 项目盈亏、日报审核、资金使用效率
    "finance",  # 财务 - 资金出入准确、数据真实、对账
    "pitcher",  # 投手 - CPL 达标、日报准确、执行投放
    "account_manager",  # 户管 - 账户分配、账户状态监控
    "admin",  # 管理员 - 系统配置（不参与业务）
}

# 技术层角色列表 (MASTER.md v4.6 §INV-007)
TECHNICAL_ROLES: Set[str] = {
    "admin",
    "finance",
    "account_manager",
    "media_buyer",  # 技术层别名，映射到 pitcher
}

# 废弃角色列表 (PRD v2.2 移除)
DEPRECATED_ROLES: Set[str] = {
    "supervisor",  # 已废弃 → 使用 project_owner
    "data_operator",  # 已废弃 → 使用 finance
}

# 角色映射 (废弃角色 → 正确角色)
ROLE_MAPPING: Dict[str, str] = {
    "supervisor": "project_owner",
    "data_operator": "finance",
    "media_buyer": "pitcher",
}


def get_valid_roles() -> Set[str]:
    """获取合法角色列表"""
    return VALID_ROLES.copy()


def get_deprecated_roles() -> Set[str]:
    """获取废弃角色列表"""
    return DEPRECATED_ROLES.copy()


def get_role_mapping() -> Dict[str, str]:
    """获取角色映射关系"""
    return ROLE_MAPPING.copy()


def is_valid_role(role: str) -> bool:
    """检查角色是否合法"""
    return role.lower() in VALID_ROLES


def is_deprecated_role(role: str) -> bool:
    """检查角色是否已废弃"""
    return role.lower() in DEPRECATED_ROLES


def get_correct_role(role: str) -> str | None:
    """获取废弃角色的正确替代"""
    return ROLE_MAPPING.get(role.lower())


# =============================================================================
# 状态定义 (STATE_MACHINE.md v2.7)
# =============================================================================

# 日报状态 (Phase 1: 3 个)
DAILY_REPORT_STATES: Set[str] = {
    "raw_submitted",  # 已提交
    "trend_ok",  # 趋势确认
    "final_confirmed",  # 最终确认
}

# 充值状态 (7 个)
TOPUP_STATES: Set[str] = {
    "draft",  # 草稿
    "pending_review",  # 待审核
    "finance_approve",  # 财务已批准
    "paid",  # 已支付
    "completed",  # 已完成
    "rejected",  # 已拒绝
    "cancelled",  # 已取消
}

# Phase 2 禁止状态 (Phase 1 不允许使用)
PHASE2_FORBIDDEN_STATES: Set[str] = {
    "trend_pending",
    "trend_flagged",
    "auto_rejected",
    "auto_suspended",
}


# =============================================================================
# Phase 1 约束
# =============================================================================

# Phase 2 禁止关键词
PHASE2_FORBIDDEN_KEYWORDS: Set[str] = {
    "auto_reject",
    "auto_suspend",
    "auto_block",
    "auto_freeze",
    "force_stop",
    "forced_approval",
}


# =============================================================================
# 高风险模块 (需要 OpenSpec 提案)
# =============================================================================

HIGH_RISK_MODULES: List[Dict[str, str]] = [
    {
        "id": "M8-LEDGER",
        "pattern": r"ledger|账本|LedgerEntry|ledger_entries",
        "action": "require_openspec",
        "reason": "账本模块涉及资金安全，修改需 OpenSpec 提案",
    },
    {
        "id": "M9-RECON",
        "pattern": r"recon|对账|reconciliation|Reconciliation",
        "action": "require_openspec",
        "reason": "对账模块涉及财务核对，修改需 OpenSpec 提案",
    },
    {
        "id": "M10-PROFIT",
        "pattern": r"profit|利润|gross_profit|net_profit",
        "action": "require_openspec",
        "reason": "利润模块涉及核心财务计算，修改需 OpenSpec 提案",
    },
    {
        "id": "M11-AUTH",
        "pattern": r"auth|认证|password|token|jwt|session",
        "action": "warn",
        "reason": "认证模块涉及安全，请谨慎修改",
    },
]


def get_high_risk_modules() -> List[Dict[str, str]]:
    """获取高风险模块列表 (优先从 YAML 配置加载)"""
    yaml_modules = get_config_value("high_risk_modules")
    if yaml_modules:
        return yaml_modules
    return HIGH_RISK_MODULES


def is_high_risk_file(filepath: str) -> Dict[str, str] | None:
    """
    检查文件是否涉及高风险模块

    Args:
        filepath: 文件路径

    Returns:
        高风险模块信息字典，如果不涉及则返回 None
    """
    import re

    filepath_lower = filepath.lower()

    for module in get_high_risk_modules():
        pattern = module.get("pattern", "")
        if re.search(pattern, filepath_lower, re.IGNORECASE):
            return module

    return None


# =============================================================================
# 当前 Phase 配置
# =============================================================================

CURRENT_PHASE: int = 1  # 当前处于 Phase 1


def get_current_phase() -> int:
    """获取当前 Phase (优先从 YAML 配置加载)"""
    yaml_phase = get_config_value("validation_rules.phases.current_phase")
    if yaml_phase is not None:
        return int(yaml_phase)
    return CURRENT_PHASE
