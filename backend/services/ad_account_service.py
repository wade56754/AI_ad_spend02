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

from models.ad_account import (
    AdAccount, AccountStatusHistory, AccountPerformance,
    AccountAlert, AccountDocument, AccountNote
)
from models.project import Project
from models.channel import Channel
from models.user import User
from schemas.ad_account import (
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
from utils.response import success_response, error_response
from exceptions import ValidationError, NotFoundError, PermissionError
from services.audit_log_service import AuditLogService


class AdAccountService:
    """广告账户管理服务类"""

    # 状态转换规则
    ALLOWED_TRANSITIONS = {
        "new": ["testing"],
        "testing": ["active", "suspended", "dead"],
        "active": ["suspended", "dead", "archived"],
        "suspended": ["active", "dead", "archived"],
        "dead": ["archived"],
        "archived": []
    }

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditLogService(db)

    async def create_account(
        self,
        request: AdAccountCreateRequest,
        current_user_id: int
    ) -> AdAccount:
        """创建广告账户"""
        # 验证项目是否存在
        project = self.db.query(Project).filter(Project.id == request.project_id).first()
        if not project:
            raise ValidationError("BIZ_401", "项目不存在")

        # 验证渠道是否存在
        channel = self.db.query(Channel).filter(Channel.id == request.channel_id).first()
        if not channel:
            raise ValidationError("BIZ_402", "渠道不存在")

        # 检查平台账户ID是否已存在
        existing = self.db.query(AdAccount).filter(
            AdAccount.account_id == request.account_id
        ).first()
        if existing:
            raise ValidationError("BIZ_403", "平台账户ID已存在")

        # 创建账户
        account = AdAccount(
            account_id=request.account_id,
            name=request.name,
            platform=request.platform.value,
            platform_account_id=request.platform_account_id,
            platform_business_id=request.platform_business_id,
            project_id=request.project_id,
            channel_id=request.channel_id,
            assigned_user_id=request.assigned_user_id,
            daily_budget=request.daily_budget,
            total_budget=request.total_budget,
            remaining_budget=request.total_budget,
            currency=request.currency,
            timezone=request.timezone,
            country=request.country,
            account_type=request.account_type,
            payment_method=request.payment_method,
            billing_information=request.billing_information,
            auto_monitoring=request.auto_monitoring,
            alert_thresholds=request.alert_thresholds,
            notes=request.notes,
            tags=request.tags,
            metadata=request.metadata,
            created_by=current_user_id
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
            details=f"创建广告账户: {account.name}"
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
            query = query.filter(AdAccount.assigned_user_id == current_user_id)
        elif user_role == "account_manager":
            # 账户管理员只能看到自己项目的账户
            query = query.join(Project).filter(
                Project.account_manager_id == current_user_id
            )

        # 应用过滤条件
        if status:
            query = query.filter(AdAccount.status == status)
        if platform:
            query = query.filter(AdAccount.platform == platform)
        if project_id:
            query = query.filter(AdAccount.project_id == project_id)
        if channel_id:
            query = query.filter(AdAccount.channel_id == channel_id)
        if assigned_user_id:
            query = query.filter(AdAccount.assigned_user_id == assigned_user_id)

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
            raise NotFoundError("SYS_004", "广告账户不存在")

        # 权限检查
        if user_role == "media_buyer" and account.assigned_user_id != current_user_id:
            raise PermissionError("BIZ_403", "无权限访问此账户")
        elif user_role == "account_manager":
            # 检查是否是账户管理员的项目
            project = self.db.query(Project).filter(Project.id == account.project_id).first()
            if not project or project.account_manager_id != current_user_id:
                raise PermissionError("BIZ_403", "无权限访问此账户")

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
        for field, value in request.dict(exclude_unset=True).items():
            if hasattr(account, field):
                old_value = getattr(account, field)
                if old_value != value:
                    old_values[field] = old_value

        # 更新字段
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(account, field, value)

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
        current_user_id: int
    ) -> AdAccount:
        """更新账户状态"""
        account = await self.get_account_by_id(account_id, current_user_id)

        # 检查状态转换是否合法
        allowed_transitions = self.ALLOWED_TRANSITIONS.get(account.status, [])
        if request.status != account.status and request.status not in allowed_transitions:
            raise ValidationError(
                "BIZ_404",
                f"不能从状态 {account.status} 转换到 {request.status}"
            )

        # 更新状态
        old_status = account.status
        account.status = request.status
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
            query = query.filter(AdAccount.assigned_user_id == current_user_id)
        elif user_role == "account_manager":
            query = query.join(Project).filter(
                Project.account_manager_id == current_user_id
            )

        # 应用过滤条件
        if project_id:
            query = query.filter(AdAccount.project_id == project_id)
        if channel_id:
            query = query.filter(AdAccount.channel_id == channel_id)
        if platform:
            query = query.filter(AdAccount.platform == platform)

        # 总体统计
        total_accounts = query.count()
        active_accounts = query.filter(AdAccount.status == "active").count()
        suspended_accounts = query.filter(AdAccount.status == "suspended").count()
        dead_accounts = query.filter(AdAccount.status == "dead").count()
        new_accounts = query.filter(AdAccount.status == "new").count()

        # 性能统计
        stats = query.with_entities(
            func.sum(AdAccount.total_spend).label('total_spend'),
            func.sum(AdAccount.total_leads).label('total_leads'),
            func.avg(AdAccount.avg_cpl).label('avg_cpl'),
            func.min(AdAccount.best_cpl).label('best_cpl'),
            func.sum(AdAccount.total_budget).label('total_budget'),
            func.sum(AdAccount.daily_budget).label('total_daily_budget')
        ).first()

        total_spend = stats.total_spend or Decimal('0')
        total_leads = stats.total_leads or 0
        avg_cpl = stats.avg_cpl or Decimal('0')
        best_cpl = stats.best_cpl or Decimal('0')
        total_budget = stats.total_budget or Decimal('0')
        total_daily_budget = stats.total_daily_budget or Decimal('0')

        # 预算使用率
        budget_utilization = float(total_spend / total_budget * 100) if total_budget > 0 else 0

        # 平台分布
        platform_dist = query.with_entities(
            AdAccount.platform,
            func.count().label('count')
        ).group_by(AdAccount.platform).all()

        platform_distribution = [
            {"platform": p[0], "count": p[1]}
            for p in platform_dist
        ]

        # 状态分布
        status_dist = query.with_entities(
            AdAccount.status,
            func.count().label('count')
        ).group_by(AdAccount.status).all()

        status_distribution = [
            {"status": s[0], "count": s[1]}
            for s in status_dist
        ]

        # TOP表现账户
        top_performers = query.order_by(
            AdAccount.total_leads.desc()
        ).limit(10).all()

        low_performers = query.filter(
            AdAccount.status == "active"
        ).order_by(
            AdAccount.avg_cpl.desc()
        ).limit(10).all()

        # 预警统计
        alerts_query = self.db.query(AccountAlert)
        if user_role == "media_buyer":
            alerts_query = alerts_query.join(AdAccount).filter(
                AdAccount.assigned_user_id == current_user_id
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
                    "name": a.name,
                    "platform": a.platform,
                    "total_leads": a.total_leads,
                    "avg_cpl": a.avg_cpl
                }
                for a in top_performers
            ],
            low_performers=[
                {
                    "id": a.id,
                    "name": a.name,
                    "platform": a.platform,
                    "avg_cpl": a.avg_cpl
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
            AccountAlert.account_id == account_id
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
            account_id=account_id,
            alert_type=request.alert_type.value,
            severity=request.severity.value,
            title=request.title,
            message=request.message,
            trigger_condition=request.trigger_condition,
            notify_users=request.notify_users
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
            raise NotFoundError("SYS_004", "预警不存在")

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
            AccountNote.account_id == account_id
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
            account_id=account_id,
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
            raise ValidationError("BIZ_405", "只有归档状态的账户才能删除")

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
            details=f"删除广告账户: {account.name}"
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
            account_id=account_id,
            old_status=old_status,
            new_status=new_status,
            change_reason=reason,
            changed_by=user_id,
            change_source=source
        )

        self.db.add(history)
        self.db.commit()