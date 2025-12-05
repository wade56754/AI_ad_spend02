"""
双账本记账服务 (对齐 LEDGER_SOT.md v1.1)

提供双账本的核心记账功能：
- PROJECT账本：项目收入（REVENUE, TOPUP, REVERSAL）
- SUPPLIER账本：供应商成本（COST, TOPUP, TRANSFER_OUT, TRANSFER_IN, REVERSAL）

Version: 1.0 (2025-12-05)
SoT: LEDGER_SOT.md v1.1
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple, Union
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from backend.models import LedgerEntry, LedgerBookType, LedgerEntryType
from backend.models import Project, Supplier


class LedgerEntryService:
    """
    双账本记账服务类

    职责：
    - 创建PROJECT/SUPPLIER账本分录
    - 验证账本类型和分录类型匹配
    - 验证金额方向正确性
    - 查询账本流水和余额
    """

    # ========== 创建分录 ==========

    @staticmethod
    def create_project_entry(
        session: Session,
        project_id: int,
        entry_type: str,
        amount: Decimal,
        balance_after: Decimal,
        reference_type: str = None,
        reference_id: int = None,
        performed_by: UUID = None,
        reason: str = None,
        notes: str = None,
        currency: str = "CNY",
        ad_account_id: int = None,
        entry_date: datetime = None
    ) -> LedgerEntry:
        """
        创建PROJECT账本分录

        Args:
            session: 数据库会话
            project_id: 项目ID（必填）
            entry_type: 分录类型（REVENUE, TOPUP, REVERSAL）
            amount: 金额
            balance_after: 交易后余额
            reference_type: 关联记录类型
            reference_id: 关联记录ID
            performed_by: 操作人ID
            reason: 操作原因
            notes: 备注
            currency: 货币类型（默认CNY）
            ad_account_id: 广告账户ID（可选）
            entry_date: 分录日期（默认当前时间）

        Returns:
            创建的LedgerEntry记录

        Raises:
            ValueError: 如果entry_type不是PROJECT账本允许的类型
        """
        # 验证entry_type
        allowed_types = [LedgerEntryType.REVENUE.value, LedgerEntryType.TOPUP.value, LedgerEntryType.REVERSAL.value]
        if entry_type not in allowed_types:
            raise ValueError(f"PROJECT账本不支持entry_type: {entry_type}。允许: {allowed_types}")

        # 验证金额方向
        if entry_type in [LedgerEntryType.REVENUE.value, LedgerEntryType.TOPUP.value] and amount < 0:
            raise ValueError(f"{entry_type}分录金额必须为正数，当前: {amount}")
        if entry_type == LedgerEntryType.REVERSAL.value and amount > 0:
            raise ValueError(f"REVERSAL分录金额必须为负数，当前: {amount}")

        entry = LedgerEntry(
            ledger_type=LedgerBookType.PROJECT.value,
            project_id=project_id,
            supplier_id=None,  # PROJECT账本必须为NULL
            ad_account_id=ad_account_id,
            entry_type=entry_type,
            amount=amount,
            currency=currency,
            balance_after=balance_after,
            reference_type=reference_type,
            reference_id=reference_id,
            performed_by=performed_by,
            reason=reason,
            notes=notes,
            entry_date=entry_date or datetime.utcnow()
        )

        session.add(entry)
        return entry

    @staticmethod
    def create_supplier_entry(
        session: Session,
        supplier_id: int,
        entry_type: str,
        amount: Decimal,
        balance_after: Decimal,
        reference_type: str = None,
        reference_id: int = None,
        performed_by: UUID = None,
        reason: str = None,
        notes: str = None,
        currency: str = "CNY",
        ad_account_id: int = None,
        entry_date: datetime = None
    ) -> LedgerEntry:
        """
        创建SUPPLIER账本分录

        Args:
            session: 数据库会话
            supplier_id: 供应商ID（必填）
            entry_type: 分录类型（COST, TOPUP, TRANSFER_OUT, TRANSFER_IN, REVERSAL）
            amount: 金额
            balance_after: 交易后余额
            reference_type: 关联记录类型
            reference_id: 关联记录ID
            performed_by: 操作人ID
            reason: 操作原因
            notes: 备注
            currency: 货币类型（默认CNY）
            ad_account_id: 广告账户ID（可选）
            entry_date: 分录日期（默认当前时间）

        Returns:
            创建的LedgerEntry记录

        Raises:
            ValueError: 如果entry_type不是SUPPLIER账本允许的类型
        """
        # 验证entry_type
        allowed_types = [
            LedgerEntryType.COST.value,
            LedgerEntryType.TOPUP.value,
            LedgerEntryType.TRANSFER_OUT.value,
            LedgerEntryType.TRANSFER_IN.value,
            LedgerEntryType.REVERSAL.value
        ]
        if entry_type not in allowed_types:
            raise ValueError(f"SUPPLIER账本不支持entry_type: {entry_type}。允许: {allowed_types}")

        # 验证金额方向
        positive_types = [LedgerEntryType.TOPUP.value, LedgerEntryType.TRANSFER_IN.value]
        negative_types = [LedgerEntryType.COST.value, LedgerEntryType.TRANSFER_OUT.value, LedgerEntryType.REVERSAL.value]

        if entry_type in positive_types and amount < 0:
            raise ValueError(f"{entry_type}分录金额必须为正数，当前: {amount}")
        if entry_type in negative_types and amount > 0:
            raise ValueError(f"{entry_type}分录金额必须为负数，当前: {amount}")

        entry = LedgerEntry(
            ledger_type=LedgerBookType.SUPPLIER.value,
            project_id=None,  # SUPPLIER账本必须为NULL
            supplier_id=supplier_id,
            ad_account_id=ad_account_id,
            entry_type=entry_type,
            amount=amount,
            currency=currency,
            balance_after=balance_after,
            reference_type=reference_type,
            reference_id=reference_id,
            performed_by=performed_by,
            reason=reason,
            notes=notes,
            entry_date=entry_date or datetime.utcnow()
        )

        session.add(entry)
        return entry

    # ========== DailyReport计费入账（LEDGER_SOT.md v1.1 第7章）==========

    @staticmethod
    def create_daily_report_entries(
        session: Session,
        daily_report_id: int,
        project_id: int,
        supplier_id: int,
        revenue_amount: Decimal,
        cost_amount: Decimal,
        project_balance_after: Decimal,
        supplier_balance_after: Decimal,
        performed_by: UUID = None,
        ad_account_id: int = None
    ) -> Tuple[LedgerEntry, LedgerEntry]:
        """
        DailyReport锁定后生成双账本分录

        一条DailyReport生成两条Ledger记录：
        - PROJECT账本: REVENUE（正数，项目收入）
        - SUPPLIER账本: COST（负数，供应商成本）

        Args:
            session: 数据库会话
            daily_report_id: 日报ID
            project_id: 项目ID
            supplier_id: 供应商ID
            revenue_amount: 项目收入金额（正数）
            cost_amount: 供应商成本金额（负数）
            project_balance_after: 项目账本交易后余额
            supplier_balance_after: 供应商账本交易后余额
            performed_by: 操作人ID
            ad_account_id: 广告账户ID（可选）

        Returns:
            (project_entry, supplier_entry) 两条分录
        """
        # 创建PROJECT REVENUE分录
        project_entry = LedgerEntryService.create_project_entry(
            session=session,
            project_id=project_id,
            entry_type=LedgerEntryType.REVENUE.value,
            amount=revenue_amount,
            balance_after=project_balance_after,
            reference_type="daily_reports",
            reference_id=daily_report_id,
            performed_by=performed_by,
            reason="日报计费入账",
            ad_account_id=ad_account_id
        )

        # 创建SUPPLIER COST分录
        supplier_entry = LedgerEntryService.create_supplier_entry(
            session=session,
            supplier_id=supplier_id,
            entry_type=LedgerEntryType.COST.value,
            amount=cost_amount,  # 应为负数
            balance_after=supplier_balance_after,
            reference_type="daily_reports",
            reference_id=daily_report_id,
            performed_by=performed_by,
            reason="日报成本入账",
            ad_account_id=ad_account_id
        )

        return project_entry, supplier_entry

    # ========== 充值入账（LEDGER_SOT.md v1.1 第8/9章）==========

    @staticmethod
    def create_project_topup_entry(
        session: Session,
        project_id: int,
        topup_request_id: int,
        amount: Decimal,
        balance_after: Decimal,
        performed_by: UUID = None
    ) -> LedgerEntry:
        """
        项目充值入账（PROJECT账本 TOPUP）

        Args:
            session: 数据库会话
            project_id: 项目ID
            topup_request_id: 充值申请ID
            amount: 充值金额（正数）
            balance_after: 充值后余额
            performed_by: 操作人ID

        Returns:
            创建的TOPUP分录
        """
        return LedgerEntryService.create_project_entry(
            session=session,
            project_id=project_id,
            entry_type=LedgerEntryType.TOPUP.value,
            amount=amount,
            balance_after=balance_after,
            reference_type="topup_requests",
            reference_id=topup_request_id,
            performed_by=performed_by,
            reason="项目充值入账"
        )

    @staticmethod
    def create_supplier_topup_entry(
        session: Session,
        supplier_id: int,
        topup_request_id: int,
        amount: Decimal,
        balance_after: Decimal,
        performed_by: UUID = None
    ) -> LedgerEntry:
        """
        供应商充值入账（SUPPLIER账本 TOPUP）

        Args:
            session: 数据库会话
            supplier_id: 供应商ID
            topup_request_id: 充值申请ID
            amount: 充值金额（正数）
            balance_after: 充值后余额
            performed_by: 操作人ID

        Returns:
            创建的TOPUP分录
        """
        return LedgerEntryService.create_supplier_entry(
            session=session,
            supplier_id=supplier_id,
            entry_type=LedgerEntryType.TOPUP.value,
            amount=amount,
            balance_after=balance_after,
            reference_type="topup_requests",
            reference_id=topup_request_id,
            performed_by=performed_by,
            reason="供应商充值入账"
        )

    # ========== 死号迁移（LEDGER_SOT.md v1.1 第10章）==========

    @staticmethod
    def create_transfer_entries(
        session: Session,
        transfer_request_id: int,
        from_supplier_id: int,
        to_supplier_id: int,
        amount: Decimal,
        from_balance_after: Decimal,
        to_balance_after: Decimal,
        performed_by: UUID = None,
        from_ad_account_id: int = None,
        to_ad_account_id: int = None
    ) -> Tuple[LedgerEntry, LedgerEntry]:
        """
        死号余额迁移分录（SUPPLIER账本内部转账）

        一条Transfer生成两条SUPPLIER账本记录：
        - 源账户: TRANSFER_OUT（负数）
        - 目标账户: TRANSFER_IN（正数）

        Args:
            session: 数据库会话
            transfer_request_id: 迁移申请ID
            from_supplier_id: 源供应商ID
            to_supplier_id: 目标供应商ID
            amount: 迁移金额（正数）
            from_balance_after: 源账户迁移后余额
            to_balance_after: 目标账户迁移后余额
            performed_by: 操作人ID
            from_ad_account_id: 源广告账户ID
            to_ad_account_id: 目标广告账户ID

        Returns:
            (out_entry, in_entry) 两条分录
        """
        # 创建TRANSFER_OUT分录（负数）
        out_entry = LedgerEntryService.create_supplier_entry(
            session=session,
            supplier_id=from_supplier_id,
            entry_type=LedgerEntryType.TRANSFER_OUT.value,
            amount=-abs(amount),  # 确保为负数
            balance_after=from_balance_after,
            reference_type="transfer_requests",
            reference_id=transfer_request_id,
            performed_by=performed_by,
            reason="死号余额转出",
            ad_account_id=from_ad_account_id
        )

        # 创建TRANSFER_IN分录（正数）
        in_entry = LedgerEntryService.create_supplier_entry(
            session=session,
            supplier_id=to_supplier_id,
            entry_type=LedgerEntryType.TRANSFER_IN.value,
            amount=abs(amount),  # 确保为正数
            balance_after=to_balance_after,
            reference_type="transfer_requests",
            reference_id=transfer_request_id,
            performed_by=performed_by,
            reason="死号余额转入",
            ad_account_id=to_ad_account_id
        )

        return out_entry, in_entry

    # ========== 红冲分录（LEDGER_SOT.md v1.1 第12章）==========

    @staticmethod
    def create_reversal_entry(
        session: Session,
        original_entry_id: int,
        reversal_amount: Decimal,
        balance_after: Decimal,
        performed_by: UUID = None,
        reason: str = "错误修正红冲"
    ) -> LedgerEntry:
        """
        创建红冲分录

        根据原始分录的ledger_type创建相应账本的REVERSAL记录

        Args:
            session: 数据库会话
            original_entry_id: 原始分录ID
            reversal_amount: 红冲金额（负数）
            balance_after: 红冲后余额
            performed_by: 操作人ID
            reason: 红冲原因

        Returns:
            创建的REVERSAL分录
        """
        # 查询原始分录
        original = session.query(LedgerEntry).filter(
            LedgerEntry.id == original_entry_id
        ).first()

        if not original:
            raise ValueError(f"原始分录不存在: {original_entry_id}")

        # 确保红冲金额为负数
        if reversal_amount > 0:
            reversal_amount = -reversal_amount

        if original.ledger_type == LedgerBookType.PROJECT.value:
            return LedgerEntryService.create_project_entry(
                session=session,
                project_id=original.project_id,
                entry_type=LedgerEntryType.REVERSAL.value,
                amount=reversal_amount,
                balance_after=balance_after,
                reference_type="ledger_entries",
                reference_id=original_entry_id,
                performed_by=performed_by,
                reason=reason,
                ad_account_id=original.ad_account_id
            )
        else:
            return LedgerEntryService.create_supplier_entry(
                session=session,
                supplier_id=original.supplier_id,
                entry_type=LedgerEntryType.REVERSAL.value,
                amount=reversal_amount,
                balance_after=balance_after,
                reference_type="ledger_entries",
                reference_id=original_entry_id,
                performed_by=performed_by,
                reason=reason,
                ad_account_id=original.ad_account_id
            )

    # ========== 查询方法 ==========

    @staticmethod
    def get_project_entries(
        session: Session,
        project_id: int,
        entry_type: str = None,
        start_date: date = None,
        end_date: date = None,
        page: int = 1,
        size: int = 20
    ) -> Tuple[List[LedgerEntry], int]:
        """
        获取项目账本分录列表

        Returns:
            (entries, total_count)
        """
        query = session.query(LedgerEntry).filter(
            LedgerEntry.ledger_type == LedgerBookType.PROJECT.value,
            LedgerEntry.project_id == project_id
        )

        if entry_type:
            query = query.filter(LedgerEntry.entry_type == entry_type)
        if start_date:
            query = query.filter(LedgerEntry.entry_date >= start_date)
        if end_date:
            query = query.filter(LedgerEntry.entry_date <= end_date)

        total = query.count()
        offset = (page - 1) * size
        entries = query.order_by(desc(LedgerEntry.entry_date)).offset(offset).limit(size).all()

        return entries, total

    @staticmethod
    def get_supplier_entries(
        session: Session,
        supplier_id: int,
        entry_type: str = None,
        start_date: date = None,
        end_date: date = None,
        page: int = 1,
        size: int = 20
    ) -> Tuple[List[LedgerEntry], int]:
        """
        获取供应商账本分录列表

        Returns:
            (entries, total_count)
        """
        query = session.query(LedgerEntry).filter(
            LedgerEntry.ledger_type == LedgerBookType.SUPPLIER.value,
            LedgerEntry.supplier_id == supplier_id
        )

        if entry_type:
            query = query.filter(LedgerEntry.entry_type == entry_type)
        if start_date:
            query = query.filter(LedgerEntry.entry_date >= start_date)
        if end_date:
            query = query.filter(LedgerEntry.entry_date <= end_date)

        total = query.count()
        offset = (page - 1) * size
        entries = query.order_by(desc(LedgerEntry.entry_date)).offset(offset).limit(size).all()

        return entries, total

    @staticmethod
    def get_entry_statistics(
        session: Session,
        ledger_type: str,
        entity_id: int,
        start_date: date = None,
        end_date: date = None
    ) -> Dict[str, Any]:
        """
        获取账本统计信息

        Args:
            session: 数据库会话
            ledger_type: 账本类型（PROJECT/SUPPLIER）
            entity_id: 项目ID或供应商ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            按entry_type分组的统计数据
        """
        if ledger_type == LedgerBookType.PROJECT.value:
            base_filter = and_(
                LedgerEntry.ledger_type == LedgerBookType.PROJECT.value,
                LedgerEntry.project_id == entity_id
            )
        else:
            base_filter = and_(
                LedgerEntry.ledger_type == LedgerBookType.SUPPLIER.value,
                LedgerEntry.supplier_id == entity_id
            )

        query = session.query(
            LedgerEntry.entry_type,
            func.count(LedgerEntry.id).label('count'),
            func.sum(LedgerEntry.amount).label('total_amount')
        ).filter(base_filter)

        if start_date:
            query = query.filter(LedgerEntry.entry_date >= start_date)
        if end_date:
            query = query.filter(LedgerEntry.entry_date <= end_date)

        stats = query.group_by(LedgerEntry.entry_type).all()

        return {
            "ledger_type": ledger_type,
            "entity_id": entity_id,
            "by_entry_type": [
                {
                    "entry_type": stat.entry_type,
                    "count": stat.count,
                    "total_amount": float(stat.total_amount) if stat.total_amount else 0.0
                }
                for stat in stats
            ]
        }


def get_ledger_entry_service() -> LedgerEntryService:
    """获取双账本记账服务实例"""
    return LedgerEntryService()
