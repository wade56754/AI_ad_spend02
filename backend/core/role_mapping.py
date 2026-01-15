"""
角色映射模块

MASTER.md v4.8 定义的 6 个业务角色 与 代码技术角色 的双向映射。
策略：兼容映射 + 废弃角色自动迁移。

业务角色（MASTER.md v4.8）  技术角色（UserRole 枚举）
────────────────────────────────────────────────
ceo                  →  admin (复用，ceo 是业务概念)
project_owner        →  project_owner
finance              →  finance
pitcher              →  pitcher (v5.0: 废弃 media_buyer)
account_manager      →  account_manager
admin                →  admin

废弃角色（PRD v5.1）：
- supervisor → 自动迁移到 project_owner
- data_operator → 自动迁移到 finance
- media_buyer → 使用 pitcher

SoT Reference: MASTER.md v4.8 §2.4
更新日期: 2026-01-01
"""

from typing import Optional, List, Set


# ============================================================================
# 映射表 (v5.0 更新)
# ============================================================================

# MASTER.md 业务角色 → 代码技术角色
# v5.0: pitcher 直接使用，废弃 media_buyer
MASTER_TO_CODE: dict[str, str] = {
    "ceo": "admin",  # ceo 映射到 admin（同权限）
    "pitcher": "pitcher",  # v5.0: 直接使用 pitcher
    # 以下角色名称一致
    "project_owner": "project_owner",
    "finance": "finance",
    "account_manager": "account_manager",
    "admin": "admin",
    # 废弃角色自动迁移（向后兼容）
    "supervisor": "project_owner",  # PRD v5.1: 合并到 project_owner
}

# 代码技术角色 → MASTER.md 业务角色（用于前端展示）
# v5.0: 废弃角色迁移到新角色
CODE_TO_MASTER: dict[str, str] = {
    "data_operator": "project_owner",  # v5.0: 迁移到 project_owner
    "media_buyer": "pitcher",  # 向后兼容
    "pitcher": "pitcher",
    "admin": "admin",
    "project_owner": "project_owner",
    "finance": "finance",
    "account_manager": "account_manager",
}

# 业务角色中文显示名
ROLE_DISPLAY_NAMES: dict[str, str] = {
    "ceo": "老板",
    "project_owner": "项目负责人",
    "finance": "财务",
    "pitcher": "投手",
    "account_manager": "户管",
    "admin": "管理员",
    # 废弃角色显示名（向后兼容）
    "supervisor": "项目负责人",  # v5.0: 显示为迁移后的角色
    "data_operator": "项目负责人",
    "media_buyer": "投手",
}

# 合法的业务角色集合（MASTER.md v4.8 §2.4）
# v5.0: 6 个角色，移除 supervisor
VALID_MASTER_ROLES: Set[str] = {
    "ceo",
    "project_owner",
    "finance",
    "pitcher",
    "account_manager",
    "admin",
}

# 合法的技术角色集合（UserRole 枚举）
# v5.0: 使用 pitcher，保留废弃角色向后兼容
VALID_CODE_ROLES: Set[str] = {
    "admin",
    "project_owner",
    "finance",
    "pitcher",
    "account_manager",
    # 废弃但保留兼容
    "data_operator",
    "media_buyer",
}

# 等价角色组（用于状态机权限检查）
# v5.0: 更新等价映射
EQUIVALENT_ROLE_GROUPS: List[Set[str]] = [
    {"supervisor", "project_owner", "data_operator"},  # 废弃角色映射到 project_owner
    {"pitcher", "media_buyer"},  # pitcher 等价
    {"ceo", "admin"},
]


# ============================================================================
# 核心函数
# ============================================================================


def normalize_role(role: Optional[str]) -> Optional[str]:
    """
    统一转为代码技术角色

    用于：API 输入、状态机权限检查

    Args:
        role: 业务角色或技术角色名

    Returns:
        技术角色名，或 None（如果输入为 None）

    Examples:
        >>> normalize_role("supervisor")
        "data_operator"
        >>> normalize_role("data_operator")
        "data_operator"
        >>> normalize_role("pitcher")
        "media_buyer"
    """
    if role is None:
        return None

    role_lower = role.lower().strip()

    # 如果是业务角色，转为技术角色
    if role_lower in MASTER_TO_CODE:
        return MASTER_TO_CODE[role_lower]

    # 如果已经是技术角色，直接返回
    if role_lower in VALID_CODE_ROLES:
        return role_lower

    # 未知角色，原样返回（让后续校验处理）
    return role_lower


def to_display_role(role: Optional[str]) -> Optional[str]:
    """
    转为业务角色（用于前端展示）

    用于：API 响应、日志、审计记录

    Args:
        role: 技术角色或业务角色名

    Returns:
        业务角色名

    Examples:
        >>> to_display_role("data_operator")
        "supervisor"
        >>> to_display_role("media_buyer")
        "pitcher"
    """
    if role is None:
        return None

    role_lower = role.lower().strip()

    # 如果是技术角色，转为业务角色
    if role_lower in CODE_TO_MASTER:
        return CODE_TO_MASTER[role_lower]

    # 如果已经是业务角色，直接返回
    if role_lower in VALID_MASTER_ROLES:
        return role_lower

    # 未知角色，原样返回
    return role_lower


def get_display_name(role: Optional[str]) -> str:
    """
    获取角色中文显示名

    Args:
        role: 任意角色名

    Returns:
        中文名，未知角色返回原值
    """
    if role is None:
        return "未知"

    role_lower = role.lower().strip()
    return ROLE_DISPLAY_NAMES.get(role_lower, role)


def is_role_equivalent(role1: Optional[str], role2: Optional[str]) -> bool:
    """
    检查两个角色是否等价

    用于：状态机权限检查时，supervisor 和 data_operator 应视为等价

    Args:
        role1: 第一个角色
        role2: 第二个角色

    Returns:
        是否等价

    Examples:
        >>> is_role_equivalent("supervisor", "data_operator")
        True
        >>> is_role_equivalent("pitcher", "media_buyer")
        True
        >>> is_role_equivalent("admin", "finance")
        False
    """
    if role1 is None or role2 is None:
        return False

    r1 = role1.lower().strip()
    r2 = role2.lower().strip()

    # 完全相同
    if r1 == r2:
        return True

    # 检查等价组
    for group in EQUIVALENT_ROLE_GROUPS:
        if r1 in group and r2 in group:
            return True

    return False


def role_in_list(user_role: Optional[str], allowed_roles: List[str]) -> bool:
    """
    检查用户角色是否在允许列表中（支持等价角色）

    用于：状态机权限检查，替代简单的 `user_role in allowed_roles`

    Args:
        user_role: 用户当前角色
        allowed_roles: 允许的角色列表

    Returns:
        是否允许

    Examples:
        >>> role_in_list("supervisor", ["data_operator", "admin"])
        True
        >>> role_in_list("pitcher", ["media_buyer"])
        True
    """
    if user_role is None:
        return False

    for allowed in allowed_roles:
        if is_role_equivalent(user_role, allowed):
            return True

    return False


def normalize_role_list(roles: List[str]) -> List[str]:
    """
    将角色列表中的业务角色统一转为技术角色

    用于：状态机定义时，保持技术角色名
    """
    return [normalize_role(r) for r in roles if r]


def expand_role_list(roles: List[str]) -> List[str]:
    """
    扩展角色列表，包含等价角色

    用于：状态机初始化，确保 supervisor 和 data_operator 都被接受

    Examples:
        >>> expand_role_list(["data_operator", "admin"])
        ["data_operator", "supervisor", "admin", "ceo"]
    """
    expanded = set()

    for role in roles:
        expanded.add(role)
        # 添加等价角色
        for group in EQUIVALENT_ROLE_GROUPS:
            if role in group:
                expanded.update(group)

    return list(expanded)


# ============================================================================
# 校验函数
# ============================================================================


def is_valid_master_role(role: str) -> bool:
    """检查是否是合法的业务角色（MASTER.md 定义）"""
    return role.lower().strip() in VALID_MASTER_ROLES


def is_valid_code_role(role: str) -> bool:
    """检查是否是合法的技术角色（UserRole 枚举）"""
    return role.lower().strip() in VALID_CODE_ROLES


def is_valid_role(role: str) -> bool:
    """检查是否是任意合法角色（业务或技术）"""
    role_lower = role.lower().strip()
    return role_lower in VALID_MASTER_ROLES or role_lower in VALID_CODE_ROLES
