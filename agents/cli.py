"""
[DEPRECATED] agents CLI - 影子模式兼容壳

此模块已迁移至 agent_platform/__main__.py。
当前文件仅作为兼容层，根据 AGENT_PLATFORM_LEGACY 环境变量决定行为。

迁移状态: 观察期
迁移文档: docs/dev/AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md

紧急回退:
    设置 AGENT_PLATFORM_LEGACY=1 可临时回退旧逻辑。

推荐使用:
    python -m agent_platform
"""

import os
import sys
import warnings

# 关键：使用纯 os.environ 检查，不导入 agent_platform
# 这避免了循环依赖问题
_LEGACY_MODE = os.environ.get("AGENT_PLATFORM_LEGACY", "0") == "1"


def main() -> int:
    """CLI 入口点"""
    if _LEGACY_MODE:
        # Legacy 模式：使用原有 CLI 逻辑
        from .cli_legacy import main as legacy_main
        return legacy_main()
    else:
        # 新模式：显示废弃警告，然后转发到新 CLI
        warnings.warn(
            "agents.cli 已废弃，请改用 python -m agent_platform。"
            "设置 AGENT_PLATFORM_LEGACY=1 可临时回退。",
            DeprecationWarning,
            stacklevel=2,
        )

        # 暂时仍使用 legacy 实现，因为 agent_platform.__main__ 可能还未完全就绪
        # Phase 2 会完成完整的 CLI 迁移
        from .cli_legacy import main as legacy_main
        return legacy_main()


if __name__ == "__main__":
    sys.exit(main())
