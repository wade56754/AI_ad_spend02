# -*- coding: utf-8 -*-
"""
状态机断言辅助函数

提供状态断言和状态流转验证函数，确保测试符合 STATE_MACHINE.md v2.6 规范。

基准文档: AUTOMATION_TEST_SPEC_v1.4.md 第 3.3 节
SoT 依赖: STATE_MACHINE.md v2.6
"""

from typing import Any, Set, Dict, Optional

# ============================================================================
# DailyReport 8 状态机定义
# SoT Ref: STATE_MACHINE.md v2.6 第 8 章
# ============================================================================

DAILY_REPORT_STATES: Set[str] = {
    "raw_submitted",
    "trend_pending",
    "trend_ok",
    "trend_flagged",
    "trend_resolved",
    "final_pending",
    "final_confirmed",
    "final_locked",
}

DAILY_REPORT_TRANSITIONS: Dict[str, Set[str]] = {
    "raw_submitted": {"trend_pending"},
    "trend_pending": {"trend_ok", "trend_flagged"},
    "trend_ok": {"final_pending"},
    "trend_flagged": {"trend_resolved"},
    "trend_resolved": {"final_pending"},
    "final_pending": {"final_confirmed"},
    "final_confirmed": {"final_locked"},
    "final_locked": set(),  # 终态，无后续转换
}

DAILY_REPORT_TERMINAL_STATES: Set[str] = {"final_locked"}

# ============================================================================
# Topup 状态机定义
# SoT Ref: STATE_MACHINE.md v2.6 第 9 章
# ============================================================================

TOPUP_STATES: Set[str] = {
    "pending",
    "approved",
    "rejected",
    "completed",
    "cancelled",
}

TOPUP_TRANSITIONS: Dict[str, Set[str]] = {
    "pending": {"approved", "rejected"},
    "approved": {"completed", "cancelled"},
    "rejected": set(),  # 终态
    "completed": set(),  # 终态
    "cancelled": set(),  # 终态
}

TOPUP_TERMINAL_STATES: Set[str] = {"rejected", "completed", "cancelled"}

# ============================================================================
# Reconciliation 状态机定义
# SoT Ref: STATE_MACHINE.md v2.6 第 10 章
# ============================================================================

RECONCILIATION_STATES: Set[str] = {
    "pending",
    "in_progress",
    "matched",
    "discrepancy",
    "resolved",
    "closed",
}

RECONCILIATION_TRANSITIONS: Dict[str, Set[str]] = {
    "pending": {"in_progress"},
    "in_progress": {"matched", "discrepancy"},
    "matched": {"closed"},
    "discrepancy": {"resolved"},
    "resolved": {"closed"},
    "closed": set(),  # 终态
}

RECONCILIATION_TERMINAL_STATES: Set[str] = {"closed"}

# ============================================================================
# Transfer 状态机定义
# SoT Ref: STATE_MACHINE.md v2.6 第 12 章
# ============================================================================

TRANSFER_STATES: Set[str] = {
    "draft",
    "pending_approval",
    "approved",
    "rejected",
    "completed",
}

TRANSFER_TRANSITIONS: Dict[str, Set[str]] = {
    "draft": {"pending_approval", "rejected"},
    "pending_approval": {"approved", "rejected"},
    "approved": {"completed"},
    "rejected": set(),  # 终态
    "completed": set(),  # 终态
}

TRANSFER_TERMINAL_STATES: Set[str] = {"rejected", "completed"}


# ============================================================================
# 断言函数
# ============================================================================

def assert_daily_report_state(
    entity: Any,
    expected_state: str,
    msg: Optional[str] = None
) -> None:
    """
    断言 DailyReport 实体处于预期状态

    Args:
        entity: DailyReport 实体或字典
        expected_state: 预期状态
        msg: 自定义错误消息

    Raises:
        AssertionError: 状态不匹配或状态无效

    SoT Ref: STATE_MACHINE.md v2.6 第 8 章
    """
    if expected_state not in DAILY_REPORT_STATES:
        raise AssertionError(
            f"无效的 DailyReport 状态: {expected_state}。"
            f"有效状态: {DAILY_REPORT_STATES}"
        )

    actual_state = _get_status(entity)
    if actual_state != expected_state:
        error_msg = msg or (
            f"DailyReport 状态断言失败: "
            f"期望 '{expected_state}'，实际 '{actual_state}'"
        )
        raise AssertionError(error_msg)


def assert_topup_state(
    entity: Any,
    expected_state: str,
    msg: Optional[str] = None
) -> None:
    """
    断言 Topup 实体处于预期状态

    Args:
        entity: Topup 实体或字典
        expected_state: 预期状态
        msg: 自定义错误消息

    Raises:
        AssertionError: 状态不匹配或状态无效

    SoT Ref: STATE_MACHINE.md v2.6 第 9 章
    """
    if expected_state not in TOPUP_STATES:
        raise AssertionError(
            f"无效的 Topup 状态: {expected_state}。"
            f"有效状态: {TOPUP_STATES}"
        )

    actual_state = _get_status(entity)
    if actual_state != expected_state:
        error_msg = msg or (
            f"Topup 状态断言失败: "
            f"期望 '{expected_state}'，实际 '{actual_state}'"
        )
        raise AssertionError(error_msg)


def assert_reconciliation_state(
    entity: Any,
    expected_state: str,
    msg: Optional[str] = None
) -> None:
    """
    断言 Reconciliation 实体处于预期状态

    Args:
        entity: Reconciliation 实体或字典
        expected_state: 预期状态
        msg: 自定义错误消息

    Raises:
        AssertionError: 状态不匹配或状态无效

    SoT Ref: STATE_MACHINE.md v2.6 第 10 章
    """
    if expected_state not in RECONCILIATION_STATES:
        raise AssertionError(
            f"无效的 Reconciliation 状态: {expected_state}。"
            f"有效状态: {RECONCILIATION_STATES}"
        )

    actual_state = _get_status(entity)
    if actual_state != expected_state:
        error_msg = msg or (
            f"Reconciliation 状态断言失败: "
            f"期望 '{expected_state}'，实际 '{actual_state}'"
        )
        raise AssertionError(error_msg)


def assert_state_transition_valid(
    entity_type: str,
    from_state: str,
    to_state: str,
    msg: Optional[str] = None
) -> None:
    """
    断言状态转换符合状态机白名单

    Args:
        entity_type: 实体类型 ('daily_report', 'topup', 'reconciliation')
        from_state: 源状态
        to_state: 目标状态
        msg: 自定义错误消息

    Raises:
        AssertionError: 转换不在白名单中

    SoT Ref: STATE_MACHINE.md v2.6 第 4 章 (状态流转白名单)
    """
    transitions_map = {
        "daily_report": DAILY_REPORT_TRANSITIONS,
        "topup": TOPUP_TRANSITIONS,
        "reconciliation": RECONCILIATION_TRANSITIONS,
        "transfer_requests": TRANSFER_TRANSITIONS,
    }

    if entity_type not in transitions_map:
        raise AssertionError(f"未知的实体类型: {entity_type}")

    transitions = transitions_map[entity_type]

    if from_state not in transitions:
        raise AssertionError(f"无效的源状态: {from_state}")

    valid_targets = transitions[from_state]
    if to_state not in valid_targets:
        error_msg = msg or (
            f"{entity_type} 状态转换非法: "
            f"'{from_state}' → '{to_state}'。"
            f"允许的目标状态: {valid_targets}"
        )
        raise AssertionError(error_msg)


def _get_status(entity: Any) -> str:
    """从实体或字典中提取状态值"""
    if isinstance(entity, dict):
        return entity.get("status", "")
    return getattr(entity, "status", "")
