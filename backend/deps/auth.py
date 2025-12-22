"""
认证和权限控制依赖模块
提供JWT认证和基于角色的权限控制

NOTE: 此模块已重构为直接使用 backend.core.dependencies
保留以兼容旧导入
"""

# 从 core.dependencies 重新导出所有认证依赖 (使用 Supabase auth)
from backend.core.dependencies import (
    get_current_user,
    get_current_user_optional,
    get_current_active_user,
    require_role,
    require_permission,
    has_permission,
    ROLE_PERMISSIONS,
    require_admin,
    require_finance,
    require_data_operator,
    require_account_manager,
    require_media_buyer,
    require_project_access,
    require_account_access,
    require_finance_access,
    require_report_access,
    check_user_role,
)

# 保持向后兼容的导入
from backend.models import User

__all__ = [
    "get_current_user",
    "get_current_user_optional",
    "get_current_active_user",
    "require_role",
    "require_permission",
    "has_permission",
    "ROLE_PERMISSIONS",
    "require_admin",
    "require_finance",
    "require_data_operator",
    "require_account_manager",
    "require_media_buyer",
    "require_project_access",
    "require_account_access",
    "require_finance_access",
    "require_report_access",
    "check_user_role",
    "User",
]
