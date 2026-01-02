"""
广告账户管理服务
Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, select, desc

from backend.models import (
    AdAccount,
    AccountStatusHistory,
    AccountPerformance,
    AccountAlert,
    AccountDocument,
    AccountNote,
)
from backend.models import Project
from backend.models import Channel
from backend.models import User
from backend.schemas.ad_account import (
    AdAccountCreateRequest,
    AdAccountUpdateRequest,
    AdAccountStatusUpdateRequest,
    AdAccountBudgetUpdateRequest,
    AccountAlertCreateRequest,
    AccountAlertUpdateRequest,
    AccountNoteCreateRequest,
    AccountDocumentCreateRequest,
    AdAccountResponse,
    AdAccountStatisticsResponse,
    AccountAssignRequest,
    AccountAssignResponse,
)
from backend.core.response import success_response, error_response
from backend.exceptions import ValidationError, NotFoundError, PermissionError
from backend.services.audit_log_service import AuditLogService
from backend.core.state_machine import (
    AD_ACCOUNT_STATE_MACHINE,
    StateTransitionError,
    AdAccountStatus as SMAdAccountStatus,
)


class AdAccountService:
    """广告账户管理服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditLogService(db)

    def _validate_transition(
        self,
        account: AdAccount,
        target_status: str,
        user_role: str,
        action_name: str = "状态转换",
    ) -> None:
        """
        验证广告账户状态转换是否合法

        Args:
            account: 广告账户实体
            target_status: 目标状态
            user_role: 当前用户角色
            action_name: 操作名称（用于错误消息）

        Raises:
            ValidationError: 如果状态转换不允许
        """
        current_status = account.status

        # 如果状态没变，跳过验证
        if current_status == target_status:
            return

        # 检查是否可以转换
        if not AD_ACCOUNT_STATE_MACHINE.can_transition(current_status, target_status):
            allowed = AD_ACCOUNT_STATE_MACHINE.get_allowed_transitions(current_status)
            raise ValidationError(
                f"{action_name}失败: 不能从状态 {current_status} 转换到 {target_status}。允许的目标状态: {allowed}"
            )

        # 使用状态机执行转换（包含角色验证）
        try:
            AD_ACCOUNT_STATE_MACHINE.transition(
                account, current_status, target_status, user_role=user_role
            )
        except StateTransitionError as e:
            raise ValidationError(
                f"{action_name}失败: 不能从状态 {current_status} 转换到 {target_status}"
            )

    async def create_account(
        self, request: AdAccountCreateRequest, current_user_id: int
    ) -> AdAccount:
        """创建广告账户"""
        # 验证项目是否存在
        project = (
            self.db.query(Project).filter(Project.id == request.project_id).first()
        )
        if not project:
            raise ValidationError("项目不存在")

        # 验证渠道是否存在
        channel = (
            self.db.query(Channel).filter(Channel.id == request.channel_id).first()
        )
        if not channel:
            raise ValidationError("渠道不存在")

        # 检查平台账户ID是否已存在
        existing = (
            self.db.query(AdAccount)
            .filter(AdAccount.account_code == request.account_id)
            .first()
        )
        if existing:
            raise ValidationError("平台账户ID已存在")

        # 创建账户
        account = AdAccount(
            account_code=request.account_id,
            account_name=request.name,
            project_id=request.project_id,
            channel_id=request.channel_id,
            assigned_to=request.assigned_user_id,
            status="new",
            # 注意：以下字段在模型中不存在，已移除
            # platform=request.platform.value,
            # platform_account_id=request.platform_account_id,
            # platform_business_id=request.platform_business_id,
            # daily_budget=request.daily_budget,
            # total_budget=request.total_budget,
            # remaining_budget=request.total_budget,
            # currency=request.currency,
            # timezone=request.timezone,
            # country=request.country,
            # account_type=request.account_type,
            # payment_method=request.payment_method,
            # billing_information=request.billing_information,
            # auto_monitoring=request.auto_monitoring,
            # alert_thresholds=request.alert_thresholds,
            notes=request.notes,
            # tags=request.tags,
            # metadata=request.metadata,
            # created_by=current_user_id
        )

        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)

        # 创建初始状态历史
        await self._create_status_history(
            account.id, None, "new", "账户创建", "system", current_user_id
        )

        # 记录审计日志
        await self.audit_service.log_action(
            user_id=current_user_id,
            action="create",
            resource_type="ad_account",
            resource_id=account.id,
            details=f"创建广告账户: {account.account_name}",
        )

        return account

    async def get_accounts(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        platform: Optional[str] = None,
        project_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        assigned_user_id: Optional[int] = None,
        current_user_id: int = None,
        user_role: str = None,
    ) -> Tuple[List[AdAccount], int]:
        """获取广告账户列表"""
        query = self.db.query(AdAccount)

        # 根据角色过滤数据
        if user_role == "pitcher":
            query = query.filter(AdAccount.assigned_to == current_user_id)
        elif user_role == "account_manager":
            # 账户管理员只能看到自己项目的账户
            query = query.join(Project).filter(
                Project.account_manager_id == current_user_id
            )

        # 应用过滤条件
        if status:
            query = query.filter(AdAccount.status == status)
        # 注意：platform 字段在模型中不存在，已移除过滤
        # if platform:
        #     query = query.filter(AdAccount.platform == platform)
        if project_id:
            query = query.filter(AdAccount.project_id == project_id)
        if channel_id:
            query = query.filter(AdAccount.channel_id == channel_id)
        if assigned_user_id:
            query = query.filter(AdAccount.assigned_to == assigned_user_id)

        # 计算总数
        total = query.count()

        # 分页
        accounts = (
            query.order_by(AdAccount.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return accounts, total

    async def get_account_by_id(
        self, account_id: int, current_user_id: int = None, user_role: str = None
    ) -> AdAccount:
        """获取广告账户详情"""
        query = self.db.query(AdAccount).filter(AdAccount.id == account_id)
        account = query.first()

        if not account:
            raise NotFoundError("广告账户不存在")

        # 权限检查
        if user_role == "pitcher" and account.assigned_to != current_user_id:
            raise PermissionError("无权限访问此账户")
        elif user_role == "account_manager":
            # 检查是否是账户管理员的项目
            project = (
                self.db.query(Project).filter(Project.id == account.project_id).first()
            )
            if not project or project.account_manager_id != current_user_id:
                raise PermissionError("无权限访问此账户")

        return account

    async def update_account(
        self, account_id: int, request: AdAccountUpdateRequest, current_user_id: int
    ) -> AdAccount:
        """更新广告账户"""
        account = await self.get_account_by_id(account_id, current_user_id)

        # 记录变更前的值
        old_values = {}
        update_data = request.dict(exclude_unset=True)

        # 字段名映射：schema 字段 -> 模型字段
        field_mapping = {"name": "account_name", "assigned_user_id": "assigned_to"}

        for field, value in update_data.items():
            # 映射字段名
            model_field = field_mapping.get(field, field)
            if hasattr(account, model_field):
                old_value = getattr(account, model_field)
                if old_value != value:
                    old_values[field] = old_value
                    setattr(account, model_field, value)

        self.db.commit()

        # 记录审计日志
        if old_values:
            await self.audit_service.log_action(
                user_id=current_user_id,
                action="update",
                resource_type="ad_account",
                resource_id=account_id,
                details=f"更新账户信息: {', '.join(old_values.keys())}",
            )

        return account

    async def update_account_status(
        self,
        account_id: int,
        request: AdAccountStatusUpdateRequest,
        current_user_id: int,
        user_role: str = "account_manager",
    ) -> AdAccount:
        """
        更新账户状态
        状态转换规则由 AD_ACCOUNT_STATE_MACHINE 定义 (STATE_MACHINE.md v2.6 §7.1)
        """
        account = await self.get_account_by_id(account_id, current_user_id)
        old_status = account.status

        # 使用统一状态机验证并执行转换
        self._validate_transition(account, request.status, user_role, "账户状态更新")

        # 更新附加信息
        account.status_reason = request.status_reason
        account.last_status_change = datetime.utcnow()

        # 更新生命周期时间
        now = datetime.utcnow()
        if request.status == "active" and not account.activated_date:
            account.activated_date = now
        elif request.status == "suspended" and not account.suspended_date:
            account.suspended_date = now
        elif request.status == "dead" and not account.dead_date:
            account.dead_date = now
        elif request.status == "archived" and not account.archived_date:
            account.archived_date = now

        self.db.commit()

        # 创建状态历史记录
        await self._create_status_history(
            account_id,
            old_status,
            request.status,
            request.status_reason or request.notes,
            request.change_source,
            current_user_id,
        )

        # 记录审计日志
        await self.audit_service.log_action(
            user_id=current_user_id,
            action="update_status",
            resource_type="ad_account",
            resource_id=account_id,
            details=f"状态变更: {old_status} -> {request.status}",
        )

        return account

    async def update_account_budget(
        self,
        account_id: int,
        request: AdAccountBudgetUpdateRequest,
        current_user_id: int,
    ) -> AdAccount:
        """更新账户预算"""
        account = await self.get_account_by_id(account_id, current_user_id)

        # 记录变更前
        old_daily_budget = account.daily_budget
        old_total_budget = account.total_budget

        # 更新预算
        if request.daily_budget is not None:
            account.daily_budget = request.daily_budget
        if request.total_budget is not None:
            account.total_budget = request.total_budget

        self.db.commit()

        # 记录审计日志
        await self.audit_service.log_action(
            user_id=current_user_id,
            action="update_budget",
            resource_type="ad_account",
            resource_id=account_id,
            details=f"预算调整: {request.reason}",
        )

        return account

    async def get_account_statistics(
        self,
        project_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        platform: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        current_user_id: int = None,
        user_role: str = None,
    ) -> AdAccountStatisticsResponse:
        """获取账户统计数据"""
        query = self.db.query(AdAccount)

        # 根据角色过滤
        if user_role == "pitcher":
            query = query.filter(AdAccount.assigned_to == current_user_id)
        elif user_role == "account_manager":
            query = query.join(Project).filter(
                Project.account_manager_id == current_user_id
            )

        # 应用过滤条件
        if project_id:
            query = query.filter(AdAccount.project_id == project_id)
        if channel_id:
            query = query.filter(AdAccount.channel_id == channel_id)
        # 注意：platform 字段在模型中不存在，已移除过滤
        # if platform:
        #     query = query.filter(AdAccount.platform == platform)

        # 总体统计
        total_accounts = query.count()
        active_accounts = query.filter(AdAccount.status == "active").count()
        suspended_accounts = query.filter(AdAccount.status == "suspended").count()
        dead_accounts = query.filter(AdAccount.status == "dead").count()
        new_accounts = query.filter(AdAccount.status == "new").count()

        # 性能统计 - 注意：这些字段在模型中不存在，需要从 AccountPerformance 获取
        # 暂时返回默认值，后续需要从 AccountPerformance 表聚合
        total_spend = Decimal("0")
        total_leads = 0
        avg_cpl = Decimal("0")
        best_cpl = Decimal("0")
        total_budget = Decimal("0")
        total_daily_budget = Decimal("0")

        # 预算使用率
        budget_utilization = 0.0

        # 平台分布 - 注意：platform 字段在模型中不存在，需要从 Channel 获取
        # 暂时返回空列表
        platform_distribution = []

        # 状态分布
        status_dist = (
            query.with_entities(AdAccount.status, func.count().label("count"))
            .group_by(AdAccount.status)
            .all()
        )

        status_distribution = [{"status": s[0], "count": s[1]} for s in status_dist]

        # TOP表现账户 - 注意：这些字段在模型中不存在，暂时返回空列表
        # 后续需要从 AccountPerformance 表聚合
        top_performers = []
        low_performers = []

        # 预警统计
        alerts_query = self.db.query(AccountAlert)
        if user_role == "pitcher":
            alerts_query = alerts_query.join(AdAccount).filter(
                AdAccount.assigned_to == current_user_id
            )
        elif user_role == "account_manager":
            alerts_query = (
                alerts_query.join(AdAccount)
                .join(Project)
                .filter(Project.account_manager_id == current_user_id)
            )

        active_alerts = alerts_query.filter(AccountAlert.status == "active").count()
        critical_alerts = alerts_query.filter(
            AccountAlert.status == "active", AccountAlert.severity == "critical"
        ).count()

        return AdAccountStatisticsResponse(
            total_accounts=total_accounts,
            active_accounts=active_accounts,
            suspended_accounts=suspended_accounts,
            dead_accounts=dead_accounts,
            new_accounts=new_accounts,
            total_spend=total_spend,
            total_leads=total_leads,
            avg_cpl=avg_cpl,
            best_cpl=best_cpl,
            total_budget=total_budget,
            total_daily_budget=total_daily_budget,
            budget_utilization=budget_utilization,
            platform_distribution=platform_distribution,
            status_distribution=status_distribution,
            top_performers=[
                {
                    "id": a.id,
                    "name": a.account_name,
                    # "platform": a.platform,  # 字段不存在，已移除
                    # "total_leads": a.total_leads,  # 字段不存在，已移除
                    # "avg_cpl": a.avg_cpl  # 字段不存在，已移除
                }
                for a in top_performers
            ],
            low_performers=[
                {
                    "id": a.id,
                    "name": a.account_name,
                    # "platform": a.platform,  # 字段不存在，已移除
                    # "avg_cpl": a.avg_cpl  # 字段不存在，已移除
                }
                for a in low_performers
            ],
            active_alerts=active_alerts,
            critical_alerts=critical_alerts,
        )

    async def get_account_alerts(
        self,
        account_id: int,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        current_user_id: int = None,
        user_role: str = None,
    ) -> List[AccountAlert]:
        """获取账户预警列表"""
        # 权限检查
        await self.get_account_by_id(account_id, current_user_id, user_role)

        query = self.db.query(AccountAlert).filter(
            AccountAlert.ad_account_id == account_id
        )

        if status:
            query = query.filter(AccountAlert.status == status)
        if severity:
            query = query.filter(AccountAlert.severity == severity)

        return query.order_by(AccountAlert.created_at.desc()).all()

    async def create_account_alert(
        self, account_id: int, request: AccountAlertCreateRequest, current_user_id: int
    ) -> AccountAlert:
        """创建账户预警"""
        # 权限检查
        await self.get_account_by_id(account_id, current_user_id)

        alert = AccountAlert(
            ad_account_id=account_id,
            alert_type=request.alert_type.value,
            severity=request.severity.value,
            status="open",  # 新建预警默认为 open 状态
            message=request.message,
            alert_metadata={
                "title": request.title,
                "trigger_condition": request.trigger_condition,
                "notify_users": request.notify_users,
            },
        )

        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        # 记录审计日志
        await self.audit_service.log_action(
            user_id=current_user_id,
            action="create",
            resource_type="account_alert",
            resource_id=alert.id,
            details=f"创建账户预警: {request.title}",
        )

        return alert

    async def update_account_alert(
        self, alert_id: int, request: AccountAlertUpdateRequest, current_user_id: int
    ) -> AccountAlert:
        """更新账户预警"""
        alert = self.db.query(AccountAlert).filter(AccountAlert.id == alert_id).first()

        if not alert:
            raise NotFoundError("预警不存在")

        # 权限检查
        await self.get_account_by_id(alert.account_id, current_user_id)

        # 更新预警
        alert.status = request.status
        if request.status == "acknowledged":
            alert.acknowledged_by = current_user_id
            alert.acknowledged_at = datetime.utcnow()
        elif request.status == "resolved":
            alert.resolved_by = current_user_id
            alert.resolved_at = datetime.utcnow()
            alert.resolution = request.resolution

        self.db.commit()

        # 记录审计日志
        await self.audit_service.log_action(
            user_id=current_user_id,
            action="update",
            resource_type="account_alert",
            resource_id=alert_id,
            details=f"更新预警状态: {request.status}",
        )

        return alert

    async def get_account_notes(
        self,
        account_id: int,
        note_type: Optional[str] = None,
        is_resolved: Optional[bool] = None,
        current_user_id: int = None,
        user_role: str = None,
    ) -> List[AccountNote]:
        """获取账户备注列表"""
        # 权限检查
        await self.get_account_by_id(account_id, current_user_id, user_role)

        query = self.db.query(AccountNote).filter(
            AccountNote.ad_account_id == account_id
        )

        if note_type:
            query = query.filter(AccountNote.note_type == note_type)
        if is_resolved is not None:
            query = query.filter(AccountNote.is_resolved == is_resolved)

        return query.order_by(
            AccountNote.priority.desc(), AccountNote.created_at.desc()
        ).all()

    async def create_account_note(
        self, account_id: int, request: AccountNoteCreateRequest, current_user_id: int
    ) -> AccountNote:
        """创建账户备注"""
        # 权限检查
        await self.get_account_by_id(account_id, current_user_id)

        note = AccountNote(
            ad_account_id=account_id,
            title=request.title,
            content=request.content,
            note_type=request.note_type.value,
            priority=request.priority,
            created_by=current_user_id,
        )

        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)

        # 记录审计日志
        await self.audit_service.log_action(
            user_id=current_user_id,
            action="create",
            resource_type="account_note",
            resource_id=note.id,
            details=f"创建账户备注: {request.title}",
        )

        return note

    async def delete_account(self, account_id: int, current_user_id: int) -> bool:
        """删除广告账户（软删除）"""
        account = await self.get_account_by_id(account_id, current_user_id)

        # 检查是否可以删除（只有archived状态可以删除）
        if account.status != "archived":
            raise ValidationError("只有归档状态的账户才能删除")

        # 软删除
        account.status = "deleted"
        account.notes = f"已删除 - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"

        self.db.commit()

        # 记录审计日志
        await self.audit_service.log_action(
            user_id=current_user_id,
            action="delete",
            resource_type="ad_account",
            resource_id=account_id,
            details=f"删除广告账户: {account.account_name}",
        )

        return True

    async def assign_account(
        self,
        account_id: int,
        request: AccountAssignRequest,
        current_user_id: str,
        user_role: str,
    ) -> AccountAssignResponse:
        """
        分配广告账户给投手

        TASK-ACC-002: 账户分配 API

        SoT Ref:
        - BR-ACCT-002: 账户分配唯一性（每账户仅一个负责人）
        - BR-ACCT-005: 分配记录审计
        - API_SOT.md v9.7 §8: POST /api/v1/ad-accounts/{account_id}/assign
        - AUTH_SPEC.md v2.0 §5.3.1: 仅 admin/account_manager 可执行

        Args:
            account_id: 广告账户 ID
            request: 分配请求（pitcher_id, reason）
            current_user_id: 操作人 ID (UUID string)
            user_role: 操作人角色

        Returns:
            AccountAssignResponse: 分配结果

        Raises:
            NotFoundError: 账户不存在 (BIZ_002)
            ValidationError: 目标用户非投手 (BIZ_001)
            PermissionError: 无分配权限 (AUTH_500)
        """
        from uuid import UUID

        # 1. 权限检查：仅 admin/account_manager 可执行分配
        if user_role not in ["admin", "account_manager"]:
            raise PermissionError("仅管理员和户管可执行账户分配")

        # 2. 查询广告账户
        account = self.db.query(AdAccount).filter(AdAccount.id == account_id).first()
        if not account:
            raise NotFoundError(f"广告账户 {account_id} 不存在")

        # 3. 查询目标投手
        target_user = self.db.query(User).filter(User.id == request.pitcher_id).first()
        if not target_user:
            raise NotFoundError(f"用户 {request.pitcher_id} 不存在")

        # 4. 验证目标用户角色：必须是 media_buyer（技术角色，对应业务角色 pitcher）
        # BR-ACCT-002: 账户分配唯一性 - 仅可分配给投手
        if target_user.role not in ["media_buyer", "pitcher"]:
            raise ValidationError(f"目标用户必须是投手角色，当前角色: {target_user.role}")

        # 5. 记录原负责人信息（用于审计和响应）
        previous_owner_id = account.owner_id
        previous_owner_name = None
        if previous_owner_id:
            previous_owner = (
                self.db.query(User).filter(User.id == previous_owner_id).first()
            )
            if previous_owner:
                previous_owner_name = (
                    previous_owner.full_name or previous_owner.username
                )

        # 6. 执行分配：更新 owner_id 字段
        account.owner_id = request.pitcher_id
        assigned_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(account)

        # 7. 记录审计日志 (BR-ACCT-005)
        await self.audit_service.log_action(
            user_id=current_user_id,
            action="assign_account",
            resource_type="ad_account",
            resource_id=account_id,
            details=(
                f"账户分配: {account.account_name} | "
                f"原负责人: {previous_owner_name or '无'} → "
                f"新负责人: {target_user.full_name or target_user.username} | "
                f"原因: {request.reason or '未填写'}"
            ),
        )

        # 8. 构建响应
        return AccountAssignResponse(
            account_id=account_id,
            account_name=account.account_name,
            previous_owner_id=previous_owner_id,
            previous_owner_name=previous_owner_name,
            new_owner_id=request.pitcher_id,
            new_owner_name=target_user.full_name or target_user.username,
            assigned_at=assigned_at,
            assigned_by=UUID(current_user_id)
            if isinstance(current_user_id, str)
            else current_user_id,
        )

    async def transfer_account(
        self,
        account_id: int,
        request: "AccountTransferRequest",
        current_user_id: str,
        current_user_name: str,
        user_role: str,
    ) -> "AccountTransferResponse":
        """
        转移广告账户到另一个投手

        TASK-ACC-003: 账户转移 API

        与 assign_account 的区别：
        - 转移要求账户已有负责人（owner_id 不能为 None）
        - 必须填写转移原因（用于审计）
        - action 为 "transfer" 而非 "assign"

        SoT Ref:
        - BR-ACCT-002: 账户分配唯一性（每账户仅一个负责人）
        - BR-ACCT-005: 分配记录审计
        - API_SOT.md v9.7 §8: POST /api/v1/ad-accounts/{account_id}/transfer
        - AUTH_SPEC.md v2.0 §5.3.1: 仅 admin/account_manager 可执行

        Args:
            account_id: 广告账户 ID
            request: 转移请求（target_pitcher_id, reason, notes）
            current_user_id: 操作人 ID (UUID string)
            current_user_name: 操作人名称
            user_role: 操作人角色

        Returns:
            AccountTransferResponse: 转移结果

        Raises:
            NotFoundError: 账户不存在 (BIZ_002)
            ValidationError: 业务规则校验失败 (BIZ_001)
            PermissionError: 无转移权限 (AUTH_500)
        """
        from uuid import UUID
        from backend.schemas.ad_account import AccountTransferResponse

        # 1. 权限检查：仅 admin/account_manager 可执行转移
        if user_role not in ["admin", "account_manager"]:
            raise PermissionError("仅管理员和户管可执行账户转移")

        # 2. 查询广告账户
        account = self.db.query(AdAccount).filter(AdAccount.id == account_id).first()
        if not account:
            raise NotFoundError(f"广告账户 {account_id} 不存在")

        # 3. 检查账户是否有当前负责人（转移前提）
        if not account.owner_id:
            raise ValidationError("账户尚未分配负责人，请使用分配（assign）接口而非转移（transfer）")

        # 4. 检查目标投手是否与当前负责人相同
        if account.owner_id == request.target_pitcher_id:
            raise ValidationError("目标投手与当前负责人相同，无需转移")

        # 5. 查询原负责人信息
        previous_owner = self.db.query(User).filter(User.id == account.owner_id).first()
        if not previous_owner:
            raise ValidationError("当前负责人用户不存在，数据异常")

        previous_owner_name = previous_owner.full_name or previous_owner.username

        # 6. 查询目标投手
        target_user = (
            self.db.query(User).filter(User.id == request.target_pitcher_id).first()
        )
        if not target_user:
            raise NotFoundError(f"目标投手 {request.target_pitcher_id} 不存在")

        # 7. 验证目标用户角色：必须是 media_buyer（技术角色，对应业务角色 pitcher）
        # BR-ACCT-002: 账户分配唯一性 - 仅可分配给投手
        if target_user.role not in ["media_buyer", "pitcher"]:
            raise ValidationError(f"目标用户必须是投手角色，当前角色: {target_user.role}")

        # 8. 执行转移：更新 owner_id 字段
        previous_owner_id = account.owner_id
        account.owner_id = request.target_pitcher_id
        transferred_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(account)

        # 9. 记录审计日志 (BR-ACCT-005)
        # 审计日志格式符合 BR-ACCT-005 定义
        audit_log_id = await self.audit_service.log_action(
            user_id=current_user_id,
            action="transfer",  # 使用 "transfer" 区分于 "assign"
            resource_type="ad_account",
            resource_id=account_id,
            details=(
                f"账户转移: {account.account_name} ({account.account_code}) | "
                f"原负责人: {previous_owner_name} → "
                f"新负责人: {target_user.full_name or target_user.username} | "
                f"原因: {request.reason}"
            ),
            old_value={"owner_id": str(previous_owner_id)},
            new_value={
                "owner_id": str(request.target_pitcher_id),
                "reason": request.reason,
                "notes": request.notes,
            },
        )

        # 10. 构建响应
        return AccountTransferResponse(
            account_id=account_id,
            account_name=account.account_name,
            account_code=account.account_code,
            previous_pitcher_id=previous_owner_id,
            previous_pitcher_name=previous_owner_name,
            new_pitcher_id=request.target_pitcher_id,
            new_pitcher_name=target_user.full_name or target_user.username,
            transferred_at=transferred_at,
            transferred_by=UUID(current_user_id)
            if isinstance(current_user_id, str)
            else current_user_id,
            transferred_by_name=current_user_name,
            reason=request.reason,
            audit_log_id=audit_log_id,
        )

    async def mark_dead(
        self,
        account_id: int,
        request: "MarkDeadRequest",
        current_user_id: Union[int, str, UUID],
        user_role: str,
    ) -> "MarkDeadResponse":
        """
        标记账户为死号 - TASK-ACC-004

        将广告账户标记为死号状态。死号只能进行余额迁移，不能再进行日报、充值等操作。

        SoT References:
        - STATE_MACHINE.md v2.9 §7.1: 账户状态机 (dead 为终态之一)
        - BR-ACCT-006: 停用账户禁止操作（死号仅允许余额迁移）
        - API_SOT.md v9.0 §8: POST /api/v1/ad-accounts/{account_id}/mark-dead

        业务规则:
        1. 只能从非终态 (new, testing, active, suspended) 转换到 dead
        2. 已经是 dead 或 archived 的账户不能再次标记
        3. 必须记录状态历史和审计日志
        4. 死号后只能进行余额迁移操作

        Args:
            account_id: 广告账户ID
            request: 标记死号请求
            current_user_id: 当前用户ID
            user_role: 用户角色 (必须是 admin 或 account_manager)

        Returns:
            MarkDeadResponse: 标记死号响应

        Raises:
            HTTPException 400: 业务规则违反
            HTTPException 403: 权限不足
            HTTPException 404: 账户不存在
        """
        from backend.schemas.ad_account import MarkDeadRequest, MarkDeadResponse

        # 1. 权限检查：只有 admin 和 account_manager 可以标记死号
        allowed_roles = ["admin", "account_manager"]
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail={
                    "success": False,
                    "error_code": "AUTH_500",
                    "message": f"角色 '{user_role}' 无权标记死号，需要 {allowed_roles} 权限",
                },
            )

        # 2. 查询账户
        account = self.db.query(AdAccount).filter(AdAccount.id == account_id).first()
        if not account:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error_code": "ACCT_404",
                    "message": f"账户 {account_id} 不存在",
                },
            )

        # 3. 状态检查：不能从终态转换
        terminal_statuses = ["dead", "archived"]
        if account.status in terminal_statuses:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error_code": "STATE_400",
                    "message": f"账户已是 '{account.status}' 状态，不能重复标记死号",
                },
            )

        # 4. 保存旧状态
        old_status = account.status
        marked_at = datetime.utcnow()

        # 5. 获取操作者信息
        user_id_int = (
            int(current_user_id)
            if isinstance(current_user_id, str)
            else current_user_id.int
            if isinstance(current_user_id, UUID)
            else current_user_id
        )
        current_user = self.db.query(User).filter(User.id == user_id_int).first()
        current_user_name = (
            current_user.full_name or current_user.username
            if current_user
            else "Unknown"
        )

        # 6. 获取项目信息
        project = (
            self.db.query(Project).filter(Project.id == account.project_id).first()
            if account.project_id
            else None
        )
        project_name = project.project_name if project else None

        # 7. 计算账户余额（如果有 remaining_budget 字段）
        final_balance = getattr(account, "remaining_budget", None)
        needs_balance_transfer = final_balance is not None and final_balance > 0

        # 8. 更新账户状态
        account.status = "dead"
        account.status_reason = request.reason
        account.last_status_change = marked_at
        account.dead_date = marked_at

        # 9. 创建状态历史记录
        await self._create_status_history(
            account_id=account_id,
            old_status=old_status,
            new_status="dead",
            reason=request.reason,
            source="mark_dead_api",
            user_id=user_id_int,
        )

        # 10. 提交数据库更改
        self.db.commit()
        self.db.refresh(account)

        # 11. 记录审计日志
        audit_log_id = await self.audit_service.log_action(
            user_id=user_id_int,
            action="mark_dead",
            resource_type="ad_account",
            resource_id=account_id,
            details=(
                f"账户标记死号: {account.account_name} ({account.account_code}) | "
                f"原状态: {old_status} → dead | "
                f"原因: {request.reason}"
            ),
            old_value={"status": old_status},
            new_value={
                "status": "dead",
                "reason": request.reason,
                "notes": request.notes,
                "marked_at": marked_at.isoformat(),
            },
        )

        # 12. 构建响应
        balance_transfer_url = (
            f"/api/v1/ad-accounts/{account_id}/balance-transfer"
            if needs_balance_transfer
            else None
        )

        return MarkDeadResponse(
            account_id=account_id,
            account_name=account.account_name,
            account_code=account.account_code,
            platform=account.platform,
            project_id=account.project_id,
            project_name=project_name,
            previous_status=old_status,
            new_status="dead",
            marked_at=marked_at,
            marked_by=UUID(str(current_user_id))
            if not isinstance(current_user_id, UUID)
            else current_user_id,
            marked_by_name=current_user_name,
            reason=request.reason,
            final_balance=final_balance,
            total_spend=account.total_spend or Decimal("0"),
            total_leads=account.total_leads or 0,
            needs_balance_transfer=needs_balance_transfer,
            balance_transfer_url=balance_transfer_url,
            audit_log_id=audit_log_id,
        )

    async def _create_status_history(
        self,
        account_id: int,
        old_status: Optional[str],
        new_status: str,
        reason: str,
        source: str,
        user_id: int,
    ):
        """创建状态历史记录"""
        history = AccountStatusHistory(
            ad_account_id=account_id,
            old_status=old_status,
            new_status=new_status,
            reason=f"{reason} (source: {source})",  # 合并 reason 和 source
            changed_by=user_id,
        )

        self.db.add(history)
        self.db.commit()


# ========================================
# 缓存支持 (Phase 3 性能优化)
# ========================================


async def get_account_statistics_cached(
    db: Session,
    project_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    current_user_id: int = None,
    user_role: str = None,
    ttl: int = 120,
) -> AdAccountStatisticsResponse:
    """
    获取账户统计 (带缓存)

    缓存策略:
    - 缓存键: ai_ads:accounts:statistics:{user_id}:{role}:{project_id}:{channel_id}
    - TTL: 120 秒 (默认)
    - 失效时机: 账户创建/更新/删除

    Args:
        db: 数据库会话
        project_id: 项目 ID 筛选
        channel_id: 渠道 ID 筛选
        current_user_id: 当前用户 ID
        user_role: 用户角色
        ttl: 缓存过期时间

    Returns:
        账户统计响应
    """
    from backend.core.cache import cache_manager

    # 生成缓存键
    cache_key = cache_manager.make_key(
        "accounts",
        "statistics",
        str(current_user_id or "all"),
        user_role or "any",
        str(project_id or "all"),
        str(channel_id or "all"),
    )

    # 尝试从缓存获取
    cached = await cache_manager.get(cache_key)
    if cached is not None:
        # 反序列化 Decimal 字段
        for field in [
            "total_spend",
            "avg_cpl",
            "best_cpl",
            "total_budget",
            "total_daily_budget",
        ]:
            if field in cached and cached[field] is not None:
                cached[field] = Decimal(str(cached[field]))
        return AdAccountStatisticsResponse(**cached)

    # 缓存未命中，从数据库查询
    service = AdAccountService(db)
    stats = await service.get_account_statistics(
        project_id=project_id,
        channel_id=channel_id,
        current_user_id=current_user_id,
        user_role=user_role,
    )

    # 序列化为可缓存格式
    cache_data = stats.model_dump()
    for field in [
        "total_spend",
        "avg_cpl",
        "best_cpl",
        "total_budget",
        "total_daily_budget",
    ]:
        if field in cache_data and cache_data[field] is not None:
            cache_data[field] = str(cache_data[field])

    # 写入缓存
    await cache_manager.set(cache_key, cache_data, ttl)

    return stats


async def invalidate_account_cache(
    account_id: Optional[int] = None,
    project_id: Optional[int] = None,
    user_id: Optional[str] = None,
) -> int:
    """
    失效广告账户相关缓存

    失效时机:
    - 账户创建/更新/删除
    - 账户状态变更
    - 账户预算调整

    Args:
        account_id: 指定账户 ID (可选)
        project_id: 指定项目 ID (可选)
        user_id: 指定用户 ID (可选)

    Returns:
        删除的缓存键数量
    """
    from backend.core.cache import cache_manager

    count = 0

    # 失效账户统计缓存
    if user_id:
        pattern = f"ai_ads:accounts:statistics:{user_id}:*"
    else:
        pattern = "ai_ads:accounts:statistics:*"
    count += await cache_manager.delete_pattern(pattern)

    # 失效账户列表缓存
    if project_id:
        pattern = f"ai_ads:accounts:list:*:{project_id}:*"
    else:
        pattern = "ai_ads:accounts:list:*"
    count += await cache_manager.delete_pattern(pattern)

    # 失效单个账户详情缓存
    if account_id:
        pattern = f"ai_ads:accounts:detail:{account_id}:*"
        count += await cache_manager.delete_pattern(pattern)

    # 同时失效 Dashboard 缓存 (账户数据变更影响 Dashboard)
    await cache_manager.invalidate_dashboard()

    return count
