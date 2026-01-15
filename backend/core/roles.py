"""
角色定义集中管理 (MASTER.md v4.8 §2.4)

版本: v2.0
创建日期: 2025-12-27
更新日期: 2026-01-01
基准文档: MASTER.md v4.8 §2.4

功能:
- 6 角色白名单定义
- 禁止使用的旧角色检查
- 技术角色映射
- project_owner 身份验证

注意:
- 本模块是角色定义的唯一权威来源
- role_mapping.py 已对齐到 v5.0

变更记录:
- v2.0 (2026-01-01): 对齐 MASTER.md v4.8，更新技术角色映射
- v1.0 (2025-12-27): 初始版本
"""

from typing import FrozenSet, Dict, Optional, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ============================================================================
# 6 角色白名单 (MASTER.md v4.8 §2.4)
# ============================================================================

BUSINESS_ROLES: FrozenSet[str] = frozenset(
    [
        "ceo",  # 老板：资金安全、公司盈亏、最终决策
        "project_owner",  # 项目负责人：项目盈亏、日报审核、确认有效粉
        "finance",  # 财务：资金出入准确、数据真实、对账
        "pitcher",  # 投手：CPL 达标、日报准确、执行投放
        "account_manager",  # 户管：账户分配、账户状态监控
        "admin",  # 管理员：系统配置（不参与业务）
    ]
)

# 角色中文名映射 (v4.8)
ROLE_DISPLAY_NAMES: Dict[str, str] = {
    "ceo": "老板",
    "project_owner": "项目负责人",
    "finance": "财务",
    "pitcher": "投手",
    "account_manager": "户管",
    "admin": "管理员",
}

# 兼容别名
ROLE_DISPLAY_NAMES_V46 = ROLE_DISPLAY_NAMES


# ============================================================================
# 禁止使用的旧角色 (PRD v5.1)
# ============================================================================

FORBIDDEN_ROLES: FrozenSet[str] = frozenset(
    [
        "supervisor",  # 已合并到 project_owner (MASTER.md v4.8)
        "data_operator",  # 已移除
        "media_buyer",  # 技术层角色，业务层用 pitcher
    ]
)


# ============================================================================
# 技术层角色映射 (v5.0: pitcher 直接使用)
# ============================================================================

TECH_ROLE_MAPPING: Dict[str, Optional[str]] = {
    "ceo": "admin",  # ceo 复用 admin 技术角色
    "project_owner": None,  # 通过 is_project_owner() 判断
    "finance": "finance",
    "pitcher": "pitcher",  # v5.0: 直接使用 pitcher
    "account_manager": "account_manager",
    "admin": "admin",
}

# 技术角色 -> 业务角色 (用于 API 响应)
CODE_TO_BUSINESS: Dict[str, str] = {
    "admin": "admin",
    "finance": "finance",
    "pitcher": "pitcher",
    "media_buyer": "pitcher",  # 向后兼容
    "account_manager": "account_manager",
}


# ============================================================================
# 核心校验函数
# ============================================================================


def is_valid_role(role: str) -> bool:
    """
    检查角色是否在 6 角色白名单中

    Args:
        role: 角色名

    Returns:
        bool: 是否合法

    Examples:
        >>> is_valid_role('pitcher')
        True
        >>> is_valid_role('supervisor')
        False
    """
    return role.lower().strip() in BUSINESS_ROLES


def is_forbidden_role(role: str) -> bool:
    """
    检查是否为禁止使用的角色

    Args:
        role: 角色名

    Returns:
        bool: 是否禁止使用

    Examples:
        >>> is_forbidden_role('supervisor')
        True
        >>> is_forbidden_role('pitcher')
        False
    """
    return role.lower().strip() in FORBIDDEN_ROLES


def get_tech_role(business_role: str) -> Optional[str]:
    """
    获取业务角色对应的技术层角色

    Args:
        business_role: 业务角色名

    Returns:
        技术角色名，project_owner 返回 None（需特殊处理）

    Examples:
        >>> get_tech_role('pitcher')
        'media_buyer'
        >>> get_tech_role('project_owner')
        None
    """
    return TECH_ROLE_MAPPING.get(business_role.lower().strip())


def get_business_role(tech_role: str) -> str:
    """
    获取技术角色对应的业务角色

    Args:
        tech_role: 技术角色名

    Returns:
        业务角色名

    Examples:
        >>> get_business_role('media_buyer')
        'pitcher'
    """
    return CODE_TO_BUSINESS.get(tech_role.lower().strip(), tech_role)


def get_display_name_v46(role: str) -> str:
    """
    获取角色中文显示名 (v4.6)

    Args:
        role: 角色名

    Returns:
        中文名，未知角色返回原值
    """
    role_lower = role.lower().strip()
    return ROLE_DISPLAY_NAMES_V46.get(role_lower, role)


def validate_role(role: str) -> None:
    """
    验证角色是否合法，不合法则抛出异常

    Args:
        role: 角色名

    Raises:
        ValueError: 角色不在白名单中或在禁止列表中
    """
    role_lower = role.lower().strip()

    if role_lower in FORBIDDEN_ROLES:
        raise ValueError(
            f"角色 '{role}' 已废弃 (MASTER.md v4.6)。"
            f"如需使用原 supervisor 功能，请使用 project_owner。"
        )

    if role_lower not in BUSINESS_ROLES:
        valid_roles = ", ".join(sorted(BUSINESS_ROLES))
        raise ValueError(f"角色 '{role}' 不在白名单中。" f"合法角色: {valid_roles}")


# ============================================================================
# project_owner 身份验证 (MASTER.md v4.6 §2.4)
# ============================================================================


def is_project_owner(user_id: int, db: "Session") -> bool:
    """
    检查用户是否为项目负责人

    判断依据 (MASTER.md v4.6 §2.4):
    1. users.is_project_owner = true
    2. 或者在 project_members 表中 role = 'owner'

    Args:
        user_id: 用户 ID
        db: 数据库会话

    Returns:
        bool: 是否为项目负责人
    """
    # 延迟导入避免循环依赖
    from backend.models.user import User
    from backend.models.project import ProjectMember

    # 方式 1: 检查 users.is_project_owner 字段
    user = db.query(User).filter(User.id == user_id).first()
    if user and getattr(user, "is_project_owner", False):
        return True

    # 方式 2: 检查 project_members 表
    member = (
        db.query(ProjectMember)
        .filter(ProjectMember.user_id == user_id, ProjectMember.role == "owner")
        .first()
    )

    return member is not None


def is_project_owner_of(user_id: int, project_id: int, db: "Session") -> bool:
    """
    检查用户是否为指定项目的负责人

    Args:
        user_id: 用户 ID
        project_id: 项目 ID
        db: 数据库会话

    Returns:
        bool: 是否为该项目负责人
    """
    # 延迟导入避免循环依赖
    from backend.models.project import Project, ProjectMember

    # 检查 projects.owner_id
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_id == user_id)
        .first()
    )
    if project:
        return True

    # 检查 project_members
    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.role == "owner",
        )
        .first()
    )

    return member is not None


# ============================================================================
# 权限检查辅助函数
# ============================================================================


def can_approve_topup(role: str) -> bool:
    """
    检查角色是否可以审批充值

    审批角色 (MASTER.md v4.6 §4.5.11):
    - account_manager: 户管收集
    - finance: 财务审批

    注意: CEO 不参与日常审批 (INV-006 F-009)

    Args:
        role: 角色名

    Returns:
        bool: 是否可以审批
    """
    return role.lower().strip() in {"account_manager", "finance"}


def can_review_daily_report(role: str) -> bool:
    """
    检查角色是否可以审核日报

    审核角色 (MASTER.md v4.6 §4.5):
    - project_owner: 项目负责人
    - admin: 管理员

    Args:
        role: 角色名

    Returns:
        bool: 是否可以审核
    """
    return role.lower().strip() in {"project_owner", "admin"}


def can_view_profit(role: str) -> bool:
    """
    检查角色是否可以查看利润

    查看角色 (MASTER.md v4.6 §4.6):
    - ceo: 老板
    - finance: 财务
    - admin: 管理员

    Args:
        role: 角色名

    Returns:
        bool: 是否可以查看
    """
    return role.lower().strip() in {"ceo", "finance", "admin"}


# ============================================================================
# 迁移辅助函数
# ============================================================================


def migrate_role(old_role: str) -> str:
    """
    将旧角色迁移到新角色

    迁移规则 (MASTER.md v4.6):
    - supervisor -> project_owner
    - data_operator -> 根据功能分配

    Args:
        old_role: 旧角色名

    Returns:
        新角色名

    Examples:
        >>> migrate_role('supervisor')
        'project_owner'
        >>> migrate_role('pitcher')
        'pitcher'
    """
    old_role_lower = old_role.lower().strip()

    migration_map = {
        "supervisor": "project_owner",
        "data_operator": "finance",  # 默认迁移到 finance，需业务确认
    }

    if old_role_lower in migration_map:
        new_role = migration_map[old_role_lower]
        logger.warning(f"角色迁移: {old_role} -> {new_role} (MASTER.md v4.6)")
        return new_role

    return old_role
