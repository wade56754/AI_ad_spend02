"""
功能开关 - 支持灰度和回滚

基准文档: MASTER.md v4.6
版本: v4.4

设计理念:
- 所有新功能默认通过开关控制
- 支持环境变量覆盖
- 支持快速回滚到旧版本
"""

from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class FeatureFlags:
    """功能开关配置"""

    # ========== 回滚开关 ==========
    use_legacy_pipeline: bool = False  # 使用 v4.0 兼容模式

    # ========== v4.1 功能 ==========
    enable_sot_dynamic_load: bool = True   # SoT 动态加载
    enable_risk_phase: bool = True          # 风险评估阶段
    enable_trace_phase: bool = True         # 来源追溯阶段

    # ========== v4.2 功能 ==========
    enable_sop_system: bool = True          # SOP 模板系统
    enable_repo_map: bool = True            # 代码地图生成
    enable_guardrails: bool = True          # 编辑防护
    enable_task_persistence: bool = True    # 任务持久化
    enable_event_stream: bool = True        # 事件流记录

    # ========== v4.3 功能 ==========
    enable_task_cards: bool = True          # 任务卡匹配

    # ========== v4.4 提示词系统 ==========
    enable_prompt_system: bool = True       # 提示词系统总开关
    enable_prompt_injection: bool = True    # 提示词注入
    enable_system_constraints: bool = True  # 系统约束提示词 (SoT, Phase1, etc)
    prompt_max_supporting: int = 3          # 最多辅助提示词数量
    enable_phase1_soft_mode: bool = True    # Phase 1 软性模式 (状态问题仅警告)

    # ========== 阈值配置 ==========
    strict_trace_rate: float = 1.0          # 追溯率阈值 (100%)
    guardrails_max_retries: int = 3         # Guardrails 最大重试次数
    search_max_candidates: int = 10         # 搜索最大候选数

    # ========== 调试选项 ==========
    verbose: bool = False                   # 详细输出
    dry_run: bool = False                   # 干运行模式 (不实际写文件)

    @classmethod
    def from_env(cls) -> "FeatureFlags":
        """从环境变量加载配置"""
        return cls(
            # 回滚开关
            use_legacy_pipeline=os.getenv("CF_LEGACY", "0") == "1",

            # v4.1 功能
            enable_sot_dynamic_load=os.getenv("CF_SOT_LOAD", "1") == "1",
            enable_risk_phase=os.getenv("CF_RISK", "1") == "1",
            enable_trace_phase=os.getenv("CF_TRACE", "1") == "1",

            # v4.2 功能
            enable_sop_system=os.getenv("CF_SOP", "1") == "1",
            enable_repo_map=os.getenv("CF_REPOMAP", "1") == "1",
            enable_guardrails=os.getenv("CF_GUARDRAILS", "1") == "1",
            enable_task_persistence=os.getenv("CF_TASKS", "1") == "1",
            enable_event_stream=os.getenv("CF_EVENTS", "1") == "1",

            # v4.3 功能
            enable_task_cards=os.getenv("CF_TASK_CARDS", "1") == "1",

            # v4.4 提示词系统
            enable_prompt_system=os.getenv("CF_PROMPT_SYSTEM", "1") == "1",
            enable_prompt_injection=os.getenv("CF_PROMPT_INJECT", "1") == "1",
            enable_system_constraints=os.getenv("CF_SYSTEM_CONSTRAINTS", "1") == "1",
            prompt_max_supporting=int(os.getenv("CF_PROMPT_MAX_SUPPORTING", "3")),
            enable_phase1_soft_mode=os.getenv("CF_PHASE1_SOFT", "1") == "1",

            # 阈值
            strict_trace_rate=float(os.getenv("CF_TRACE_RATE", "1.0")),
            guardrails_max_retries=int(os.getenv("CF_GUARDRAILS_RETRIES", "3")),

            # 调试
            verbose=os.getenv("CF_VERBOSE", "0") == "1",
            dry_run=os.getenv("CF_DRY_RUN", "0") == "1",
        )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "use_legacy_pipeline": self.use_legacy_pipeline,
            "enable_sot_dynamic_load": self.enable_sot_dynamic_load,
            "enable_risk_phase": self.enable_risk_phase,
            "enable_trace_phase": self.enable_trace_phase,
            "enable_sop_system": self.enable_sop_system,
            "enable_repo_map": self.enable_repo_map,
            "enable_guardrails": self.enable_guardrails,
            "enable_task_persistence": self.enable_task_persistence,
            "enable_event_stream": self.enable_event_stream,
            "enable_task_cards": self.enable_task_cards,
            "enable_prompt_system": self.enable_prompt_system,
            "enable_prompt_injection": self.enable_prompt_injection,
            "enable_system_constraints": self.enable_system_constraints,
            "prompt_max_supporting": self.prompt_max_supporting,
            "enable_phase1_soft_mode": self.enable_phase1_soft_mode,
            "strict_trace_rate": self.strict_trace_rate,
            "guardrails_max_retries": self.guardrails_max_retries,
        }


# 全局单例
_flags: Optional[FeatureFlags] = None


def get_flags() -> FeatureFlags:
    """获取全局功能开关实例"""
    global _flags
    if _flags is None:
        _flags = FeatureFlags.from_env()
    return _flags


def reset_flags():
    """重置全局功能开关 (用于测试)"""
    global _flags
    _flags = None


def set_flags(flags: FeatureFlags):
    """设置全局功能开关 (用于测试)"""
    global _flags
    _flags = flags
