"""
agent_platform.config - 配置层

Phase 1 迁移：从 agents/agents_config.py 拆分出配置。

提供：
- paths: BASE_PATH, BACKEND_DIR, FRONTEND_DIR 等路径常量
- sot_files: SOT_FILES 映射
- constants: is_legacy_mode(), is_mcp_mode() 等

迁移文档：docs/dev/AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md
"""

from .paths import BASE_PATH, PROJECT_ROOT, BACKEND_DIR, FRONTEND_DIR, DOCS_DIR
from .sot_files import SOT_FILES, CRITICAL_SOT_FILES
from .constants import is_legacy_mode, is_mcp_mode

__all__ = [
    # 路径常量
    "BASE_PATH",
    "PROJECT_ROOT",
    "BACKEND_DIR",
    "FRONTEND_DIR",
    "DOCS_DIR",
    # SoT 配置
    "SOT_FILES",
    "CRITICAL_SOT_FILES",
    # 模式检查
    "is_legacy_mode",
    "is_mcp_mode",
]
