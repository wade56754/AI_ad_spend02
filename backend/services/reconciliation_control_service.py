"""
对账中控服务层

OpenSpec Change: add-reconciliation-control-center
SoT References:
- DATA_SCHEMA.md v5.4 §3.5.5, §3.5.6, §3.5.7
- STATE_MACHINE.md v2.6 §11.4 对账差异单状态机
- BUSINESS_RULES.md v3.2 BR-REC-*, BR-SET-*
- ERROR_CODES_SOT.md v2.2 REC_*, SET_*

Phase 1 约束 (MASTER.md v4.4 §5):
- 提示 + 高亮 + 记录
- 不自动阻断

Version: 1.0
Author: Claude Code (OpenSpec apply)
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy import func, desc, and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.core.error_codes import BusinessErrorCodes
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError,
)
from backend.models.reconciliation import (
    SettlementRule,
    RuleType,
    AdAccountBalanceSnapshot,
    SnapshotSource,
    ReconciliationIssue,
    IssueType,
    IssueStatus,
    ResolutionType,
    ISSUE_STATUS_TRANSITIONS,
    CommissionRule,
)
from backend.models import AdAccount, User
from backend.schemas.reconciliation import (
    SettlementRuleCreate,
    SettlementRuleUpdate,
    BalanceSnapshotCreate,
    BalanceSnapshotBatchCreate,
    ReconciliationIssueCreate,
    ReconciliationIssueAssign,
    ReconciliationIssueResolve,
    ReconciliationIssueStatus as SchemaIssueStatus,
    CommissionRuleCreate,
    CommissionRuleUpdate,
)


class SettlementRuleService:
    """结算规则服务"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: SettlementRuleCreate, created_by: UUID) -> SettlementRule:
        """
        创建结算规则

        Business Rules:
        - BR-SET-001: tiered 规则必须有 tiers 数组
        - BR-SET-002: markup 规则必须有 markup_type 和 markup_value
        """
        rule = SettlementRule(
            name=data.name,
            rule_type=data.rule_type.value,
            config=data.config,
            effective_from=data.effective_from,
            effective_to=data.effective_to,
            created_by=created_by,
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def get_by_id(self, rule_id: int) -> Optional[SettlementRule]:
        """根据ID获取规则"""
        return (
            self.db.query(SettlementRule).filter(SettlementRule.id == rule_id).first()
        )

    def list_rules(
        self,
        rule_type: Optional[RuleType] = None,
        effective_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[SettlementRule], int]:
        """列出结算规则"""
        query = self.db.query(SettlementRule)

        if rule_type:
            query = query.filter(SettlementRule.rule_type == rule_type.value)

        if effective_date:
            query = query.filter(
                and_(
                    SettlementRule.effective_from <= effective_date,
                    or_(
                        SettlementRule.effective_to.is_(None),
                        SettlementRule.effective_to >= effective_date,
                    ),
                )
            )

        total = query.count()
        rules = (
            query.order_by(desc(SettlementRule.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        return rules, total

    def update(self, rule_id: int, data: SettlementRuleUpdate) -> SettlementRule:
        """更新结算规则"""
        rule = self.get_by_id(rule_id)
        if not rule:
            raise ResourceNotFoundError("结算规则不存在")

        if data.name is not None:
            rule.name = data.name
        if data.config is not None:
            rule.config = data.config
        if data.effective_to is not None:
            rule.effective_to = data.effective_to

        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete(self, rule_id: int) -> bool:
        """删除结算规则 (软删除 - 设置 effective_to)"""
        rule = self.get_by_id(rule_id)
        if not rule:
            raise ResourceNotFoundError("结算规则不存在")

        # 软删除：设置结束日期
        # 必须满足 effective_to > effective_from 约束
        from datetime import timedelta

        tomorrow = date.today() + timedelta(days=1)
        # 如果规则 effective_from 是今天或未来，设置为 effective_from + 1 天
        if rule.effective_from >= date.today():
            rule.effective_to = rule.effective_from + timedelta(days=1)
        else:
            rule.effective_to = tomorrow
        self.db.commit()
        return True


class BalanceSnapshotService:
    """余额快照服务"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self, data: BalanceSnapshotCreate, created_by: UUID
    ) -> AdAccountBalanceSnapshot:
        """
        创建余额快照

        Business Rules:
        - BR-REC-003: 同账户同日期只能有一条快照
        """
        # 检查是否已存在
        existing = (
            self.db.query(AdAccountBalanceSnapshot)
            .filter(
                and_(
                    AdAccountBalanceSnapshot.ad_account_id == data.ad_account_id,
                    AdAccountBalanceSnapshot.snapshot_date == data.snapshot_date,
                )
            )
            .first()
        )

        if existing:
            raise ResourceConflictError(
                f"账户 {data.ad_account_id} 在 {data.snapshot_date} 已有快照记录"
            )

        # 计算 remaining_balance
        remaining = data.balance - data.deposit

        snapshot = AdAccountBalanceSnapshot(
            ad_account_id=data.ad_account_id,
            snapshot_date=data.snapshot_date,
            balance=data.balance,
            deposit=data.deposit,
            remaining_balance=remaining,
            source=data.source.value,
            notes=data.notes,
            created_by=created_by,
        )
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot

    def batch_create(
        self, data: BalanceSnapshotBatchCreate, created_by: UUID
    ) -> List[AdAccountBalanceSnapshot]:
        """批量创建余额快照"""
        snapshots = []
        for item in data.snapshots:
            try:
                snapshot = self.create(item, created_by)
                snapshots.append(snapshot)
            except ResourceConflictError:
                # 跳过已存在的，或根据业务需求处理
                pass
        return snapshots

    def get_by_id(self, snapshot_id: int) -> Optional[AdAccountBalanceSnapshot]:
        """根据ID获取快照"""
        return (
            self.db.query(AdAccountBalanceSnapshot)
            .filter(AdAccountBalanceSnapshot.id == snapshot_id)
            .first()
        )

    def get_by_account_date(
        self, ad_account_id: int, snapshot_date: date
    ) -> Optional[AdAccountBalanceSnapshot]:
        """根据账户和日期获取快照"""
        return (
            self.db.query(AdAccountBalanceSnapshot)
            .filter(
                and_(
                    AdAccountBalanceSnapshot.ad_account_id == ad_account_id,
                    AdAccountBalanceSnapshot.snapshot_date == snapshot_date,
                )
            )
            .first()
        )

    def list_snapshots(
        self,
        ad_account_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[AdAccountBalanceSnapshot], int]:
        """列出余额快照"""
        query = self.db.query(AdAccountBalanceSnapshot)

        if ad_account_id:
            query = query.filter(
                AdAccountBalanceSnapshot.ad_account_id == ad_account_id
            )
        if start_date:
            query = query.filter(AdAccountBalanceSnapshot.snapshot_date >= start_date)
        if end_date:
            query = query.filter(AdAccountBalanceSnapshot.snapshot_date <= end_date)

        total = query.count()
        snapshots = (
            query.order_by(desc(AdAccountBalanceSnapshot.snapshot_date))
            .offset(skip)
            .limit(limit)
            .all()
        )
        return snapshots, total

    def verify_conservation(
        self,
        ad_account_id: int,
        start_date: date,
        end_date: date,
        topup_total: Decimal,
        spend_total: Decimal,
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        验证守恒公式 (BR-REC-001)

        公式: Σ(充值到账) - Σ(实际消耗) = Δ(余额) + Δ(押款)

        Returns:
            (is_valid, details)
        """
        start_snapshot = self.get_by_account_date(ad_account_id, start_date)
        end_snapshot = self.get_by_account_date(ad_account_id, end_date)

        if not start_snapshot or not end_snapshot:
            return False, {
                "error": "快照缺失",
                "missing_start": start_snapshot is None,
                "missing_end": end_snapshot is None,
            }

        # 计算余额和押款变化
        balance_delta = end_snapshot.balance - start_snapshot.balance
        deposit_delta = end_snapshot.deposit - start_snapshot.deposit

        # 左边: 充值 - 消耗
        left_side = topup_total - spend_total
        # 右边: 余额变化 + 押款变化
        right_side = balance_delta + deposit_delta

        # 允许 0.01 的舍入误差
        is_valid = abs(left_side - right_side) < Decimal("0.01")

        return is_valid, {
            "topup_total": float(topup_total),
            "spend_total": float(spend_total),
            "balance_delta": float(balance_delta),
            "deposit_delta": float(deposit_delta),
            "left_side": float(left_side),
            "right_side": float(right_side),
            "difference": float(left_side - right_side),
            "is_valid": is_valid,
        }


class ReconciliationIssueService:
    """对账差异单服务"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self, data: ReconciliationIssueCreate, created_by: UUID
    ) -> ReconciliationIssue:
        """
        创建对账差异单

        初始状态: open
        """
        issue = ReconciliationIssue(
            reconciliation_batch_id=data.reconciliation_batch_id,
            ad_account_id=data.ad_account_id,
            issue_date=data.issue_date,
            issue_type=data.issue_type.value,
            expected_amount=data.expected_amount,
            actual_amount=data.actual_amount,
            status=IssueStatus.OPEN.value,
            attachments=data.attachments or [],
            created_by=created_by,
        )
        self.db.add(issue)
        self.db.commit()
        self.db.refresh(issue)
        return issue

    def get_by_id(self, issue_id: int) -> Optional[ReconciliationIssue]:
        """根据ID获取差异单"""
        return (
            self.db.query(ReconciliationIssue)
            .filter(ReconciliationIssue.id == issue_id)
            .first()
        )

    def list_issues(
        self,
        status: Optional[IssueStatus] = None,
        issue_type: Optional[IssueType] = None,
        ad_account_id: Optional[int] = None,
        assigned_to: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sla_breached: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[ReconciliationIssue], int]:
        """列出差异单"""
        query = self.db.query(ReconciliationIssue)

        if status:
            query = query.filter(ReconciliationIssue.status == status.value)
        if issue_type:
            query = query.filter(ReconciliationIssue.issue_type == issue_type.value)
        if ad_account_id:
            query = query.filter(ReconciliationIssue.ad_account_id == ad_account_id)
        if assigned_to:
            query = query.filter(ReconciliationIssue.assigned_to == assigned_to)
        if start_date:
            query = query.filter(ReconciliationIssue.issue_date >= start_date)
        if end_date:
            query = query.filter(ReconciliationIssue.issue_date <= end_date)
        if sla_breached is not None:
            query = query.filter(ReconciliationIssue.sla_breached == sla_breached)

        total = query.count()
        issues = (
            query.order_by(desc(ReconciliationIssue.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        return issues, total

    def assign(
        self, issue_id: int, data: ReconciliationIssueAssign, operator_id: UUID
    ) -> ReconciliationIssue:
        """
        分配差异单

        状态流转: open -> assigned
        """
        issue = self.get_by_id(issue_id)
        if not issue:
            raise ResourceNotFoundError("差异单不存在")

        # 检查状态流转
        if not issue.can_transition_to(IssueStatus.ASSIGNED):
            raise BusinessLogicError(
                f"无法从 {issue.status} 状态分配差异单", error_code="REC_005"
            )

        issue.status = IssueStatus.ASSIGNED.value
        issue.assigned_to = UUID(data.assigned_to)
        issue.assigned_at = datetime.now(timezone.utc)
        if data.sla_deadline:
            issue.sla_deadline = data.sla_deadline

        self.db.commit()
        self.db.refresh(issue)
        return issue

    def start_investigation(
        self, issue_id: int, operator_id: UUID
    ) -> ReconciliationIssue:
        """
        开始调查

        状态流转: assigned -> investigating
        """
        issue = self.get_by_id(issue_id)
        if not issue:
            raise ResourceNotFoundError("差异单不存在")

        if not issue.can_transition_to(IssueStatus.INVESTIGATING):
            raise BusinessLogicError(f"无法从 {issue.status} 状态开始调查", error_code="REC_005")

        issue.status = IssueStatus.INVESTIGATING.value
        self.db.commit()
        self.db.refresh(issue)
        return issue

    def resolve(
        self, issue_id: int, data: ReconciliationIssueResolve, resolved_by: UUID
    ) -> ReconciliationIssue:
        """
        处理差异单

        状态流转: investigating -> resolved
        """
        issue = self.get_by_id(issue_id)
        if not issue:
            raise ResourceNotFoundError("差异单不存在")

        if not issue.can_transition_to(IssueStatus.RESOLVED):
            raise BusinessLogicError(
                f"无法从 {issue.status} 状态处理差异单", error_code="REC_005"
            )

        issue.status = IssueStatus.RESOLVED.value
        issue.resolution_type = data.resolution_type.value
        issue.resolution_note = data.resolution_note
        issue.resolved_at = datetime.now(timezone.utc)
        issue.resolved_by = resolved_by
        if data.attachments:
            issue.attachments = (issue.attachments or []) + data.attachments

        self.db.commit()
        self.db.refresh(issue)
        return issue

    def close(self, issue_id: int, operator_id: UUID) -> ReconciliationIssue:
        """
        关闭差异单 (终态)

        状态流转: resolved -> closed
        """
        issue = self.get_by_id(issue_id)
        if not issue:
            raise ResourceNotFoundError("差异单不存在")

        if not issue.can_transition_to(IssueStatus.CLOSED):
            raise BusinessLogicError(
                f"无法从 {issue.status} 状态关闭差异单", error_code="REC_005"
            )

        issue.status = IssueStatus.CLOSED.value
        self.db.commit()
        self.db.refresh(issue)
        return issue

    def reopen(self, issue_id: int, operator_id: UUID) -> ReconciliationIssue:
        """
        重新打开差异单

        状态流转: resolved -> investigating 或 investigating -> assigned
        """
        issue = self.get_by_id(issue_id)
        if not issue:
            raise ResourceNotFoundError("差异单不存在")

        current_status = IssueStatus(issue.status)

        if current_status == IssueStatus.RESOLVED:
            if issue.can_transition_to(IssueStatus.INVESTIGATING):
                issue.status = IssueStatus.INVESTIGATING.value
            else:
                raise BusinessLogicError("无法重新打开该差异单", error_code="REC_005")
        elif current_status == IssueStatus.INVESTIGATING:
            if issue.can_transition_to(IssueStatus.ASSIGNED):
                issue.status = IssueStatus.ASSIGNED.value
            else:
                raise BusinessLogicError("无法回退该差异单状态", error_code="REC_005")
        else:
            raise BusinessLogicError(f"无法从 {issue.status} 状态重新打开", error_code="REC_005")

        self.db.commit()
        self.db.refresh(issue)
        return issue

    def check_sla_breach(self) -> int:
        """
        检查并标记 SLA 超时的差异单

        Phase 1: 仅标记，不自动阻断

        Returns:
            标记的数量
        """
        now = datetime.now(timezone.utc)
        count = (
            self.db.query(ReconciliationIssue)
            .filter(
                and_(
                    ReconciliationIssue.sla_breached == False,
                    ReconciliationIssue.sla_deadline.isnot(None),
                    ReconciliationIssue.sla_deadline < now,
                    ReconciliationIssue.status.notin_(
                        [IssueStatus.RESOLVED.value, IssueStatus.CLOSED.value]
                    ),
                )
            )
            .update({"sla_breached": True})
        )

        self.db.commit()
        return count

    def get_summary(self) -> Dict[str, Any]:
        """获取差异单统计摘要"""
        from sqlalchemy import case

        result = self.db.query(
            func.count(ReconciliationIssue.id).label("total"),
            func.sum(
                case((ReconciliationIssue.status == IssueStatus.OPEN.value, 1), else_=0)
            ).label("open"),
            func.sum(
                case(
                    (ReconciliationIssue.status == IssueStatus.ASSIGNED.value, 1),
                    else_=0,
                )
            ).label("assigned"),
            func.sum(
                case(
                    (ReconciliationIssue.status == IssueStatus.INVESTIGATING.value, 1),
                    else_=0,
                )
            ).label("investigating"),
            func.sum(
                case(
                    (ReconciliationIssue.status == IssueStatus.RESOLVED.value, 1),
                    else_=0,
                )
            ).label("resolved"),
            func.sum(
                case(
                    (ReconciliationIssue.status == IssueStatus.CLOSED.value, 1), else_=0
                )
            ).label("closed"),
            func.sum(
                case((ReconciliationIssue.sla_breached == True, 1), else_=0)
            ).label("sla_breached"),
            func.coalesce(func.sum(ReconciliationIssue.difference_amount), 0).label(
                "total_difference"
            ),
        ).first()

        # 按类型统计
        type_counts = (
            self.db.query(
                ReconciliationIssue.issue_type, func.count(ReconciliationIssue.id)
            )
            .group_by(ReconciliationIssue.issue_type)
            .all()
        )

        return {
            "total_issues": result.total or 0,
            "open_issues": result.open or 0,
            "assigned_issues": result.assigned or 0,
            "investigating_issues": result.investigating or 0,
            "resolved_issues": result.resolved or 0,
            "closed_issues": result.closed or 0,
            "sla_breached_issues": result.sla_breached or 0,
            "total_difference_amount": float(result.total_difference or 0),
            "issues_by_type": {t: c for t, c in type_counts},
        }


class CommissionRuleService:
    """
    提成规则服务

    TASK-PRJ-003: 提成配置
    SoT References:
    - BUSINESS_RULES.md v4.8 BR-COM-*
    - DATA_SCHEMA.md v5.7 §3.5.8

    提成计算逻辑:
    - 基于 conversions_final (确认进粉数) 计算
    - 阶梯累加: Σ(tier.count × tier.rate)
    - 按月累计，按项目计算
    - 只统计 final_confirmed 状态的日报
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: CommissionRuleCreate, created_by: UUID) -> CommissionRule:
        """
        创建提成规则

        Business Rules:
        - BR-COM-001: tiers 数组必须非空
        - BR-COM-002: 阶梯必须连续 (min[n+1] = max[n] + 1)
        """
        rule = CommissionRule(
            name=data.name,
            config=data.config,
            effective_from=data.effective_from,
            effective_to=data.effective_to,
            is_default=data.is_default,
            created_by=created_by,
        )

        # 如果设为默认规则，取消其他默认规则
        if data.is_default:
            self._clear_default_rules()

        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def _clear_default_rules(self):
        """取消所有默认规则标记"""
        self.db.query(CommissionRule).filter(CommissionRule.is_default == True).update(
            {"is_default": False}
        )

    def get_by_id(self, rule_id: int) -> Optional[CommissionRule]:
        """根据ID获取规则"""
        return (
            self.db.query(CommissionRule).filter(CommissionRule.id == rule_id).first()
        )

    def get_default_rule(self) -> Optional[CommissionRule]:
        """获取默认提成规则"""
        return (
            self.db.query(CommissionRule)
            .filter(CommissionRule.is_default == True)
            .first()
        )

    def list_rules(
        self,
        effective_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[CommissionRule], int]:
        """列出提成规则"""
        query = self.db.query(CommissionRule)

        if effective_date:
            query = query.filter(
                and_(
                    CommissionRule.effective_from <= effective_date,
                    or_(
                        CommissionRule.effective_to.is_(None),
                        CommissionRule.effective_to >= effective_date,
                    ),
                )
            )

        total = query.count()
        rules = (
            query.order_by(desc(CommissionRule.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        return rules, total

    def update(self, rule_id: int, data: CommissionRuleUpdate) -> CommissionRule:
        """更新提成规则"""
        rule = self.get_by_id(rule_id)
        if not rule:
            raise ResourceNotFoundError("提成规则不存在")

        if data.name is not None:
            rule.name = data.name
        if data.config is not None:
            rule.config = data.config
        if data.effective_to is not None:
            rule.effective_to = data.effective_to
        if data.is_default is not None:
            if data.is_default:
                self._clear_default_rules()
            rule.is_default = data.is_default

        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete(self, rule_id: int) -> bool:
        """删除提成规则 (软删除 - 设置 effective_to)"""
        rule = self.get_by_id(rule_id)
        if not rule:
            raise ResourceNotFoundError("提成规则不存在")

        # 软删除：设置结束日期
        from datetime import timedelta

        tomorrow = date.today() + timedelta(days=1)
        if rule.effective_from >= date.today():
            rule.effective_to = rule.effective_from + timedelta(days=1)
        else:
            rule.effective_to = tomorrow

        # 如果是默认规则，取消默认标记
        rule.is_default = False

        self.db.commit()
        return True

    def calculate_commission(self, rule_id: int, conversions: int) -> Dict[str, Any]:
        """
        计算提成金额

        Args:
            rule_id: 提成规则ID
            conversions: 进粉数 (conversions_final)

        Returns:
            {
                "rule_id": int,
                "rule_name": str,
                "conversions": int,
                "total_commission": Decimal,
                "currency": str,
                "breakdown": [{"tier": {...}, "count": int, "amount": Decimal}, ...]
            }

        Example:
            tiers: [
                {"min": 1, "max": 50, "rate": 1.0},
                {"min": 51, "max": 100, "rate": 1.5},
                {"min": 101, "max": null, "rate": 2.0}
            ]
            conversions: 120
            result: 50×1.0 + 50×1.5 + 20×2.0 = 165.0
        """
        rule = self.get_by_id(rule_id)
        if not rule:
            raise ResourceNotFoundError("提成规则不存在")

        total, breakdown = rule.calculate_commission(conversions)

        return {
            "rule_id": rule.id,
            "rule_name": rule.name,
            "conversions": conversions,
            "total_commission": total,
            "currency": "CNY",
            "breakdown": breakdown,
        }

    def get_effective_rule_for_project(
        self, project_id: int, target_date: Optional[date] = None
    ) -> Optional[CommissionRule]:
        """
        获取项目的生效提成规则

        优先级:
        1. 项目关联的规则 (如果生效)
        2. 默认规则 (如果生效)
        """
        from backend.models.core import Project

        target = target_date or date.today()

        # 查找项目
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None

        # 检查项目关联的规则
        if project.commission_rules_id:
            rule = self.get_by_id(project.commission_rules_id)
            if rule and rule.is_effective(target):
                return rule

        # 回退到默认规则
        default_rule = self.get_default_rule()
        if default_rule and default_rule.is_effective(target):
            return default_rule

        return None
