"""
项目成员管理 Service

业务逻辑:
1. 每个项目最多一个 owner (通过数据库唯一约束保证)
2. 转移 owner 时需要原子操作
3. 只有 admin 或当前 owner 可以管理成员
4. 删除 owner 前必须先转移或降级

SoT Reference: MASTER.md v4.4 §2.4
"""

from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
import structlog

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_

from backend.models import User, Project
from backend.models.core.project_member import ProjectMember
from backend.schemas.project_member import (
    ProjectMemberCreateRequest,
    ProjectMemberUpdateRequest,
    TransferOwnershipRequest,
    ProjectMemberRole,
)
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError,
)

logger = structlog.get_logger(__name__)


class ProjectMemberService:
    """项目成员管理服务"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 权限检查 ====================

    def _check_management_permission(
        self,
        project_id: int,
        current_user: User,
        action: str = "manage"
    ) -> None:
        """
        检查用户是否有项目成员管理权限

        允许:
        - admin 角色
        - 项目 owner

        Args:
            project_id: 项目ID
            current_user: 当前用户
            action: 操作描述

        Raises:
            PermissionDeniedError: 无权限
        """
        # admin 有所有权限
        user_role = getattr(current_user, 'role', None)
        if user_role:
            role_value = user_role.value if hasattr(user_role, 'value') else str(user_role)
            if role_value == 'admin':
                return

        # 检查是否为项目 owner
        membership = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
            ProjectMember.role == 'owner'
        ).first()

        if not membership:
            raise PermissionDeniedError(
                f"无权限{action}项目成员",
                error_code="AUTH-002"
            )

    def _check_read_permission(
        self,
        project_id: int,
        current_user: User
    ) -> None:
        """
        检查用户是否有项目成员读取权限

        允许:
        - admin 角色
        - 项目任意成员

        Raises:
            PermissionDeniedError: 无权限
        """
        # admin 有所有权限
        user_role = getattr(current_user, 'role', None)
        if user_role:
            role_value = user_role.value if hasattr(user_role, 'value') else str(user_role)
            if role_value == 'admin':
                return

        # 检查是否为项目成员
        membership = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id
        ).first()

        if not membership:
            raise PermissionDeniedError(
                "无权限查看项目成员",
                error_code="AUTH-002"
            )

    # ==================== CRUD 操作 ====================

    def create_member(
        self,
        request: ProjectMemberCreateRequest,
        current_user: User
    ) -> ProjectMember:
        """
        创建项目成员

        Args:
            request: 创建请求
            current_user: 当前用户

        Returns:
            ProjectMember: 创建的成员

        Raises:
            ResourceNotFoundError: 项目或用户不存在
            ResourceConflictError: 成员已存在
            PermissionDeniedError: 无权限
        """
        # 权限检查
        self._check_management_permission(
            request.project_id,
            current_user,
            action="添加"
        )

        # 检查项目是否存在
        project = self.db.query(Project).filter(
            Project.id == request.project_id
        ).first()
        if not project:
            raise ResourceNotFoundError(
                f"项目 {request.project_id} 不存在",
                error_code="SYS-004"
            )

        # 检查用户是否存在
        user = self.db.query(User).filter(
            User.id == request.user_id
        ).first()
        if not user:
            raise ResourceNotFoundError(
                f"用户 {request.user_id} 不存在",
                error_code="SYS-004"
            )

        # 检查是否已是成员
        existing = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == request.project_id,
            ProjectMember.user_id == request.user_id
        ).first()
        if existing:
            raise ResourceConflictError(
                f"用户已是项目成员 (角色: {existing.role})",
                error_code="BIZ_001"
            )

        # 如果添加为 owner，检查是否已有 owner
        role_value = request.role.value if hasattr(request.role, 'value') else str(request.role)
        if role_value == 'owner':
            existing_owner = self.db.query(ProjectMember).filter(
                ProjectMember.project_id == request.project_id,
                ProjectMember.role == 'owner'
            ).first()
            if existing_owner:
                raise ResourceConflictError(
                    "项目已有负责人，请使用转移负责人功能",
                    error_code="BIZ_002"
                )

        # 创建成员
        member = ProjectMember(
            project_id=request.project_id,
            user_id=request.user_id,
            role=role_value,
            permissions=request.permissions,
            notes=request.notes
        )

        try:
            self.db.add(member)
            self.db.commit()
            self.db.refresh(member)

            logger.info(
                "project_member_created",
                project_id=request.project_id,
                user_id=str(request.user_id),
                role=role_value,
                operator=str(current_user.id)
            )

            return member

        except IntegrityError as e:
            self.db.rollback()
            if 'idx_one_owner_per_project' in str(e):
                raise ResourceConflictError(
                    "项目已有负责人",
                    error_code="BIZ_002"
                )
            raise ResourceConflictError(
                "成员已存在",
                error_code="BIZ_001"
            )

    def get_member(
        self,
        member_id: int,
        current_user: User
    ) -> ProjectMember:
        """
        获取单个项目成员

        Args:
            member_id: 成员关系ID
            current_user: 当前用户

        Returns:
            ProjectMember: 成员信息

        Raises:
            ResourceNotFoundError: 成员不存在
            PermissionDeniedError: 无权限
        """
        member = self.db.query(ProjectMember).filter(
            ProjectMember.id == member_id
        ).first()

        if not member:
            raise ResourceNotFoundError(
                f"成员关系 {member_id} 不存在",
                error_code="SYS-004"
            )

        # 权限检查
        self._check_read_permission(member.project_id, current_user)

        return member

    def get_project_members(
        self,
        project_id: int,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        role: Optional[str] = None
    ) -> Tuple[List[ProjectMember], int]:
        """
        获取项目成员列表

        Args:
            project_id: 项目ID
            current_user: 当前用户
            page: 页码
            page_size: 每页数量
            role: 筛选角色

        Returns:
            Tuple[List[ProjectMember], int]: (成员列表, 总数)
        """
        # 权限检查
        self._check_read_permission(project_id, current_user)

        # 构建查询
        query = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id
        )

        if role:
            query = query.filter(ProjectMember.role == role)

        # 总数
        total = query.count()

        # 分页
        members = query.order_by(
            # owner 排第一
            ProjectMember.role.desc(),
            ProjectMember.created_at.asc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return members, total

    def get_user_projects(
        self,
        user_id: UUID,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        role: Optional[str] = None
    ) -> Tuple[List[ProjectMember], int]:
        """
        获取用户参与的项目列表

        Args:
            user_id: 用户ID
            current_user: 当前用户
            page: 页码
            page_size: 每页数量
            role: 筛选角色

        Returns:
            Tuple[List[ProjectMember], int]: (成员关系列表, 总数)
        """
        # 只允许查看自己的项目或 admin
        user_role = getattr(current_user, 'role', None)
        is_admin = False
        if user_role:
            role_value = user_role.value if hasattr(user_role, 'value') else str(user_role)
            is_admin = role_value == 'admin'

        if not is_admin and current_user.id != user_id:
            raise PermissionDeniedError(
                "只能查看自己参与的项目",
                error_code="AUTH-002"
            )

        # 构建查询
        query = self.db.query(ProjectMember).filter(
            ProjectMember.user_id == user_id
        )

        if role:
            query = query.filter(ProjectMember.role == role)

        # 总数
        total = query.count()

        # 分页
        members = query.order_by(
            ProjectMember.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return members, total

    def update_member(
        self,
        member_id: int,
        request: ProjectMemberUpdateRequest,
        current_user: User
    ) -> ProjectMember:
        """
        更新项目成员

        Args:
            member_id: 成员关系ID
            request: 更新请求
            current_user: 当前用户

        Returns:
            ProjectMember: 更新后的成员

        Raises:
            ResourceNotFoundError: 成员不存在
            PermissionDeniedError: 无权限
            ResourceConflictError: 角色冲突
        """
        member = self.db.query(ProjectMember).filter(
            ProjectMember.id == member_id
        ).first()

        if not member:
            raise ResourceNotFoundError(
                f"成员关系 {member_id} 不存在",
                error_code="SYS-004"
            )

        # 权限检查
        self._check_management_permission(
            member.project_id,
            current_user,
            action="更新"
        )

        # 如果要更新为 owner
        if request.role:
            new_role = request.role.value if hasattr(request.role, 'value') else str(request.role)

            if new_role == 'owner' and member.role != 'owner':
                # 检查是否已有 owner
                existing_owner = self.db.query(ProjectMember).filter(
                    ProjectMember.project_id == member.project_id,
                    ProjectMember.role == 'owner',
                    ProjectMember.id != member_id
                ).first()

                if existing_owner:
                    raise ResourceConflictError(
                        "项目已有负责人，请使用转移负责人功能",
                        error_code="BIZ_002"
                    )

            member.role = new_role

        if request.permissions is not None:
            member.permissions = request.permissions

        if request.notes is not None:
            member.notes = request.notes

        try:
            self.db.commit()
            self.db.refresh(member)

            logger.info(
                "project_member_updated",
                member_id=member_id,
                project_id=member.project_id,
                operator=str(current_user.id)
            )

            return member

        except IntegrityError:
            self.db.rollback()
            raise ResourceConflictError(
                "更新失败：角色冲突",
                error_code="BIZ_002"
            )

    def delete_member(
        self,
        member_id: int,
        current_user: User
    ) -> None:
        """
        删除项目成员

        Args:
            member_id: 成员关系ID
            current_user: 当前用户

        Raises:
            ResourceNotFoundError: 成员不存在
            PermissionDeniedError: 无权限
            BusinessLogicError: owner 不能直接删除
        """
        member = self.db.query(ProjectMember).filter(
            ProjectMember.id == member_id
        ).first()

        if not member:
            raise ResourceNotFoundError(
                f"成员关系 {member_id} 不存在",
                error_code="SYS-004"
            )

        # 权限检查
        self._check_management_permission(
            member.project_id,
            current_user,
            action="删除"
        )

        # owner 不能直接删除
        if member.role == 'owner':
            raise BusinessLogicError(
                "项目负责人不能直接删除，请先转移负责人",
                error_code="BIZ_003"
            )

        project_id = member.project_id
        user_id = str(member.user_id)

        self.db.delete(member)
        self.db.commit()

        logger.info(
            "project_member_deleted",
            member_id=member_id,
            project_id=project_id,
            deleted_user_id=user_id,
            operator=str(current_user.id)
        )

    # ==================== 特殊操作 ====================

    def transfer_ownership(
        self,
        project_id: int,
        request: TransferOwnershipRequest,
        current_user: User
    ) -> Dict[str, Any]:
        """
        转移项目负责人

        原子操作：
        1. 将当前 owner 降级
        2. 将新用户升级为 owner

        Args:
            project_id: 项目ID
            request: 转移请求
            current_user: 当前用户

        Returns:
            Dict: 包含 previous_owner 和 new_owner

        Raises:
            ResourceNotFoundError: 项目/用户/成员不存在
            PermissionDeniedError: 无权限
            BusinessLogicError: 转移失败
        """
        # 权限检查 (只有 admin 或当前 owner 可以转移)
        self._check_management_permission(
            project_id,
            current_user,
            action="转移负责人"
        )

        # 检查新负责人是否是项目成员
        new_owner_member = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == request.new_owner_user_id
        ).first()

        if not new_owner_member:
            # 检查用户是否存在
            user = self.db.query(User).filter(
                User.id == request.new_owner_user_id
            ).first()
            if not user:
                raise ResourceNotFoundError(
                    f"用户 {request.new_owner_user_id} 不存在",
                    error_code="SYS-004"
                )
            # 自动添加为成员
            new_owner_member = ProjectMember(
                project_id=project_id,
                user_id=request.new_owner_user_id,
                role='member'
            )
            self.db.add(new_owner_member)
            self.db.flush()

        # 获取当前 owner
        current_owner = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.role == 'owner'
        ).first()

        previous_owner_data = None

        # 原子转移
        try:
            # 降级当前 owner
            if current_owner:
                demote_role = request.demote_current_to.value if hasattr(
                    request.demote_current_to, 'value'
                ) else str(request.demote_current_to)
                current_owner.role = demote_role
                previous_owner_data = current_owner

            # 升级新 owner
            new_owner_member.role = 'owner'

            self.db.commit()
            self.db.refresh(new_owner_member)
            if previous_owner_data:
                self.db.refresh(previous_owner_data)

            logger.info(
                "project_ownership_transferred",
                project_id=project_id,
                previous_owner=str(current_owner.user_id) if current_owner else None,
                new_owner=str(request.new_owner_user_id),
                operator=str(current_user.id)
            )

            return {
                "previous_owner": previous_owner_data,
                "new_owner": new_owner_member
            }

        except IntegrityError:
            self.db.rollback()
            raise BusinessLogicError(
                "转移负责人失败：数据冲突",
                error_code="BIZ_003"
            )

    def get_project_owner(
        self,
        project_id: int
    ) -> Optional[ProjectMember]:
        """
        获取项目负责人

        Args:
            project_id: 项目ID

        Returns:
            Optional[ProjectMember]: 负责人成员关系，无则返回 None
        """
        return self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.role == 'owner'
        ).first()

    def batch_add_members(
        self,
        members_data: List[ProjectMemberCreateRequest],
        current_user: User
    ) -> Dict[str, Any]:
        """
        批量添加成员

        Args:
            members_data: 成员数据列表
            current_user: 当前用户

        Returns:
            Dict: 包含 success_count, failed_count, members, errors
        """
        results = {
            "success_count": 0,
            "failed_count": 0,
            "members": [],
            "errors": []
        }

        for i, member_data in enumerate(members_data):
            try:
                member = self.create_member(member_data, current_user)
                results["success_count"] += 1
                results["members"].append(member)
            except Exception as e:
                results["failed_count"] += 1
                results["errors"].append({
                    "index": i,
                    "user_id": str(member_data.user_id),
                    "project_id": member_data.project_id,
                    "error": str(e)
                })

        return results
