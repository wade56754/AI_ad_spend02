"""
项目管理业务逻辑层 (重构版)

SoT Reference: API_SOT.md v9.3 §6 (Projects API)
SoT Reference: STATE_MACHINE.md v2.6 §5 (项目状态机)

依赖代码块:
- response-envelope: 统一响应格式
- error-codes: 错误码枚举
- pagination: 分页查询
- permission-filter: 权限过滤
- audit-log: 审计日志
- state-machine: 状态流转
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, desc
from sqlalchemy.orm import Session, joinedload

from backend.core.audit import audit_logger
from backend.core.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError,
    BusinessError,
    raise_not_found,
    raise_permission_denied,
    raise_validation_error,
    raise_conflict,
)
from backend.core.error_codes import BusinessErrorCodes, ValidationErrorCodes
from backend.core.pagination import PaginationParams, paginate
from backend.core.permissions import apply_permission_filter
from backend.core.state_machine import ProjectStatus
from backend.models import (
    Project,
    ProjectMember,
    ProjectExpense,
    User,
    AdAccount,
    DailyReport,
)
from backend.schemas.project import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectMemberAssignRequest,
    ProjectExpenseRequest,
    ProjectMarkFulfilledRequest,
)


class ProjectService:
    """
    项目管理服务类

    职责:
    - 项目 CRUD 操作
    - 项目成员管理
    - 项目费用管理
    - 权限过滤和审计日志

    依赖:
    - apply_permission_filter: 角色数据过滤
    - audit_log: 审计日志装饰器
    - paginate: 分页查询
    """

    def __init__(self, db: Session):
        self.db = db

    # ========================================
    # 项目 CRUD
    # ========================================

    def create_project(
        self, request: ProjectCreateRequest, current_user: User
    ) -> Project:
        """
        创建项目

        权限: admin, ceo, project_owner
        初始状态: draft

        SoT: 户管(account_manager)只能管理账户，不能创建项目

        Args:
            request: 创建请求
            current_user: 当前用户

        Returns:
            创建的项目实例

        Raises:
            PermissionError: 权限不足
            ConflictError: 项目名称已存在
            ValidationError: 验证失败
        """
        # 权限检查 - 只有 admin/ceo/project_owner 可以创建项目
        if current_user.role not in ["admin", "ceo", "project_owner"]:
            raise_permission_denied("create_project")

        # 检查项目名称是否已存在
        existing = self.db.query(Project).filter(Project.name == request.name).first()
        if existing:
            raise_conflict("Project", request.name)

        # 验证日期范围
        if request.start_date and request.end_date:
            if request.end_date < request.start_date:
                raise_validation_error("end_date", "结束日期不能早于开始日期")

        # 创建项目 (初始状态: draft)
        project = Project(
            name=request.name,
            client_name=request.client_name,
            client_company=request.client_company,
            description=request.description,
            budget=request.budget or Decimal("0.00"),
            currency=request.currency or "CNY",
            start_date=request.start_date,
            end_date=request.end_date,
            account_manager_id=request.account_manager_id,
            status=ProjectStatus.DRAFT.value,
            created_by=current_user.id,
        )

        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

        return project

    def get_projects(
        self,
        current_user: User,
        pagination: PaginationParams,
        status: Optional[str] = None,
        client_name: Optional[str] = None,
    ) -> Tuple[List[Project], int]:
        """
        获取项目列表 (带权限过滤和分页)

        权限过滤规则:
        - admin/ceo: 全部项目
        - account_manager: 自己负责的项目
        - pitcher: 参与的项目

        Args:
            current_user: 当前用户
            pagination: 分页参数
            status: 状态筛选
            client_name: 客户名称筛选

        Returns:
            (项目列表, 总数)
        """
        query = self.db.query(Project)

        # 使用 permission-filter 代码块进行权限过滤
        query = apply_permission_filter(query, Project, current_user, self.db)

        # 应用筛选条件
        if status:
            query = query.filter(Project.status == status)
        if client_name:
            query = query.filter(Project.client_name.ilike(f"%{client_name}%"))

        # 使用 pagination 代码块进行分页
        items, total = paginate(query, pagination, Project)

        # 批量计算统计字段
        self._compute_batch_project_stats(items)

        return items, total

    def get_project(self, project_id: int, current_user: User) -> Project:
        """
        获取项目详情

        Args:
            project_id: 项目 ID
            current_user: 当前用户

        Returns:
            项目实例

        Raises:
            NotFoundError: 项目不存在
            PermissionError: 无权访问
        """
        project = (
            self.db.query(Project)
            .options(
                joinedload(Project.creator),
                joinedload(Project.members).joinedload(ProjectMember.user),
            )
            .filter(Project.id == project_id)
            .first()
        )

        if not project:
            raise_not_found("Project", project_id)

        # 权限检查
        if not self._can_access_project(current_user, project):
            raise_permission_denied("view_project", str(project_id))

        # 计算统计字段
        self._compute_project_stats(project)

        return project

    def update_project(
        self, project_id: int, request: ProjectUpdateRequest, current_user: User
    ) -> Project:
        """
        更新项目

        权限: admin, account_manager (仅自己负责的项目)

        Args:
            project_id: 项目 ID
            request: 更新请求
            current_user: 当前用户

        Returns:
            更新后的项目

        Raises:
            NotFoundError: 项目不存在
            PermissionError: 无权更新
            ConflictError: 名称冲突
            ValidationError: 状态无效
        """
        project = self.get_project(project_id, current_user)

        # 权限检查
        if not self._can_update_project(current_user, project):
            raise_permission_denied("update_project", str(project_id))

        # 检查名称冲突
        if request.name and request.name != project.name:
            existing = (
                self.db.query(Project)
                .filter(and_(Project.name == request.name, Project.id != project_id))
                .first()
            )
            if existing:
                raise_conflict("Project", request.name)

        # 验证状态值
        if request.status:
            valid_statuses = [s.value for s in ProjectStatus]
            if request.status not in valid_statuses:
                raise_validation_error("status", f"无效状态，允许值: {valid_statuses}")

        # 更新字段
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(project, field) and value is not None:
                setattr(project, field, value)

        self.db.commit()
        self.db.refresh(project)

        return project

    def delete_project(self, project_id: int, current_user: User) -> bool:
        """
        删除项目

        权限: admin only

        Args:
            project_id: 项目 ID
            current_user: 当前用户

        Returns:
            True 删除成功

        Raises:
            NotFoundError: 项目不存在
            PermissionError: 无权删除
            BusinessError: 有关联数据无法删除
        """
        if current_user.role != "admin":
            raise_permission_denied("delete_project")

        project = self.get_project(project_id, current_user)

        # 检查关联数据
        expense_count = (
            self.db.query(ProjectExpense)
            .filter(ProjectExpense.project_id == project_id)
            .count()
        )

        if expense_count > 0:
            raise BusinessError(
                message="项目有关联的费用记录，无法删除",
                error=BusinessErrorCodes.RESOURCE_HAS_DEPENDENCIES,
            )

        # 删除成员关联
        self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id
        ).delete()

        # 删除项目
        self.db.delete(project)
        self.db.commit()

        return True

    def mark_project_fulfilled(
        self, project_id: int, request: ProjectMarkFulfilledRequest, current_user: User
    ) -> Project:
        """
        标记项目履约完成

        SoT Reference: BUSINESS_RULES.md v4.6 BR-PROJ-006
        SoT Reference: BI-06 履约完成唯一判定条件

        权限: admin, project_owner, account_manager (仅负责的项目)

        状态转换: running -> fulfilled (不可逆)

        Args:
            project_id: 项目 ID
            request: 履约完成请求 (reason, note)
            current_user: 当前用户

        Returns:
            更新后的项目

        Raises:
            NotFoundError: 项目不存在
            PermissionError: 无权操作
            BusinessError: 项目已履约完成，不可重复操作
        """
        project = self.get_project(project_id, current_user)

        # 权限检查: admin, project_owner, account_manager (仅自己负责的)
        can_fulfill = False
        if current_user.role in ["admin", "project_owner", "ceo"]:
            can_fulfill = True
        elif current_user.role == "account_manager":
            can_fulfill = project.account_manager_id == self._user_id_to_int(
                current_user.id
            )

        if not can_fulfill:
            raise_permission_denied("mark_project_fulfilled", str(project_id))

        # 检查当前履约状态
        if project.fulfillment_status == "fulfilled":
            raise BusinessError(
                message="项目已履约完成，不可重复操作",
                error=BusinessErrorCodes.INVALID_STATE_TRANSITION,
            )

        # 执行状态转换
        project.fulfillment_status = "fulfilled"
        project.fulfillment_reason = request.reason
        project.fulfilled_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(project)

        # 计算统计字段
        self._compute_project_stats(project)

        return project

    # ========================================
    # 项目成员管理
    # ========================================

    def assign_member(
        self, project_id: int, request: ProjectMemberAssignRequest, current_user: User
    ) -> ProjectMember:
        """
        分配项目成员

        权限: admin, account_manager

        Args:
            project_id: 项目 ID
            request: 分配请求 (user_id, role)
            current_user: 当前用户

        Returns:
            创建的成员关联

        Raises:
            NotFoundError: 项目或用户不存在
            ConflictError: 用户已是成员
            PermissionError: 无权操作
        """
        if current_user.role not in ["admin", "account_manager"]:
            raise_permission_denied("assign_member")

        # 验证项目存在
        project = self.get_project(project_id, current_user)

        # 转换 user_id 为 UUID
        user_id = self._to_uuid(request.user_id)

        # 验证用户存在
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise_not_found("User", str(user_id))

        # 检查是否已是成员
        existing = (
            self.db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
            )
            .first()
        )

        if existing:
            raise_conflict("ProjectMember", f"{project_id}:{user_id}")

        # 创建成员关联
        member = ProjectMember(
            project_id=project_id, user_id=user_id, role=request.role
        )

        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)

        return member

    def get_project_members(
        self, project_id: int, current_user: User
    ) -> List[ProjectMember]:
        """获取项目成员列表"""
        # 验证项目访问权限
        self.get_project(project_id, current_user)

        members = (
            self.db.query(ProjectMember)
            .options(joinedload(ProjectMember.user))
            .filter(ProjectMember.project_id == project_id)
            .all()
        )

        return members

    def remove_member(self, project_id: int, user_id: str, current_user: User) -> bool:
        """
        移除项目成员

        权限: admin, account_manager

        Args:
            project_id: 项目 ID
            user_id: 用户 ID (UUID 字符串)
            current_user: 当前用户

        Returns:
            True 删除成功

        Raises:
            NotFoundError: 成员不存在
            PermissionError: 无权操作
        """
        if current_user.role not in ["admin", "account_manager"]:
            raise_permission_denied("remove_member")

        # 验证项目存在
        self.get_project(project_id, current_user)

        # 转换 user_id
        uid = self._to_uuid(user_id)

        member = (
            self.db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id, ProjectMember.user_id == uid
            )
            .first()
        )

        if not member:
            raise_not_found("ProjectMember", f"{project_id}:{user_id}")

        # 不能移除项目经理 (除非是 admin)
        if member.role == "owner" and current_user.role != "admin":
            raise_permission_denied("remove_project_owner")

        self.db.delete(member)
        self.db.commit()

        return True

    # ========================================
    # 项目费用管理
    # ========================================

    def add_expense(
        self, project_id: int, request: ProjectExpenseRequest, current_user: User
    ) -> ProjectExpense:
        """添加项目费用"""
        project = self.get_project(project_id, current_user)

        if current_user.role not in ["admin", "account_manager", "finance"]:
            raise_permission_denied("add_expense")

        expense = ProjectExpense(
            project_id=project_id,
            expense_type=request.expense_type,
            amount=request.amount,
            description=request.description,
            expense_date=request.expense_date,
            created_by=current_user.id,
        )

        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)

        return expense

    def get_project_expenses(
        self, project_id: int, current_user: User, pagination: PaginationParams
    ) -> Tuple[List[ProjectExpense], int]:
        """获取项目费用列表 (分页)"""
        # 验证项目访问权限
        self.get_project(project_id, current_user)

        query = self.db.query(ProjectExpense).filter(
            ProjectExpense.project_id == project_id
        )

        items, total = paginate(query, pagination, ProjectExpense)

        return items, total

    # ========================================
    # 统计
    # ========================================

    def get_project_statistics(self, current_user: User) -> dict:
        """
        获取项目统计信息

        权限: admin, finance, ceo, project_owner
        注意: account_manager 只能管理账户，不能查看项目统计

        SoT Reference: BUSINESS_RULES.md v4.6 BR-PROJ-006
        """
        # project_owner 需要统计信息来监督项目
        # account_manager 不允许查看统计信息 (test_project_permissions.py:122)
        if current_user.role not in [
            "admin",
            "finance",
            "ceo",
            "project_owner",
        ]:
            raise_permission_denied("view_statistics")

        query = self.db.query(Project)
        query = apply_permission_filter(query, Project, current_user, self.db)

        # 基础统计
        total = query.count()
        active = query.filter(Project.status == ProjectStatus.ACTIVE.value).count()
        suspended = query.filter(
            Project.status == ProjectStatus.SUSPENDED.value
        ).count()
        archived = query.filter(Project.status == ProjectStatus.ARCHIVED.value).count()
        draft = query.filter(Project.status == ProjectStatus.DRAFT.value).count()

        # 履约状态统计 (BUSINESS_RULES.md v4.6 BR-PROJ-006)
        fulfilled = query.filter(Project.fulfillment_status == "fulfilled").count()
        running = query.filter(Project.fulfillment_status == "running").count()

        # 预算汇总
        budget_sum = query.with_entities(func.sum(Project.budget)).scalar() or Decimal(
            "0.00"
        )

        return {
            "total_projects": total,
            "active_projects": active,
            "suspended_projects": suspended,
            "archived_projects": archived,
            "draft_projects": draft,
            "fulfilled_projects": fulfilled,
            "running_projects": running,
            "total_budget": budget_sum,
        }

    # ========================================
    # 私有方法
    # ========================================

    def _can_access_project(self, user: User, project: Project) -> bool:
        """检查用户是否可以访问项目"""
        if user.role in ["admin", "ceo", "finance"]:
            return True

        if user.role == "account_manager":
            return project.account_manager_id == self._user_id_to_int(user.id)

        # pitcher: 必须是项目成员
        member = (
            self.db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project.id, ProjectMember.user_id == user.id
            )
            .first()
        )

        return member is not None

    def _can_update_project(self, user: User, project: Project) -> bool:
        """检查用户是否可以更新项目"""
        if user.role == "admin":
            return True

        if user.role == "account_manager":
            return project.account_manager_id == self._user_id_to_int(user.id)

        return False

    def _compute_project_stats(self, project: Project) -> None:
        """
        计算项目统计字段

        聚合数据:
        - total_spent: 总消耗 (从费用记录)
        - total_follows: 总进粉数 (从日报聚合)
        - total_accounts: 账户数
        - active_accounts: 活跃账户数
        """
        # 总消耗 (从费用记录)
        total_spent = self.db.query(func.sum(ProjectExpense.amount)).filter(
            ProjectExpense.project_id == project.id
        ).scalar() or Decimal("0.00")

        # 获取项目下的广告账户ID列表
        account_ids = (
            self.db.query(AdAccount.id).filter(AdAccount.project_id == project.id).all()
        )
        account_id_list = [a[0] for a in account_ids]

        # 统计账户数
        total_accounts = len(account_id_list)
        active_accounts = (
            self.db.query(AdAccount)
            .filter(AdAccount.project_id == project.id, AdAccount.status == "active")
            .count()
        )

        # 聚合进粉数 (从日报的 follows_count 字段)
        total_follows = 0
        if account_id_list:
            result = (
                self.db.query(func.sum(DailyReport.follows_count))
                .filter(DailyReport.ad_account_id.in_(account_id_list))
                .scalar()
            )
            total_follows = result or 0

        project.total_spent = total_spent
        project.total_accounts = total_accounts
        project.active_accounts = active_accounts
        project.total_follows = total_follows

    def _compute_batch_project_stats(self, projects: List[Project]) -> None:
        """
        批量计算项目统计字段 (优化性能)

        对于列表查询，使用批量聚合查询而不是单个查询
        """
        if not projects:
            return

        project_ids = [p.id for p in projects]

        # 批量查询账户数
        account_counts = dict(
            self.db.query(AdAccount.project_id, func.count(AdAccount.id))
            .filter(AdAccount.project_id.in_(project_ids))
            .group_by(AdAccount.project_id)
            .all()
        )

        # 批量查询活跃账户数
        active_counts = dict(
            self.db.query(AdAccount.project_id, func.count(AdAccount.id))
            .filter(AdAccount.project_id.in_(project_ids), AdAccount.status == "active")
            .group_by(AdAccount.project_id)
            .all()
        )

        # 批量查询进粉数 (通过账户关联日报)
        # 子查询: 获取每个项目的账户ID
        follows_subquery = (
            self.db.query(
                AdAccount.project_id,
                func.sum(DailyReport.follows_count).label("total_follows"),
            )
            .join(DailyReport, DailyReport.ad_account_id == AdAccount.id)
            .filter(AdAccount.project_id.in_(project_ids))
            .group_by(AdAccount.project_id)
            .all()
        )

        follows_counts = {r[0]: r[1] or 0 for r in follows_subquery}

        # 批量查询费用
        expense_sums = dict(
            self.db.query(ProjectExpense.project_id, func.sum(ProjectExpense.amount))
            .filter(ProjectExpense.project_id.in_(project_ids))
            .group_by(ProjectExpense.project_id)
            .all()
        )

        # 赋值给每个项目
        for project in projects:
            project.total_accounts = account_counts.get(project.id, 0)
            project.active_accounts = active_counts.get(project.id, 0)
            project.total_follows = follows_counts.get(project.id, 0)
            project.total_spent = expense_sums.get(project.id, Decimal("0.00"))

    def _to_uuid(self, value) -> UUID:
        """转换值为 UUID"""
        if isinstance(value, UUID):
            return value
        if isinstance(value, str):
            return UUID(value)
        if isinstance(value, int):
            # 如果是整数，尝试从数据库查找
            raise ValidationError(
                message="user_id 必须是 UUID 格式", error=ValidationErrorCodes.INVALID_FORMAT
            )
        return UUID(str(value))

    def _user_id_to_int(self, user_id) -> Optional[int]:
        """将 UUID user_id 转换为整数 (用于 account_manager_id 比较)"""
        if isinstance(user_id, int):
            return user_id
        if isinstance(user_id, UUID):
            return abs(user_id.int) % (2**63)
        return None

    # ========================================
    # 项目仪表盘 (TASK-PRJ-004)
    # ========================================

    def get_project_dashboard(
        self,
        project_id: int,
        current_user: User,
        days: int = 30,
    ) -> dict:
        """
        获取项目仪表盘数据

        SoT Reference: API_SOT.md v9.3 §6.8 项目仪表盘

        Args:
            project_id: 项目ID
            current_user: 当前用户
            days: 趋势数据天数 (默认30天)

        Returns:
            dict: 包含 KPI、趋势、账户表现的仪表盘数据

        Raises:
            NotFoundError: 项目不存在
            PermissionError: 无权限访问
        """
        # 1. 获取项目并检查权限
        project = self.get_project(project_id, current_user)

        # 2. 获取项目关联的账户ID列表
        account_ids = [
            acc.id
            for acc in self.db.query(AdAccount.id)
            .filter(AdAccount.project_id == project_id)
            .all()
        ]

        # 3. 计算日期范围
        from datetime import timedelta

        today = date.today()
        start_date = today - timedelta(days=days - 1)

        # 4. 基础 KPI 汇总
        kpi_result = {
            "total_spend": Decimal("0.00"),
            "total_follows": 0,
            "total_conversions": 0,
        }

        if account_ids:
            kpi_query = (
                self.db.query(
                    func.sum(DailyReport.real_spend).label("total_spend"),
                    func.sum(DailyReport.follows_count).label("total_follows"),
                    func.sum(DailyReport.conversions_final).label("total_conversions"),
                )
                .filter(
                    DailyReport.ad_account_id.in_(account_ids),
                    DailyReport.report_date >= start_date,
                    DailyReport.report_date <= today,
                )
                .first()
            )

            if kpi_query:
                kpi_result["total_spend"] = kpi_query.total_spend or Decimal("0.00")
                kpi_result["total_follows"] = kpi_query.total_follows or 0
                kpi_result["total_conversions"] = kpi_query.total_conversions or 0

        # 5. 计算平均 CPL
        avg_cpl = None
        if kpi_result["total_follows"] > 0:
            avg_cpl = kpi_result["total_spend"] / Decimal(kpi_result["total_follows"])

        # 6. 计算预算使用率
        budget_usage_percent = Decimal("0.00")
        if project.budget and project.budget > 0:
            budget_usage_percent = (kpi_result["total_spend"] / project.budget) * 100

        # 7. 每日趋势数据
        daily_trend = []
        if account_ids:
            trend_query = (
                self.db.query(
                    DailyReport.report_date,
                    func.sum(DailyReport.real_spend).label("spend"),
                    func.sum(DailyReport.follows_count).label("follows"),
                    func.sum(DailyReport.conversions_final).label("conversions"),
                )
                .filter(
                    DailyReport.ad_account_id.in_(account_ids),
                    DailyReport.report_date >= start_date,
                    DailyReport.report_date <= today,
                )
                .group_by(DailyReport.report_date)
                .order_by(DailyReport.report_date)
                .all()
            )

            for row in trend_query:
                spend = row.spend or Decimal("0.00")
                follows = row.follows or 0
                cpl = None
                if follows > 0:
                    cpl = spend / Decimal(follows)

                daily_trend.append(
                    {
                        "date": row.report_date.isoformat(),
                        "spend": spend,
                        "follows": follows,
                        "conversions": row.conversions or 0,
                        "cpl": cpl,
                    }
                )

        # 8. 账户表现排行
        account_performance = []
        if account_ids:
            perf_query = (
                self.db.query(
                    AdAccount.id.label("account_id"),
                    AdAccount.name.label("account_name"),
                    AdAccount.platform,
                    AdAccount.status,
                    func.sum(DailyReport.real_spend).label("spend"),
                    func.sum(DailyReport.follows_count).label("follows"),
                    func.sum(DailyReport.conversions_final).label("conversions"),
                )
                .outerjoin(
                    DailyReport,
                    and_(
                        DailyReport.ad_account_id == AdAccount.id,
                        DailyReport.report_date >= start_date,
                        DailyReport.report_date <= today,
                    ),
                )
                .filter(AdAccount.project_id == project_id)
                .group_by(
                    AdAccount.id, AdAccount.name, AdAccount.platform, AdAccount.status
                )
                .order_by(desc(func.sum(DailyReport.real_spend)))
                .all()
            )

            for row in perf_query:
                spend = row.spend or Decimal("0.00")
                follows = row.follows or 0
                cpl = None
                if follows > 0:
                    cpl = spend / Decimal(follows)

                account_performance.append(
                    {
                        "account_id": row.account_id,
                        "account_name": row.account_name,
                        "platform": row.platform,
                        "status": row.status,
                        "spend": spend,
                        "follows": follows,
                        "conversions": row.conversions or 0,
                        "cpl": cpl,
                    }
                )

        return {
            "total_spend": kpi_result["total_spend"],
            "total_follows": kpi_result["total_follows"],
            "total_conversions": kpi_result["total_conversions"],
            "avg_cpl": avg_cpl,
            "budget_usage_percent": budget_usage_percent,
            "daily_trend": daily_trend,
            "account_performance": account_performance,
            "period_start": start_date.isoformat(),
            "period_end": today.isoformat(),
        }


# ========================================
# 缓存支持 (Phase 3 性能优化)
# ========================================


async def get_project_statistics_cached(
    db: Session, current_user: User, ttl: int = 120
) -> dict:
    """
    获取项目统计信息 (带缓存)

    缓存策略:
    - 缓存键: ai_ads:projects:statistics:{user_id}:{role}
    - TTL: 120 秒 (默认)
    - 失效时机: 项目创建/更新/删除

    Args:
        db: 数据库会话
        current_user: 当前用户
        ttl: 缓存过期时间

    Returns:
        项目统计字典
    """
    from backend.core.cache import cache_manager

    # 生成缓存键 (包含用户角色，因为不同角色看到的统计不同)
    cache_key = cache_manager.make_key(
        "projects", "statistics", str(current_user.id), current_user.role
    )

    # 尝试从缓存获取
    cached = await cache_manager.get(cache_key)
    if cached is not None:
        # 反序列化 Decimal
        if "total_budget" in cached:
            cached["total_budget"] = Decimal(str(cached["total_budget"]))
        return cached

    # 缓存未命中，从数据库查询
    service = ProjectService(db)
    stats = service.get_project_statistics(current_user)

    # 序列化 Decimal 为字符串
    cache_data = {k: str(v) if isinstance(v, Decimal) else v for k, v in stats.items()}

    # 写入缓存
    await cache_manager.set(cache_key, cache_data, ttl)

    return stats


async def invalidate_project_cache(
    project_id: Optional[int] = None, user_id: Optional[str] = None
) -> int:
    """
    失效项目相关缓存

    失效时机:
    - 项目创建/更新/删除
    - 项目成员变更
    - 项目费用变更

    Args:
        project_id: 指定项目 ID (可选)
        user_id: 指定用户 ID (可选)

    Returns:
        删除的缓存键数量
    """
    from backend.core.cache import cache_manager

    count = 0

    # 失效项目统计缓存
    if user_id:
        # 失效指定用户的缓存
        pattern = f"ai_ads:projects:statistics:{user_id}:*"
    else:
        # 失效所有用户的项目统计缓存
        pattern = "ai_ads:projects:statistics:*"

    count += await cache_manager.delete_pattern(pattern)

    # 失效项目列表缓存
    if project_id:
        # 单个项目详情缓存
        detail_pattern = f"ai_ads:projects:detail:{project_id}:*"
        count += await cache_manager.delete_pattern(detail_pattern)

    # 失效列表缓存 (所有用户)
    list_pattern = "ai_ads:projects:list:*"
    count += await cache_manager.delete_pattern(list_pattern)

    return count
