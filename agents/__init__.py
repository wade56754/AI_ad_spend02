"""
[DEPRECATED] agents 模块 - 影子模式兼容壳

此模块已迁移至 agent_platform/。
当前文件仅作为兼容层，所有调用转发至新模块。

迁移状态: 观察期
迁移文档: docs/dev/AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md

紧急回退:
    设置 AGENT_PLATFORM_LEGACY=1 可临时回退旧逻辑。

观察期结束条件:
    1. 连续 7 天无 AGENT_PLATFORM_LEGACY 回退
    2. 所有 .claude/commands 已更新
    3. CI/CD 全部通过

删除前检查清单:
    - [ ] grep -r "from agents" --include="*.py" 无结果
    - [ ] grep -r "import agents" --include="*.py" 无结果
    - [ ] .claude/commands 中无 agents.cli 引用
"""

import os
import warnings

__version__ = "1.0.0"

# 关键：使用纯 os.environ 检查，不导入 agent_platform
# 这避免了循环依赖问题
_LEGACY_MODE = os.environ.get("AGENT_PLATFORM_LEGACY", "0") == "1"

if _LEGACY_MODE:
    # =========================================================================
    # Legacy 模式：使用原有逻辑
    # =========================================================================
    from .agents_config import (
        create_agent,
        list_agents,
        check_llm_available,
        AgentInfo,
        SOT_FILES,
        BASE_PATH,
        BACKEND_DIR,
        FRONTEND_DIR,
        PROJECT_ROOT,
    )

    from .agent_core import (
        FEAgent,
        BEAgent,
        TestAgent,
        DocAgent,
        CodeReviewAgent,
        OrchestratorAgent,
    )

    from .tools.types import (
        AgentResponse,
        SkillResult,
    )

    __all__ = [
        # Factory functions
        "create_agent",
        "list_agents",
        "check_llm_available",
        "AgentInfo",
        # Config
        "SOT_FILES",
        "BASE_PATH",
        "BACKEND_DIR",
        "FRONTEND_DIR",
        "PROJECT_ROOT",
        # Agent classes
        "FEAgent",
        "BEAgent",
        "TestAgent",
        "DocAgent",
        "CodeReviewAgent",
        "OrchestratorAgent",
        # Types
        "AgentResponse",
        "SkillResult",
    ]

else:
    # =========================================================================
    # 新模式：转发到 agent_platform（使用延迟导入避免启动时依赖）
    # =========================================================================
    warnings.warn(
        "agents 模块已废弃，请改用 agent_platform。"
        "设置 AGENT_PLATFORM_LEGACY=1 可临时回退。",
        DeprecationWarning,
        stacklevel=2,
    )

    # 延迟导入映射，仅在实际使用时触发
    _LAZY_IMPORTS = {
        # 从 agent_platform.config 导入
        "SOT_FILES": ("agent_platform.config.sot_files", "SOT_FILES"),
        "BASE_PATH": ("agent_platform.config.paths", "BASE_PATH"),
        "BACKEND_DIR": ("agent_platform.config.paths", "BACKEND_DIR"),
        "FRONTEND_DIR": ("agent_platform.config.paths", "FRONTEND_DIR"),
        "PROJECT_ROOT": ("agent_platform.config.paths", "PROJECT_ROOT"),
        # 从 agents.agents_config 导入（暂时保留，Phase 2 会迁移）
        "create_agent": ("agents.agents_config", "create_agent"),
        "list_agents": ("agents.agents_config", "list_agents"),
        "check_llm_available": ("agents.agents_config", "check_llm_available"),
        "AgentInfo": ("agents.agents_config", "AgentInfo"),
        # Agent 类（暂时保留，Phase 2 会迁移）
        "FEAgent": ("agents.agent_core", "FEAgent"),
        "BEAgent": ("agents.agent_core", "BEAgent"),
        "TestAgent": ("agents.agent_core", "TestAgent"),
        "DocAgent": ("agents.agent_core", "DocAgent"),
        "CodeReviewAgent": ("agents.agent_core", "CodeReviewAgent"),
        "OrchestratorAgent": ("agents.agent_core", "OrchestratorAgent"),
        # Types
        "AgentResponse": ("agents.tools.types", "AgentResponse"),
        "SkillResult": ("agents.tools.types", "SkillResult"),
    }

    def __getattr__(name: str):
        """延迟导入：仅在实际访问属性时触发导入"""
        if name in _LAZY_IMPORTS:
            module_path, attr_name = _LAZY_IMPORTS[name]
            import importlib
            module = importlib.import_module(module_path)
            return getattr(module, attr_name)
        raise AttributeError(f"module 'agents' has no attribute '{name}'")

    __all__ = list(_LAZY_IMPORTS.keys())
