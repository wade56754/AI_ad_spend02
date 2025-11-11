"""
依赖注入模块
"""
from .auth import (
    get_current_user_optional,
    get_current_active_user,
    require_role,
    require_admin,
    require_finance,
    require_data_operator,
    require_account_manager,
    require_media_buyer,
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
    "require_data_operator",
    "require_account_manager",
    "require_media_buyer",
    "require_permission",
    "require_project_access",
    "require_account_access",
    "require_finance_access",
    "require_report_access",
    "has_permission",
    "ROLE_PERMISSIONS",
]