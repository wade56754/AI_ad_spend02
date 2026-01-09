"""
依赖注入模块

PRD v2.2 变更:
- 移除 require_data_operator (使用 require_finance 或 require_project_owner)
- 移除 require_media_buyer (使用 require_role(["pitcher"]))
"""
from .auth import (
    get_current_user_optional,
    get_current_active_user,
    require_role,
    require_admin,
    require_finance,
    require_account_manager,
    require_permission,
    require_project_access,
    require_account_access,
    require_finance_access,
    require_report_access,
    has_permission,
    ROLE_PERMISSIONS,
)

__all__ = [
    "get_current_user_optional",
    "get_current_active_user",
    "require_role",
    "require_admin",
    "require_finance",
    "require_account_manager",
    "require_permission",
    "require_project_access",
    "require_account_access",
    "require_finance_access",
    "require_report_access",
    "has_permission",
    "ROLE_PERMISSIONS",
]
