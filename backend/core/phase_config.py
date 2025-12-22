"""
Phase Configuration System - Phase 1/2 边界管理

基准文档: MASTER.md v4.4 §8 Phase 1/2 定义
版本: v1.0
创建日期: 2025-12-22

功能:
- 管理 Phase 1（照亮不问责）和 Phase 2（问责与约束）的配置
- 通过环境变量控制 Phase 2 功能开关
- 为业务服务提供 Phase 边界检查

Phase 1 (照亮):
- 记录 + 提示 + 高亮，不阻断流程
- 允许负余额投放（仅警告）
- 日报未提交仅提醒

Phase 2 (问责):
- 强制校验 + 审批 + 考核
- 不允许负余额投放
- 日报未提交自动暂停
"""

from enum import Enum
from pydantic import BaseModel, Field
import os
import logging
from typing import Optional, Callable, TypeVar, Any
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Phase(str, Enum):
    """Phase 枚举

    - PHASE1: 照亮不问责 - 记录+提示+高亮，不阻断流程
    - PHASE2: 问责与约束 - 强制校验+审批+考核
    """
    PHASE1 = "phase1"  # 照亮：记录+提示+高亮
    PHASE2 = "phase2"  # 问责：约束+审批+考核


class PhaseConfig(BaseModel):
    """Phase 配置模型

    环境变量:
        FACTORY_PHASE: "phase1" | "phase2" (默认 phase1)
        PHASE2_TOPUP_ENFORCEMENT: "true" | "false" (默认 false)
        PHASE2_DAILY_REPORT_REQUIRED: "true" | "false" (默认 false)
        PHASE2_NEGATIVE_BALANCE_BLOCK: "true" | "false" (默认 false)
        PHASE2_SETTLEMENT_LOCK: "true" | "false" (默认 false)

    示例:
        >>> config = PhaseConfig.from_env()
        >>> if config.is_phase2_enabled():
        ...     # 执行 Phase 2 强制验证
        ...     pass
    """

    phase: Phase = Field(
        default=Phase.PHASE1,
        description="当前 Phase（phase1 或 phase2）"
    )

    # Phase 2 功能开关 (MASTER.md v4.4 §8.2.3)
    topup_enforcement: bool = Field(
        default=False,
        description="充值强制校验：必须有足够预算才能申请（Phase 2）"
    )

    daily_report_required: bool = Field(
        default=False,
        description="日报强制填报：超过 N 天未提交则自动暂停（Phase 2）"
    )

    negative_balance_block: bool = Field(
        default=False,
        description="负余额阻断：不允许负余额投放（Phase 2）"
    )

    settlement_lock: bool = Field(
        default=False,
        description="结算期锁定：禁止修改已结算期间数据（Phase 2）"
    )

    @classmethod
    def from_env(cls) -> "PhaseConfig":
        """从环境变量加载配置

        Returns:
            PhaseConfig: 根据环境变量构建的配置实例
        """
        phase_str = os.getenv("FACTORY_PHASE", "phase1").lower()

        # 验证 phase 值
        if phase_str not in ["phase1", "phase2"]:
            logger.warning(
                f"Invalid FACTORY_PHASE value: {phase_str}. "
                f"Defaulting to 'phase1'"
            )
            phase_str = "phase1"

        config = cls(
            phase=Phase(phase_str),
            topup_enforcement=os.getenv("PHASE2_TOPUP_ENFORCEMENT", "false").lower() == "true",
            daily_report_required=os.getenv("PHASE2_DAILY_REPORT_REQUIRED", "false").lower() == "true",
            negative_balance_block=os.getenv("PHASE2_NEGATIVE_BALANCE_BLOCK", "false").lower() == "true",
            settlement_lock=os.getenv("PHASE2_SETTLEMENT_LOCK", "false").lower() == "true"
        )

        logger.info(f"PhaseConfig loaded: {config}")
        return config

    def is_phase2_enabled(self) -> bool:
        """检查是否启用 Phase 2"""
        return self.phase == Phase.PHASE2

    def is_phase1_enabled(self) -> bool:
        """检查是否启用 Phase 1"""
        return self.phase == Phase.PHASE1

    def get_enabled_features(self) -> list[str]:
        """获取已启用的 Phase 2 功能列表"""
        if not self.is_phase2_enabled():
            return []

        features = []
        if self.topup_enforcement:
            features.append("topup_enforcement")
        if self.daily_report_required:
            features.append("daily_report_required")
        if self.negative_balance_block:
            features.append("negative_balance_block")
        if self.settlement_lock:
            features.append("settlement_lock")

        return features

    def __str__(self) -> str:
        """字符串表示"""
        features = self.get_enabled_features()
        features_str = ", ".join(features) if features else "None"
        return f"PhaseConfig(phase={self.phase.value}, features=[{features_str}])"


# ========== 全局单例 ==========

_global_config: Optional[PhaseConfig] = None


def get_phase_config() -> PhaseConfig:
    """获取全局 Phase 配置单例

    Returns:
        PhaseConfig: 全局配置实例
    """
    global _global_config
    if _global_config is None:
        _global_config = PhaseConfig.from_env()
    return _global_config


def reset_phase_config():
    """重置全局配置（用于测试）"""
    global _global_config
    _global_config = None


# ========== Phase-aware 装饰器 ==========

def phase2_only(
    feature: str,
    fallback: Optional[Callable[..., T]] = None,
    warning_message: Optional[str] = None
):
    """Phase 2 专属功能装饰器

    在 Phase 1 模式下:
    - 如果提供 fallback，调用 fallback 函数
    - 否则跳过执行并记录警告

    在 Phase 2 模式下:
    - 正常执行被装饰的函数

    Args:
        feature: 功能名称（用于日志）
        fallback: Phase 1 时的降级函数
        warning_message: Phase 1 时的警告消息

    示例:
        @phase2_only("negative_balance_block")
        def block_negative_balance(self, account_id: int):
            # 只在 Phase 2 执行
            raise BusinessError("余额不足")

        @phase2_only("daily_report_required", fallback=lambda self, user_id: None)
        def suspend_for_missing_reports(self, user_id: int):
            # Phase 1 时调用 fallback（什么都不做）
            self.suspend_user(user_id)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Optional[T]:
            config = get_phase_config()

            if config.is_phase1_enabled():
                msg = warning_message or f"Phase 2 feature '{feature}' skipped in Phase 1 mode"
                logger.info(f"[Phase1] {msg}")

                if fallback is not None:
                    return fallback(*args, **kwargs)
                return None

            # Phase 2: 正常执行
            return func(*args, **kwargs)

        return wrapper
    return decorator


def phase_aware_validation(
    phase2_validator: Callable[..., bool],
    phase1_action: str = "warn"
):
    """Phase-aware 验证装饰器

    根据当前 Phase 执行不同的验证行为:
    - Phase 1: 记录警告但不阻断
    - Phase 2: 验证失败则抛出异常

    Args:
        phase2_validator: Phase 2 验证函数，返回 True 表示验证通过
        phase1_action: Phase 1 行为，"warn" 或 "skip"

    示例:
        @phase_aware_validation(
            phase2_validator=lambda self, amount: amount > 0,
            phase1_action="warn"
        )
        def process_topup(self, amount: Decimal):
            # 处理充值
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            config = get_phase_config()

            # 执行验证
            validation_passed = phase2_validator(*args, **kwargs)

            if not validation_passed:
                if config.is_phase2_enabled():
                    # Phase 2: 验证失败，抛出异常
                    raise ValueError(f"Phase 2 validation failed for {func.__name__}")
                else:
                    # Phase 1: 记录警告
                    if phase1_action == "warn":
                        logger.warning(
                            f"[Phase1] Validation warning in {func.__name__}: "
                            f"Would fail in Phase 2"
                        )

            return func(*args, **kwargs)

        return wrapper
    return decorator


# ========== Phase-aware 辅助函数 ==========

def should_block_negative_balance() -> bool:
    """是否应该阻止负余额"""
    config = get_phase_config()
    return config.is_phase2_enabled() and config.negative_balance_block


def should_enforce_daily_report() -> bool:
    """是否应该强制日报填报"""
    config = get_phase_config()
    return config.is_phase2_enabled() and config.daily_report_required


def should_lock_settlement() -> bool:
    """是否应该锁定结算期数据"""
    config = get_phase_config()
    return config.is_phase2_enabled() and config.settlement_lock


def should_enforce_topup() -> bool:
    """是否应该强制充值校验"""
    config = get_phase_config()
    return config.is_phase2_enabled() and config.topup_enforcement


def log_phase_warning(feature: str, message: str, **context):
    """记录 Phase 1 警告日志

    在 Phase 1 模式下记录警告，Phase 2 模式下会变成阻断。

    Args:
        feature: 功能名称
        message: 警告消息
        **context: 上下文信息
    """
    config = get_phase_config()
    context_str = ", ".join(f"{k}={v}" for k, v in context.items())

    if config.is_phase1_enabled():
        logger.warning(
            f"[Phase1 Warning] {feature}: {message} | {context_str}"
        )
    else:
        logger.error(
            f"[Phase2 Violation] {feature}: {message} | {context_str}"
        )
