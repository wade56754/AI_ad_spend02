"""
Phase 功能开关 (细粒度)

版本: v1.0
创建日期: 2025-12-27
基准文档: MASTER.md v4.6 §3.4

功能:
- 细粒度功能开关 (禁止使用单一 SYSTEM_PHASE 开关)
- 每个功能独立控制
- 日报状态机 Phase 1/2 切换

环境变量:
- PHASE2_TOPUP_ENFORCEMENT: 充值强制审批
- PHASE2_DAILY_REPORT_REQUIRED: 强制日报提交
- ENABLE_FULL_DAILY_REPORT_SM: 启用完整 8 状态日报状态机
- PHASE2_WEEKLY_BRIEF_REQUIRED: 强制周报生成
- PHASE2_SETTLEMENT_LOCK: 结算数据锁定

注意:
- 本模块是对 phase_config.py 的增强封装
- 新功能应优先使用本模块的 FLAGS 实例
"""

from dataclasses import dataclass
from typing import List, Optional
import os
import logging

# 复用现有 phase_config 的核心功能
from backend.core.phase_config import (
    get_phase_config,
    PhaseConfig,
    Phase,
    log_phase_warning,
)

logger = logging.getLogger(__name__)


# ============================================================================
# 细粒度功能开关 (MASTER.md v4.6 §3.4)
# ============================================================================

@dataclass
class PhaseFlags:
    """
    细粒度功能开关 (MASTER.md v4.6 §3.4)

    每个功能独立控制，禁止使用单一 SYSTEM_PHASE 开关

    Attributes:
        PHASE2_TOPUP_ENFORCEMENT: 充值强制审批流程
        PHASE2_DAILY_REPORT_REQUIRED: 强制日报提交
        ENABLE_FULL_DAILY_REPORT_SM: 启用完整 8 状态日报状态机
        PHASE2_WEEKLY_BRIEF_REQUIRED: 强制周报生成
        PHASE2_SETTLEMENT_LOCK: 结算数据锁定
    """

    # ===== 充值模块 =====
    PHASE2_TOPUP_ENFORCEMENT: bool = False
    """充值强制审批流程 (Phase 2)"""

    # ===== 日报模块 =====
    PHASE2_DAILY_REPORT_REQUIRED: bool = False
    """强制日报提交 (Phase 2)"""

    ENABLE_FULL_DAILY_REPORT_SM: bool = False
    """启用完整 8 状态日报状态机 (Phase 2)"""

    # ===== 周报模块 =====
    PHASE2_WEEKLY_BRIEF_REQUIRED: bool = False
    """强制周报生成 (Phase 2)"""

    # ===== 结算模块 =====
    PHASE2_SETTLEMENT_LOCK: bool = False
    """结算数据锁定 (Phase 2)"""

    # ===== 负余额控制 =====
    PHASE2_NEGATIVE_BALANCE_BLOCK: bool = False
    """负余额阻断 (Phase 2)"""

    @classmethod
    def from_env(cls) -> "PhaseFlags":
        """从环境变量加载开关"""
        flags = cls(
            PHASE2_TOPUP_ENFORCEMENT=_env_bool("PHASE2_TOPUP_ENFORCEMENT"),
            PHASE2_DAILY_REPORT_REQUIRED=_env_bool("PHASE2_DAILY_REPORT_REQUIRED"),
            ENABLE_FULL_DAILY_REPORT_SM=_env_bool("ENABLE_FULL_DAILY_REPORT_SM"),
            PHASE2_WEEKLY_BRIEF_REQUIRED=_env_bool("PHASE2_WEEKLY_BRIEF_REQUIRED"),
            PHASE2_SETTLEMENT_LOCK=_env_bool("PHASE2_SETTLEMENT_LOCK"),
            PHASE2_NEGATIVE_BALANCE_BLOCK=_env_bool("PHASE2_NEGATIVE_BALANCE_BLOCK"),
        )
        logger.info(f"PhaseFlags loaded: {flags}")
        return flags

    def get_enabled_flags(self) -> List[str]:
        """获取已启用的开关列表"""
        enabled = []
        if self.PHASE2_TOPUP_ENFORCEMENT:
            enabled.append("PHASE2_TOPUP_ENFORCEMENT")
        if self.PHASE2_DAILY_REPORT_REQUIRED:
            enabled.append("PHASE2_DAILY_REPORT_REQUIRED")
        if self.ENABLE_FULL_DAILY_REPORT_SM:
            enabled.append("ENABLE_FULL_DAILY_REPORT_SM")
        if self.PHASE2_WEEKLY_BRIEF_REQUIRED:
            enabled.append("PHASE2_WEEKLY_BRIEF_REQUIRED")
        if self.PHASE2_SETTLEMENT_LOCK:
            enabled.append("PHASE2_SETTLEMENT_LOCK")
        if self.PHASE2_NEGATIVE_BALANCE_BLOCK:
            enabled.append("PHASE2_NEGATIVE_BALANCE_BLOCK")
        return enabled

    def __str__(self) -> str:
        enabled = self.get_enabled_flags()
        return f"PhaseFlags(enabled=[{', '.join(enabled) if enabled else 'None'}])"


def _env_bool(key: str) -> bool:
    """从环境变量读取布尔值"""
    return os.getenv(key, "").lower() == "true"


# ============================================================================
# 全局实例
# ============================================================================

_flags: Optional[PhaseFlags] = None


def get_flags() -> PhaseFlags:
    """获取全局 PhaseFlags 实例"""
    global _flags
    if _flags is None:
        _flags = PhaseFlags.from_env()
    return _flags


def reset_flags() -> None:
    """重置全局 PhaseFlags（用于测试）"""
    global _flags
    _flags = None


# 便捷访问
FLAGS = get_flags()


# ============================================================================
# 日报状态机辅助函数
# ============================================================================

# Phase 1 状态 (3 状态)
PHASE1_REPORT_STATES: List[str] = [
    'raw_submitted',
    'trend_ok',
    'final_confirmed'
]

# Phase 2 状态 (8 状态)
PHASE2_REPORT_STATES: List[str] = [
    'raw_submitted',
    'trend_pending',
    'trend_ok',
    'trend_flagged',
    'trend_resolved',
    'final_pending',
    'final_confirmed',
    'final_locked'
]


def get_allowed_report_states() -> List[str]:
    """
    返回当前允许的日报状态

    Returns:
        Phase 1: 3 状态列表
        Phase 2 (ENABLE_FULL_DAILY_REPORT_SM=true): 8 状态列表
    """
    flags = get_flags()
    if flags.ENABLE_FULL_DAILY_REPORT_SM:
        return PHASE2_REPORT_STATES.copy()
    return PHASE1_REPORT_STATES.copy()


def is_valid_report_state(state: str) -> bool:
    """
    检查日报状态是否在当前 Phase 允许范围内

    Args:
        state: 状态值

    Returns:
        bool: 是否合法
    """
    return state.lower().strip() in get_allowed_report_states()


# ============================================================================
# Phase 检查辅助函数
# ============================================================================

def should_block_on_limit() -> bool:
    """是否应该在超限时阻断（Phase 2 才阻断）"""
    return get_flags().PHASE2_TOPUP_ENFORCEMENT


def should_lock_settlement() -> bool:
    """是否应该锁定结算数据（Phase 2 才锁定）"""
    return get_flags().PHASE2_SETTLEMENT_LOCK


def should_enforce_approval() -> bool:
    """是否应该强制审批流程（Phase 2 才强制）"""
    return get_flags().PHASE2_TOPUP_ENFORCEMENT


def should_require_daily_report() -> bool:
    """是否应该强制日报提交（Phase 2 才强制）"""
    return get_flags().PHASE2_DAILY_REPORT_REQUIRED


def should_require_weekly_brief() -> bool:
    """是否应该强制周报生成（Phase 2 才强制）"""
    return get_flags().PHASE2_WEEKLY_BRIEF_REQUIRED


def should_block_negative_balance() -> bool:
    """是否应该阻止负余额投放（Phase 2 才阻止）"""
    return get_flags().PHASE2_NEGATIVE_BALANCE_BLOCK


# ============================================================================
# 兼容 phase_config 导出
# ============================================================================

# 保持向后兼容
__all__ = [
    # 新 API
    'PhaseFlags',
    'FLAGS',
    'get_flags',
    'reset_flags',
    'get_allowed_report_states',
    'is_valid_report_state',
    'should_block_on_limit',
    'should_lock_settlement',
    'should_enforce_approval',
    'should_require_daily_report',
    'should_require_weekly_brief',
    'should_block_negative_balance',
    # 状态常量
    'PHASE1_REPORT_STATES',
    'PHASE2_REPORT_STATES',
    # 兼容导出
    'get_phase_config',
    'PhaseConfig',
    'Phase',
    'log_phase_warning',
]
