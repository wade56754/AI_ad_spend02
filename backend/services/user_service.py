"""
用户管理服务层 (重构版)

SoT References:
- API_SOT.md v9.3 §5 Users API
- DATA_SCHEMA.md v5.3 §3.1.1 users 表
- MASTER.md v4.4 §2.4 (7角色模型)
- BUSINESS_RULES.md BR-USER-001 (用户名唯一), BR-USER-002 (邮箱唯一)
- ERROR_CODES_SOT.md v2.1: PERM-001, VAL-001, RES-001, BIZ-002

依赖代码块:
- pagination: 分页查询
- permission-filter: 权限过滤

权限矩阵 (MASTER.md v4.4 §2.4):
- admin: 用户 CRUD
- ceo, finance, supervisor: 查看用户列表和统计
- 其他角色: 仅查看自己

Version: 2.0
Author: Claude Code
"""
from typing import List, Optional, Tuple
from uuid import UUID
import math

from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from backend.models import User
from backend.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    VALID_ROLES
)
from backend.utils import hash_password
from backend.exceptions.custom_exceptions import (
    ResourceNotFoundError,
    PermissionDeniedError,
    ValidationError,
    ResourceConflictError
)


class UserService:
    """
    用户管理服务

    职责:
    - 用户 CRUD 操作
    - 权限验证
    - 业务规则执行 (BR-USER-001, BR-USER-002)
    """

    def __init__(self, db: Session):
        self.db = db

    def get_users(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> Tuple[List[User], int, dict]:
        """
        获取用户列表

        权限: 仅 admin

        Args:
            current_user: 当前用户
            page: 页码
            page_size: 每页数量
            role: 角色过滤
            is_active: 状态过滤
            search: 搜索关键词

        Returns:
            Tuple[用户列表, 总数, 分页元数据]

        Raises:
            PermissionDeniedError: 非 admin 角色访问 (AUTH_500)
            ValidationError: role 参数无效 (VALIDATION_002)
        """
        # 权限检查 - 仅 admin 可查看用户列表
        if current_user.role != "admin":
            raise PermissionDeniedError(
                message="权限不足：仅管理员可查看用户列表",
                code="AUTH_500"
            )

        # 验证 role 参数
        if role is not None and role not in VALID_ROLES:
            raise ValidationError(
                message=f"无效的角色参数: {role}，合法角色: {VALID_ROLES}",
                code="VALIDATION_002"
            )

        # 构建查询
        query = self.db.query(User)

        # 应用过滤条件
        if role is not None:
            query = query.filter(User.role == role)

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern)
                )
            )

        # 获取总数
        total = query.count()

        # 计算分页
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        offset = (page - 1) * page_size

        # 获取分页数据
        users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()

        # 构建分页元数据
        pagination_meta = {
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }

        return users, total, pagination_meta

    def get_user_by_id(
        self,
        user_id: UUID,
        current_user: User
    ) -> User:
        """
        根据 ID 获取用户详情

        权限: admin 可查看任意用户，其他用户只能查看自己

        Args:
            user_id: 用户 ID
            current_user: 当前用户

        Returns:
            用户对象

        Raises:
            PermissionDeniedError: 无权限访问 (AUTH_500)
            ResourceNotFoundError: 用户不存在 (BIZ_002)
        """
        # 查询用户
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            raise ResourceNotFoundError(
                message=f"用户不存在: {user_id}",
                code="BIZ_002"
            )

        # 权限检查：admin 可查看任意用户，其他用户只能查看自己
        if current_user.role != "admin" and current_user.id != user_id:
            raise PermissionDeniedError(
                message="权限不足：无法查看其他用户信息",
                code="AUTH_500"
            )

        return user

    def create_user(
        self,
        user_data: UserCreate,
        current_user: User
    ) -> User:
        """
        创建用户

        权限: 仅 admin
        业务规则:
        - BR-USER-001: 用户名必须唯一
        - BR-USER-002: 邮箱必须唯一

        Args:
            user_data: 用户创建数据
            current_user: 当前用户

        Returns:
            创建的用户对象

        Raises:
            PermissionDeniedError: 非 admin 角色 (AUTH_500)
            ResourceConflictError: 用户名或邮箱已存在 (DB_004)
        """
        # 权限检查
        if current_user.role != "admin":
            raise PermissionDeniedError(
                message="权限不足：仅管理员可创建用户",
                code="AUTH_500"
            )

        # BR-USER-001: 检查用户名唯一性
        existing_username = self.db.query(User).filter(
            User.username == user_data.username
        ).first()
        if existing_username:
            raise ResourceConflictError(
                message=f"用户名已存在: {user_data.username}",
                code="DB_004"
            )

        # BR-USER-002: 检查邮箱唯一性
        existing_email = self.db.query(User).filter(
            User.email == user_data.email
        ).first()
        if existing_email:
            raise ResourceConflictError(
                message=f"邮箱已存在: {user_data.email}",
                code="DB_004"
            )

        # 创建用户
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            role=user_data.role,
            is_active=user_data.is_active
        )

        # 可选字段
        if user_data.full_name:
            # User 模型可能没有 full_name 字段，需要检查
            if hasattr(new_user, 'full_name'):
                new_user.full_name = user_data.full_name

        if user_data.department:
            if hasattr(new_user, 'department'):
                new_user.department = user_data.department

        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)

        return new_user

    def update_user(
        self,
        user_id: UUID,
        user_data: UserUpdate,
        current_user: User
    ) -> User:
        """
        更新用户信息

        权限: 仅 admin
        业务规则:
        - BR-USER-001: 用户名必须唯一
        - BR-USER-002: 邮箱必须唯一
        - BR-AUTH-001: 角色变更仅 admin 可操作 (DEV-004)

        Args:
            user_id: 用户 ID
            user_data: 更新数据
            current_user: 当前用户

        Returns:
            更新后的用户对象

        Raises:
            PermissionDeniedError: 非 admin 角色 (AUTH_500)
            ResourceNotFoundError: 用户不存在 (BIZ_002)
            ResourceConflictError: 用户名或邮箱已存在 (DB_004)
        """
        # 权限检查
        if current_user.role != "admin":
            raise PermissionDeniedError(
                message="权限不足：仅管理员可更新用户信息",
                code="AUTH_500"
            )

        # 查询用户
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ResourceNotFoundError(
                message=f"用户不存在: {user_id}",
                code="BIZ_002"
            )

        # 更新字段
        update_data = user_data.model_dump(exclude_unset=True)

        # BR-USER-001: 检查用户名唯一性
        if "username" in update_data and update_data["username"] != user.username:
            existing = self.db.query(User).filter(
                User.username == update_data["username"],
                User.id != user_id
            ).first()
            if existing:
                raise ResourceConflictError(
                    message=f"用户名已存在: {update_data['username']}",
                    code="DB_004"
                )
            user.username = update_data["username"]

        # BR-USER-002: 检查邮箱唯一性
        if "email" in update_data and update_data["email"] != user.email:
            existing = self.db.query(User).filter(
                User.email == update_data["email"],
                User.id != user_id
            ).first()
            if existing:
                raise ResourceConflictError(
                    message=f"邮箱已存在: {update_data['email']}",
                    code="DB_004"
                )
            user.email = update_data["email"]

        # 更新其他字段
        if "role" in update_data:
            user.role = update_data["role"]

        if "is_active" in update_data:
            user.is_active = update_data["is_active"]

        if "full_name" in update_data and hasattr(user, 'full_name'):
            user.full_name = update_data["full_name"]

        if "department" in update_data and hasattr(user, 'department'):
            user.department = update_data["department"]

        # 密码更新
        if "password" in update_data and update_data["password"]:
            user.hashed_password = hash_password(update_data["password"])

        self.db.commit()
        self.db.refresh(user)

        return user

    def delete_user(
        self,
        user_id: UUID,
        current_user: User
    ) -> bool:
        """
        删除用户（软删除 - 设置 is_active=False）

        权限: 仅 admin
        约束: 不能删除自己

        Args:
            user_id: 用户 ID
            current_user: 当前用户

        Returns:
            是否删除成功

        Raises:
            PermissionDeniedError: 非 admin 角色或尝试删除自己 (AUTH_500)
            ResourceNotFoundError: 用户不存在 (BIZ_002)
        """
        # 权限检查
        if current_user.role != "admin":
            raise PermissionDeniedError(
                message="权限不足：仅管理员可删除用户",
                code="AUTH_500"
            )

        # 不能删除自己
        if current_user.id == user_id:
            raise PermissionDeniedError(
                message="不能删除当前登录用户",
                code="AUTH_500"
            )

        # 查询用户
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ResourceNotFoundError(
                message=f"用户不存在: {user_id}",
                code="BIZ_002"
            )

        # 软删除：设置 is_active=False
        user.is_active = False
        self.db.commit()

        return True

    def get_user_statistics(
        self,
        current_user: User
    ) -> dict:
        """
        获取用户统计信息

        权限 (MASTER.md v4.4 §2.4): admin, ceo, finance, supervisor

        Returns:
            统计数据字典
        """
        allowed_roles = ["admin", "ceo", "finance", "supervisor"]
        if current_user.role not in allowed_roles:
            raise PermissionDeniedError(
                message="权限不足：无法查看用户统计",
                code="AUTH_500"
            )

        # 总用户数
        total = self.db.query(func.count(User.id)).scalar()

        # 活跃用户数
        active = self.db.query(func.count(User.id)).filter(User.is_active == True).scalar()

        # 各角色用户数
        role_counts = {}
        for role in VALID_ROLES:
            count = self.db.query(func.count(User.id)).filter(User.role == role).scalar()
            role_counts[role] = count

        return {
            "total": total,
            "active": active,
            "inactive": total - active,
            "by_role": role_counts
        }


def get_user_service(db: Session) -> UserService:
    """获取用户服务实例"""
    return UserService(db)
