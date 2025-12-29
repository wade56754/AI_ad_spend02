#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置模块 - SoT 版本和角色定义

从 CLAUDE.md 和 SoT 文档同步的配置信息
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Set

# =============================================================================
# SoT 版本 (同步自 CLAUDE.md)
# =============================================================================

SOT_VERSIONS: Dict[str, str] = {
    "MASTER.md": "v4.6",
    "BUSINESS_RULES.md": "v4.6",
    "DATA_SCHEMA.md": "v5.6",
    "STATE_MACHINE.md": "v2.7",
}


def get_sot_versions() -> Dict[str, str]:
    """获取 SoT 文档版本"""
    return SOT_VERSIONS.copy()


# =============================================================================
# 角色定义 (PRD v2.2 / MASTER.md v4.6)
# =============================================================================

# 业务层合法角色列表 - 6 个核心角色
VALID_ROLES: Set[str] = {
    "ceo",              # 老板 - 资金安全、公司盈亏、最终决策
    "project_owner",    # 项目负责人 - 项目盈亏、日报审核、资金使用效率
    "finance",          # 财务 - 资金出入准确、数据真实、对账
    "pitcher",          # 投手 - CPL 达标、日报准确、执行投放
    "account_manager",  # 户管 - 账户分配、账户状态监控
    "admin",            # 管理员 - 系统配置（不参与业务）
}

# 技术层角色列表 (MASTER.md v4.6 §INV-007)
TECHNICAL_ROLES: Set[str] = {
    "admin",
    "finance",
    "account_manager",
    "media_buyer",      # 技术层别名，映射到 pitcher
}

# 废弃角色列表 (PRD v2.2 移除)
DEPRECATED_ROLES: Set[str] = {
    "supervisor",       # 已废弃 → 使用 project_owner
    "data_operator",    # 已废弃 → 使用 finance
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
    "raw_submitted",      # 已提交
    "trend_ok",           # 趋势确认
    "final_confirmed",    # 最终确认
}

# 充值状态 (7 个)
TOPUP_STATES: Set[str] = {
    "draft",              # 草稿
    "pending_review",     # 待审核
    "finance_approve",    # 财务已批准
    "paid",               # 已支付
    "completed",          # 已完成
    "rejected",           # 已拒绝
    "cancelled",          # 已取消
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
