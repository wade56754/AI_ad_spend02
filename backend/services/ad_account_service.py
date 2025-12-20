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
    AdAccount, AccountStatusHistory, AccountPerformance,
    AccountAlert, AccountDocument, AccountNote
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
    AdAccountStatisticsResponse
)
from backend.core.response import success_response, error_response
from backend.exceptions import ValidationError, NotFoundError, PermissionError
from backend.services.audit_log_service import AuditLogService
from backend.core.state_machine import (
    AD_ACCOUNT_STATE_MACHINE,
    StateTransitionError,
    AdAccountStatus as SMAdAccountStatus
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
        action_name: str = "状态转换"
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
        self,
        request: AdAccountCreateRequest,
        current_user_id: int
    ) -> AdAccount:
        """创建广告账户"""
        # 验证项目是否存在
        project = self.db.query(Project).filter(Project.id == request.project_id).first()
        if not project:
            raise ValidationError("项目不存在")

        # 验证渠道是否存在
        channel = self.db.query(Channel).filter(Channel.id == request.channel_id).first()
        if not channel:
            raise ValidationError("渠道不存在")

        # 检查平台账户ID是否已存在
        existing = self.db.query(AdAccount).filter(
            AdAccount.account_code == request.account_id
        ).first()
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
            account.id,
            None,
            "new",
            "账户创建",
            "system",
            current_user_id
        )

        # 记录审计日志
        await self.audit_service.log_action(
            user_id=current_user_id,
            action="create",
            resource_type="ad_account",
            resource_id=account.id,
            details=f"创建广告账户: {account.account_name}"
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
        user_role: str = None
    ) -> Tuple[List[AdAccount], int]:
        """获取广告账户列表"""
        query = self.db.query(AdAccount)

        # 根据角色过滤数据
        if user_role == "media_buyer":
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
        accounts = query.order_by(
            AdAccount.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return accounts, total

    async def get_account_by_id(
        self,
        account_id: int,
        current_user_id: int = None,
        user_role: str = None
    ) -> AdAccount:
        """获取广告账户详情"""
        query = self.db.query(AdAccount).filter(AdAccount.id == account_id)
        account = query.first()

        if not account:
            raise NotFoundError("广告账户不存在")

        # 权限检查
        if user_role == "media_buyer" and account.assigned_to != current_user_id:
            raise PermissionError("无权限访问此账户")
        elif user_role == "account_manager":
            # 检查是否是账户管理员的项目
            project = self.db.query(Project).filter(Project.id == account.project_id).first()
            if not project or project.account_manager_id != current_user_id:
                raise PermissionError("无权限访问此账户")

        return account

    async def update_account(
        self,
        account_id: int,
        request: AdAccountUpdateRequest,
        current_user_id: int
    ) -> AdAccount:
        """更新广告账户"""
        account = await self.get_account_by_id(account_id, current_user_id)

        # 记录变更前的值
        old_values = {}
        update_data = request.dict(exclude_unset=True)
        
        # 字段名映射：schema 字段 -> 模型字段
        field_mapping = {
            'name': 'account_name',
            'assigned_user_id': 'assigned_to'
        }
        
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
                details=f"更新账户信息: {', '.join(old_values.keys())}"
            )

        return account

    async def update_account_status(
        self,
        account_id: int,
        request: AdAccountStatusUpdateRequest,
        current_user_id: int,
        user_role: str = "account_manager"
    ) -> AdAccount:
        """
        更新账户状态
        状态转换规则由 AD_ACCOUNT_STATE_MACHINE 定义 (STATE_MACHINE.md v2.6 §7.1)
        """
        account = await self.get_account_by_id(account_id, current_user_id)
        old_status = account.status

        # 使用统一状态机验证并执行转换
        self._validate_transition(
            account,
            request.status,
            user_role,
            "账户状态更新"
        )

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
            current_user_id
        )

        # 记录审计日志
        await self.audit_service.log_action(
            user_id=current_user_id,
            action="update_status",
            resource_type="ad_account",
            resource_id=account_id,
            details=f"状态变更: {old_status} -> {request.status}"
        )

        return account

    async def update_account_budget(
        self,
        account_id: int,
        request: AdAccountBudgetUpdateRequest,
        current_user_id: int
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
            details=f"预算调整: {request.reason}"
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
        user_role: str = None
    ) -> AdAccountStatisticsResponse:
        """获取账户统计数据"""
        query = self.db.query(AdAccount)

        # 根据角色过滤
        if user_role == "media_buyer":
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
        total_spend = Decimal('0')
        total_leads = 0
        avg_cpl = Decimal('0')
        best_cpl = Decimal('0')
        total_budget = Decimal('0')
        total_daily_budget = Decimal('0')

        # 预算使用率
        budget_utilization = 0.0

        # 平台分布 - 注意：platform 字段在模型中不存在，需要从 Channel 获取
        # 暂时返回空列表
        platform_distribution = []

        # 状态分布
        status_dist = query.with_entities(
            AdAccount.status,
            func.count().label('count')
        ).group_by(AdAccount.status).all()

        status_distribution = [
            {"status": s[0], "count": s[1]}
            for s in status_dist
        ]

        # TOP表现账户 - 注意：这些字段在模型中不存在，暂时返回空列表
        # 后续需要从 AccountPerformance 表聚合
        top_performers = []
        low_performers = []

        # 预警统计
        alerts_query = self.db.query(AccountAlert)
        if user_role == "media_buyer":
            alerts_query = alerts_query.join(AdAccount).filter(
                AdAccount.assigned_to == current_user_id
            )
        elif user_role == "account_manager":
            alerts_query = alerts_query.join(AdAccount).join(Project).filter(
                Project.account_manager_id == current_user_id
            )

        active_alerts = alerts_query.filter(
            AccountAlert.status == "active"
        ).count()
        critical_alerts = alerts_query.filter(
            AccountAlert.status == "active",
            AccountAlert.severity == "critical"
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
            critical_alerts=critical_alerts
        )

    async def get_account_alerts(
        self,
        account_id: int,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        current_user_id: int = None,
        user_role: str = None
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

        return query.order_by(
            AccountAlert.created_at.desc()
        ).all()

    async def create_account_alert(
        self,
        account_id: int,
        request: AccountAlertCreateRequest,
        current_user_id: int
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
                "notify_users": request.notify_users
            }
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
            details=f"创建账户预警: {request.title}"
        )

        return alert

    async def update_account_alert(
        self,
        alert_id: int,
        request: AccountAlertUpdateRequest,
        current_user_id: int
    ) -> AccountAlert:
        """更新账户预警"""
        alert = self.db.query(AccountAlert).filter(
            AccountAlert.id == alert_id
        ).first()

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
            details=f"更新预警状态: {request.status}"
        )

        return alert

    async def get_account_notes(
        self,
        account_id: int,
        note_type: Optional[str] = None,
        is_resolved: Optional[bool] = None,
        current_user_id: int = None,
        user_role: str = None
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
            AccountNote.priority.desc(),
            AccountNote.created_at.desc()
        ).all()

    async def create_account_note(
        self,
        account_id: int,
        request: AccountNoteCreateRequest,
        current_user_id: int
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
            created_by=current_user_id
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
            details=f"创建账户备注: {request.title}"
        )

        return note

    async def delete_account(
        self,
        account_id: int,
        current_user_id: int
    ) -> bool:
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
            details=f"删除广告账户: {account.account_name}"
        )

        return True

    async def _create_status_history(
        self,
        account_id: int,
        old_status: Optional[str],
        new_status: str,
        reason: str,
        source: str,
        user_id: int
    ):
        """创建状态历史记录"""
        history = AccountStatusHistory(
            ad_account_id=account_id,
            old_status=old_status,
            new_status=new_status,
            reason=f"{reason} (source: {source})",  # 合并 reason 和 source
            changed_by=user_id
        )

        self.db.add(history)
        self.db.commit()