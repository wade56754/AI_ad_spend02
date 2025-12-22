"""
Phase Configuration System - AI 代码工厂 Phase 1/2 边界管理

基准文档: MASTER.md v4.4 §8 Phase 1/2 定义
版本: v1.0
创建日期: 2025-12-22

功能:
- 管理 Phase 1（照亮不问责）和 Phase 2（问责与约束）的配置
- 通过环境变量控制 Phase 2 功能开关
- 为代码生成器和验证器提供 Phase 边界检查
"""

from enum import Enum
from pydantic import BaseModel, Field
import os
from typing import Optional


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
        PHASE2_WEEKLY_BRIEF_REQUIRED: "true" | "false" (默认 false)
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
        description="充值强制校验：不允许负余额投放（Phase 2）"
    )

    daily_report_required: bool = Field(
        default=False,
        description="日报强制填报：超过 N 天未提交则自动暂停（Phase 2）"
    )

    weekly_brief_required: bool = Field(
        default=False,
        description="周报强制填报：主管必须每周提交（Phase 2）"
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

        示例:
            >>> os.environ["FACTORY_PHASE"] = "phase2"
            >>> os.environ["PHASE2_TOPUP_ENFORCEMENT"] = "true"
            >>> config = PhaseConfig.from_env()
            >>> config.is_phase2_enabled()
            True
            >>> config.topup_enforcement
            True
        """
        phase_str = os.getenv("FACTORY_PHASE", "phase1").lower()

        # 验证 phase 值
        if phase_str not in ["phase1", "phase2"]:
            raise ValueError(
                f"Invalid FACTORY_PHASE value: {phase_str}. "
                f"Must be 'phase1' or 'phase2'"
            )

        return cls(
            phase=Phase(phase_str),
            topup_enforcement=os.getenv("PHASE2_TOPUP_ENFORCEMENT", "false").lower() == "true",
            daily_report_required=os.getenv("PHASE2_DAILY_REPORT_REQUIRED", "false").lower() == "true",
            weekly_brief_required=os.getenv("PHASE2_WEEKLY_BRIEF_REQUIRED", "false").lower() == "true",
            settlement_lock=os.getenv("PHASE2_SETTLEMENT_LOCK", "false").lower() == "true"
        )

    def is_phase2_enabled(self) -> bool:
        """检查是否启用 Phase 2

        Returns:
            bool: True 表示当前为 Phase 2 模式
        """
        return self.phase == Phase.PHASE2

    def is_phase1_enabled(self) -> bool:
        """检查是否启用 Phase 1

        Returns:
            bool: True 表示当前为 Phase 1 模式
        """
        return self.phase == Phase.PHASE1

    def get_enabled_features(self) -> list[str]:
        """获取已启用的 Phase 2 功能列表

        Returns:
            list[str]: 启用的功能名称列表

        示例:
            >>> config = PhaseConfig(phase=Phase.PHASE2, topup_enforcement=True)
            >>> config.get_enabled_features()
            ['topup_enforcement']
        """
        if not self.is_phase2_enabled():
            return []

        features = []
        if self.topup_enforcement:
            features.append("topup_enforcement")
        if self.daily_report_required:
            features.append("daily_report_required")
        if self.weekly_brief_required:
            features.append("weekly_brief_required")
        if self.settlement_lock:
            features.append("settlement_lock")

        return features

    def validate_code_for_phase(self, code: str) -> tuple[bool, Optional[str]]:
        """验证代码是否符合当前 Phase 的约束

        Phase 1 约束:
        - 禁止自动拒绝/暂停（应使用高亮提示）
        - 禁止强制阻断业务流程

        Phase 2 约束:
        - 允许强制校验和自动拒绝

        Args:
            code: 待验证的代码字符串

        Returns:
            tuple[bool, Optional[str]]: (是否通过, 错误信息)

        示例:
            >>> config = PhaseConfig(phase=Phase.PHASE1)
            >>> code = "if balance < 0: raise BusinessError('余额不足')"
            >>> valid, msg = config.validate_code_for_phase(code)
            >>> valid
            False
            >>> "Phase 1 不允许强制阻断" in msg
            True
        """
        if self.is_phase1_enabled():
            # Phase 1 禁止模式
            if "raise" in code and "BusinessError" in code and "Phase 2" not in code:
                return False, (
                    "Phase 1 不允许强制阻断业务流程。"
                    "应使用高亮/提示而非异常。"
                    "如需强制验证，请标注 '# Phase 2 only' 注释。"
                )

            if ".status = 'rejected'" in code or '.status = "rejected"' in code:
                return False, (
                    "Phase 1 不允许自动拒绝。"
                    "应记录异常并通知人工处理。"
                )

            if ".status = 'suspended'" in code or '.status = "suspended"' in code:
                return False, (
                    "Phase 1 不允许自动暂停账户。"
                    "应高亮显示并通知管理员。"
                )

        return True, None

    def __str__(self) -> str:
        """字符串表示"""
        features = self.get_enabled_features()
        features_str = ", ".join(features) if features else "None"
        return f"PhaseConfig(phase={self.phase.value}, features=[{features_str}])"


# 全局单例（可选）
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
