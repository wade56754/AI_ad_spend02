"""
项目管理业务逻辑层
Version: 1.0
Author: Claude协作开发
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any

from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from core.response import success_response, error_response, paginated_response
from exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError
)
from models.project import Project, ProjectMember, ProjectExpense
from models.user import User
from schemas.project import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectMemberAssignRequest,
    ProjectExpenseRequest
)


class ProjectService:
    """项目管理服务类"""

    def __init__(self, db: Session):
        self.db = db

    def create_project(
        self,
        request: ProjectCreateRequest,
        current_user: User
    ) -> Project:
        """创建项目"""
        if current_user.role != "admin":
            raise PermissionDeniedError("只有管理员可以创建项目")

        # 检查项目名称是否已存在
        if self.db.query(Project).filter(Project.name == request.name).first():
            raise ResourceConflictError(f"项目名称 '{request.name}' 已存在")

        # 创建项目
        project = Project(
            name=request.name,
            client_name=request.client_name,
            client_company=request.client_company,
            description=request.description,
            budget=request.budget,
            currency=request.currency,
            start_date=request.start_date,
            end_date=request.end_date,
            account_manager_id=request.account_manager_id,
            created_by=current_user.id
        )

        self.db.add(project)
        self.db.flush()

        # 记录审计日志
        self._create_audit_log(
            project_id=project.id,
            action="created",
            user_id=current_user.id
        )

        self.db.commit()
        return project

    def get_projects(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        manager_id: Optional[int] = None,
        client_name: Optional[str] = None
    ) -> tuple[List[Project], int]:
        """获取项目列表"""
        query = self.db.query(Project)

        # 应用权限过滤
        query = self._apply_permission_filter(query, current_user)

        # 应用筛选条件
        if status:
            query = query.filter(Project.status == status)
        if manager_id:
            query = query.filter(Project.account_manager_id == manager_id)
        if client_name:
            query = query.filter(Project.client_name.ilike(f"%{client_name}%"))

        # 统计总数
        total = query.count()

        # 分页查询
        projects = query.order_by(desc(Project.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return projects, total

    def get_project(self, project_id: int, current_user: User) -> Project:
        """获取项目详情"""
        project = self.db.query(Project).options(
            joinedload(Project.account_manager),
            joinedload(Project.creator),
            joinedload(Project.members),
            joinedload(Project.expenses)
        ).filter(Project.id == project_id).first()

        if not project:
            raise ResourceNotFoundError(f"项目 {project_id} 不存在")

        # 检查权限
        if not self._can_user_access_project(current_user, project):
            raise PermissionDeniedError("无权限查看该项目")

        # 计算统计信息
        project.total_accounts = len(project.ad_accounts) if hasattr(project, 'ad_accounts') else 0
        project.active_accounts = len([a for a in project.ad_accounts if hasattr(a, 'status') and a.status == 'active']) if hasattr(project, 'ad_accounts') else 0
        project.total_spent = sum(e.amount for e in project.expenses) if hasattr(project, 'expenses') else 0

        return project

    def update_project(
        self,
        project_id: int,
        request: ProjectUpdateRequest,
        current_user: User
    ) -> Project:
        """更新项目"""
        project = self.get_project(project_id, current_user)

        # 检查权限
        if not self._can_user_update_project(current_user, project):
            raise PermissionDeniedError("无权限更新该项目")

        # 检查项目名称是否重复
        if request.name and request.name != project.name:
            if self.db.query(Project).filter(
                and_(Project.name == request.name, Project.id != project_id)
            ).first():
                raise ResourceConflictError(f"项目名称 '{request.name}' 已存在")

        # 更新字段
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(project, field):
                setattr(project, field, value)

        project.updated_by = current_user.id
        project.updated_at = datetime.utcnow()

        # 记录审计日志
        self._create_audit_log(
            project_id=project_id,
            action="updated",
            user_id=current_user.id
        )

        self.db.commit()
        return project

    def delete_project(self, project_id: int, current_user: User) -> bool:
        """删除项目"""
        if current_user.role != "admin":
            raise PermissionDeniedError("只有管理员可以删除项目")

        project = self.get_project(project_id, current_user)

        # 检查是否可以删除（有关联的账户等）
        if hasattr(project, 'ad_accounts') and len(project.ad_accounts) > 0:
            raise BusinessLogicError("项目下还有广告账户，无法删除")

        # 删除相关记录
        self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id
        ).delete()

        self.db.query(ProjectExpense).filter(
            ProjectExpense.project_id == project_id
        ).delete()

        # 删除项目
        self.db.delete(project)
        self.db.commit()

        return True

    def assign_member(
        self,
        project_id: int,
        request: ProjectMemberAssignRequest,
        current_user: User
    ) -> ProjectMember:
        """分配项目成员"""
        if current_user.role not in ["admin", "account_manager"]:
            raise PermissionDeniedError("无权限分配项目成员")

        project = self.get_project(project_id, current_user)

        # 检查用户是否存在
        user = self.db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise ResourceNotFoundError(f"用户 {request.user_id} 不存在")

        # 检查是否已经是成员
        existing = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == request.user_id
        ).first()

        if existing:
            raise ResourceConflictError("用户已经是项目成员")

        # 添加成员
        member = ProjectMember(
            project_id=project_id,
            user_id=request.user_id,
            role=request.role
        )

        self.db.add(member)
        self.db.commit()

        return member

    def remove_member(self, project_id: int, user_id: int, current_user: User) -> bool:
        """移除项目成员"""
        project = self.get_project(project_id, current_user)

        member = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()

        if not member:
            raise ResourceNotFoundError("用户不是项目成员")

        # 不能移除项目经理
        if member.role == "account_manager" and current_user.role != "admin":
            raise PermissionDeniedError("只有管理员可以移除项目经理")

        self.db.delete(member)
        self.db.commit()

        return True

    def add_expense(
        self,
        project_id: int,
        request: ProjectExpenseRequest,
        current_user: User
    ) -> ProjectExpense:
        """添加项目费用"""
        project = self.get_project(project_id, current_user)

        if not self._can_user_add_expense(current_user, project):
            raise PermissionDeniedError("无权限添加项目费用")

        expense = ProjectExpense(
            project_id=project_id,
            expense_type=request.expense_type,
            amount=request.amount,
            description=request.description,
            expense_date=request.expense_date,
            created_by=current_user.id
        )

        self.db.add(expense)
        self.db.commit()

        return expense

    def get_project_members(self, project_id: int, current_user: User) -> List[ProjectMember]:
        """获取项目成员列表"""
        project = self.get_project(project_id, current_user)

        members = self.db.query(ProjectMember).options(
            joinedload(ProjectMember.user)
        ).filter(ProjectMember.project_id == project_id).all()

        return members

    def get_project_expenses(
        self,
        project_id: int,
        current_user: User,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[ProjectExpense], int]:
        """获取项目费用列表"""
        project = self.get_project(project_id, current_user)

        query = self.db.query(ProjectExpense).options(
            joinedload(ProjectExpense.creator)
        ).filter(ProjectExpense.project_id == project_id)

        total = query.count()
        expenses = query.order_by(desc(ProjectExpense.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return expenses, total

    def get_project_statistics(self, current_user: User) -> Dict[str, Any]:
        """获取项目统计信息"""
        query = self.db.query(Project)

        # 应用权限过滤
        query = self._apply_permission_filter(query, current_user)

        # 基础统计
        stats = query.with_entities(
            func.count(Project.id).label('total_projects'),
            func.sum(Project.budget).label('total_budget'),
            func.count(func.distinct(Project.client_company)).label('total_clients')
        ).first()

        # 按状态统计
        status_stats = query.with_entities(
            Project.status,
            func.count(Project.id).label('count')
        ).group_by(Project.status).all()

        # 构建结果
        result = {
            'total_projects': stats.total_projects or 0,
            'active_projects': next((s.count for s in status_stats if s.status == 'active'), 0),
            'paused_projects': next((s.count for s in status_stats if s.status == 'paused'), 0),
            'completed_projects': next((s.count for s in status_stats if s.status == 'completed'), 0),
            'cancelled_projects': next((s.count for s in status_stats if s.status == 'cancelled'), 0),
            'total_budget': stats.total_budget or Decimal('0'),
            'total_clients': stats.total_clients or 0,
            'avg_project_value': (stats.total_budget or Decimal('0')) / max(stats.total_projects or 1, 1)
        }

        # 计算总消耗（从费用表）
        if current_user.role in ['admin', 'finance', 'data_operator']:
            total_spent = self.db.query(func.sum(ProjectExpense.amount)).scalar() or Decimal('0')
            result['total_spent'] = total_spent

        return result

    # 私有方法
    def _apply_permission_filter(self, query, current_user: User):
        """应用权限过滤"""
        if current_user.role == "admin":
            return query
        elif current_user.role == "account_manager":
            return query.filter(Project.account_manager_id == current_user.id)
        elif current_user.role == "media_buyer":
            # 投手只能看到自己参与的项目
            return query.join(ProjectMember).filter(ProjectMember.user_id == current_user.id)
        else:
            # finance和data_operator可以查看所有项目
            return query

    def _can_user_access_project(self, user: User, project: Project) -> bool:
        """检查用户是否可以访问项目"""
        if user.role == "admin":
            return True
        elif user.role == "account_manager":
            return project.account_manager_id == user.id
        elif user.role == "media_buyer":
            return any(m.user_id == user.id for m in project.members)
        else:
            return True  # finance和data_operator可以查看所有项目

    def _can_user_update_project(self, user: User, project: Project) -> bool:
        """检查用户是否可以更新项目"""
        if user.role == "admin":
            return True
        elif user.role == "account_manager":
            return project.account_manager_id == user.id
        else:
            return False

    def _can_user_add_expense(self, user: User, project: Project) -> bool:
        """检查用户是否可以添加费用"""
        if user.role in ["admin", "account_manager"]:
            return True
        else:
            return False

    def _create_audit_log(self, project_id: int, action: str, user_id: int, details: Optional[str] = None):
        """创建审计日志（简化版，实际应该有专门的审计日志表）"""
        # TODO: 实现审计日志记录
        pass