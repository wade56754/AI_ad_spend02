"""
财务总账服务
处理财务流水、账户余额、预算分配等业务逻辑
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from core.db import get_db_session
from core.error_codes import ErrorCode
from core.response import ApiResponse, PaginatedResponse
from models.ledger import LedgerTransaction, AccountBalance, BudgetAllocation, TransactionType, TransactionStatus
from services.audit_service import AuditService, BusinessAction


class LedgerService:
    """财务总账服务类"""

    @staticmethod
    def create_transaction(
        transaction_type: TransactionType,
        amount: Decimal,
        currency: str = "USD",
        project_id: UUID = None,
        account_id: UUID = None,
        topup_id: UUID = None,
        reference_id: str = None,
        description: str = None,
        metadata: Dict[str, Any] = None,
        user_id: str = None
    ) -> LedgerTransaction:
        """创建财务交易记录"""
        with get_db_session() as session:
            # 生成交易流水号
            transaction_number = LedgerService._generate_transaction_number(
                transaction_type, session
            )

            # 创建交易记录
            transaction = LedgerTransaction(
                id=uuid4(),
                transaction_number=transaction_number,
                transaction_type=transaction_type,
                amount=amount,
                currency=currency,
                status=TransactionStatus.PENDING,
                project_id=project_id,
                account_id=account_id,
                topup_id=topup_id,
                reference_id=reference_id,
                description=description,
                transaction_metadata=metadata or {}
            )

            session.add(transaction)
            session.flush()  # 获取ID

            # 更新账户余额
            LedgerService._update_account_balance(
                session=session,
                account_id=account_id,
                project_id=project_id,
                amount=amount,
                transaction_type=transaction_type,
                transaction_id=transaction.id
            )

            # 更新预算分配
            if project_id and transaction_type in [TransactionType.SPEND]:
                LedgerService._update_budget_allocation(
                    session=session,
                    project_id=project_id,
                    amount=amount,
                    transaction_type=transaction_type
                )

            session.commit()

            # 记录审计日志
            AuditService.log_business_action(
                action=BusinessAction.TOPUP_SUBMIT if transaction_type == TransactionType.TOPUP else BusinessAction.PROJECT_CREATE,
                user_id=user_id or "system",
                resource_type="ledger_transactions",
                resource_id=str(transaction.id),
                new_data={
                    "transaction_number": transaction_number,
                    "transaction_type": transaction_type.value,
                    "amount": float(amount),
                    "currency": currency,
                    "project_id": str(project_id) if project_id else None,
                    "account_id": str(account_id) if account_id else None
                },
                description=f"创建财务交易: {transaction_number} - {transaction_type.value} {amount}"
            )

            return transaction

    @staticmethod
    def update_transaction_status(
        transaction_id: UUID,
        status: TransactionStatus,
        user_id: str = None,
        note: str = None
    ) -> Optional[LedgerTransaction]:
        """更新交易状态"""
        with get_db_session() as session:
            transaction = session.query(LedgerTransaction).filter(
                LedgerTransaction.id == transaction_id
            ).first()

            if not transaction:
                return None

            old_status = transaction.status
            transaction.status = status
            transaction.updated_at = datetime.utcnow()

            if note:
                if not transaction.transaction_metadata:
                    transaction.transaction_metadata = {}
                transaction.transaction_metadata["status_note"] = note

            # 如果状态变为完成，重新更新余额
            if status == TransactionStatus.COMPLETED and old_status != TransactionStatus.COMPLETED:
                LedgerService._update_account_balance(
                    session=session,
                    account_id=transaction.account_id,
                    project_id=transaction.project_id,
                    amount=transaction.amount,
                    transaction_type=transaction.transaction_type,
                    transaction_id=transaction.id
                )

            session.commit()

            # 记录审计日志
            AuditService.log_business_action(
                action=BusinessAction.TOPUP_APPROVE_FINANCE if transaction.transaction_type == TransactionType.TOPUP else BusinessAction.PROJECT_UPDATE,
                user_id=user_id,
                resource_type="ledger_transactions",
                resource_id=str(transaction_id),
                old_data={"status": old_status.value},
                new_data={"status": status.value, "note": note},
                description=f"更新交易状态: {transaction.transaction_number} - {old_status.value} -> {status.value}"
            )

            return transaction

    @staticmethod
    def get_transactions(
        project_id: UUID = None,
        account_id: UUID = None,
        transaction_type: TransactionType = None,
        status: TransactionStatus = None,
        start_date: date = None,
        end_date: date = None,
        page: int = 1,
        size: int = 20
    ) -> PaginatedResponse:
        """获取交易记录列表"""
        with get_db_session() as session:
            query = session.query(LedgerTransaction)

            # 应用过滤条件
            if project_id:
                query = query.filter(LedgerTransaction.project_id == project_id)
            if account_id:
                query = query.filter(LedgerTransaction.account_id == account_id)
            if transaction_type:
                query = query.filter(LedgerTransaction.transaction_type == transaction_type)
            if status:
                query = query.filter(LedgerTransaction.status == status)
            if start_date:
                query = query.filter(LedgerTransaction.created_at >= start_date)
            if end_date:
                query = query.filter(LedgerTransaction.created_at <= end_date)

            # 获取总数
            total = query.count()

            # 应用分页
            offset = (page - 1) * size
            transactions = query.order_by(desc(LedgerTransaction.created_at)).offset(offset).limit(size).all()

            return PaginatedResponse(
                items=[LedgerService._transaction_to_dict(t) for t in transactions],
                total=total,
                page=page,
                size=size,
                pages=(total + size - 1) // size
            )

    @staticmethod
    def get_account_balance(
        account_id: UUID = None,
        project_id: UUID = None
    ) -> Optional[Dict[str, Any]]:
        """获取账户余额"""
        with get_db_session() as session:
            query = session.query(AccountBalance)

            if account_id:
                query = query.filter(AccountBalance.account_id == account_id)
            if project_id:
                query = query.filter(AccountBalance.project_id == project_id)

            balance = query.first()
            if not balance:
                return None

            return {
                "account_id": str(balance.account_id) if balance.account_id else None,
                "project_id": str(balance.project_id) if balance.project_id else None,
                "currency": balance.currency,
                "current_balance": float(balance.current_balance),
                "available_balance": float(balance.available_balance),
                "frozen_balance": float(balance.frozen_balance),
                "total_credit": float(balance.total_credit),
                "total_debit": float(balance.total_debit),
                "last_updated": balance.updated_at.isoformat() if balance.updated_at else None
            }

    @staticmethod
    def get_project_budget_allocation(project_id: UUID) -> List[Dict[str, Any]]:
        """获取项目预算分配"""
        with get_db_session() as session:
            allocations = session.query(BudgetAllocation).filter(
                BudgetAllocation.project_id == project_id
            ).all()

            return [
                {
                    "id": str(allocation.id),
                    "category": allocation.category,
                    "allocated_amount": float(allocation.allocated_amount),
                    "spent_amount": float(allocation.spent_amount),
                    "remaining_amount": float(allocation.remaining_amount),
                    "percentage_used": allocation.percentage_used,
                    "is_active": allocation.is_active,
                    "created_at": allocation.created_at.isoformat(),
                    "updated_at": allocation.updated_at.isoformat() if allocation.updated_at else None
                }
                for allocation in allocations
            ]

    @staticmethod
    def create_budget_allocation(
        project_id: UUID,
        category: str,
        allocated_amount: Decimal,
        user_id: str = None
    ) -> BudgetAllocation:
        """创建预算分配"""
        with get_db_session() as session:
            allocation = BudgetAllocation(
                id=uuid4(),
                project_id=project_id,
                category=category,
                allocated_amount=allocated_amount,
                spent_amount=Decimal('0'),
                remaining_amount=allocated_amount,
                percentage_used=Decimal('0'),
                is_active=True
            )

            session.add(allocation)
            session.commit()

            # 记录审计日志
            AuditService.log_business_action(
                action=BusinessAction.PROJECT_CREATE,
                user_id=user_id,
                resource_type="budget_allocations",
                resource_id=str(allocation.id),
                new_data={
                    "project_id": str(project_id),
                    "category": category,
                    "allocated_amount": float(allocated_amount)
                },
                description=f"创建预算分配: {category} - {allocated_amount}"
            )

            return allocation

    @staticmethod
    def get_transaction_statistics(
        project_id: UUID = None,
        account_id: UUID = None,
        start_date: date = None,
        end_date: date = None
    ) -> Dict[str, Any]:
        """获取交易统计信息"""
        with get_db_session() as session:
            query = session.query(LedgerTransaction)

            if project_id:
                query = query.filter(LedgerTransaction.project_id == project_id)
            if account_id:
                query = query.filter(LedgerTransaction.account_id == account_id)
            if start_date:
                query = query.filter(LedgerTransaction.created_at >= start_date)
            if end_date:
                query = query.filter(LedgerTransaction.created_at <= end_date)

            # 按交易类型统计
            type_stats = session.query(
                LedgerTransaction.transaction_type,
                func.count(LedgerTransaction.id).label('count'),
                func.sum(LedgerTransaction.amount).label('total_amount')
            ).filter(
                and_(
                    LedgerTransaction.status == TransactionStatus.COMPLETED,
                    *([LedgerTransaction.project_id == project_id] if project_id else []),
                    *([LedgerTransaction.account_id == account_id] if account_id else []),
                    *([LedgerTransaction.created_at >= start_date] if start_date else []),
                    *([LedgerTransaction.created_at <= end_date] if end_date else [])
                )
            ).group_by(LedgerTransaction.transaction_type).all()

            # 按状态统计
            status_stats = session.query(
                LedgerTransaction.status,
                func.count(LedgerTransaction.id).label('count'),
                func.sum(LedgerTransaction.amount).label('total_amount')
            ).filter(
                and_(
                    *([LedgerTransaction.project_id == project_id] if project_id else []),
                    *([LedgerTransaction.account_id == account_id] if account_id else []),
                    *([LedgerTransaction.created_at >= start_date] if start_date else []),
                    *([LedgerTransaction.created_at <= end_date] if end_date else [])
                )
            ).group_by(LedgerTransaction.status).all()

            return {
                "by_transaction_type": [
                    {
                        "type": stat.transaction_type.value,
                        "count": stat.count,
                        "total_amount": float(stat.total_amount) if stat.total_amount else 0.0
                    }
                    for stat in type_stats
                ],
                "by_status": [
                    {
                        "status": stat.status.value,
                        "count": stat.count,
                        "total_amount": float(stat.total_amount) if stat.total_amount else 0.0
                    }
                    for stat in status_stats
                ]
            }

    @staticmethod
    def _generate_transaction_number(transaction_type: TransactionType, session: Session) -> str:
        """生成交易流水号"""
        # 格式: TXN{YYYYMMDD}{类型代码}{4位序号}
        date_str = datetime.now().strftime("%Y%m%d")
        type_code = {
            TransactionType.TOPUP: "TP",
            TransactionType.SPEND: "SP",
            TransactionType.REFUND: "RF",
            TransactionType.FEE: "FE",
            TransactionType.ADJUSTMENT: "AD",
            TransactionType.TRANSFER: "TR"
        }[transaction_type]

        # 查询当天同类型的最大序号
        max_number = session.query(func.max(LedgerTransaction.transaction_number)).filter(
            LedgerTransaction.transaction_number.like(f"TXN{date_str}{type_code}%")
        ).scalar()

        if max_number:
            sequence = int(max_number[-4:]) + 1
        else:
            sequence = 1

        return f"TXN{date_str}{type_code}{sequence:04d}"

    @staticmethod
    def _update_account_balance(
        session: Session,
        account_id: UUID,
        project_id: UUID,
        amount: Decimal,
        transaction_type: TransactionType,
        transaction_id: UUID
    ):
        """更新账户余额"""
        # 获取或创建余额记录
        balance = session.query(AccountBalance).filter(
            and_(
                AccountBalance.account_id == account_id if account_id else AccountBalance.account_id.is_(None),
                AccountBalance.project_id == project_id if project_id else AccountBalance.project_id.is_(None)
            )
        ).first()

        if not balance:
            balance = AccountBalance(
                id=uuid4(),
                account_id=account_id,
                project_id=project_id,
                currency="USD",
                current_balance=Decimal('0'),
                available_balance=Decimal('0'),
                frozen_balance=Decimal('0'),
                total_credit=Decimal('0'),
                total_debit=Decimal('0')
            )
            session.add(balance)

        # 根据交易类型更新余额
        if transaction_type in [TransactionType.TOPUP]:
            balance.current_balance += amount
            balance.available_balance += amount
            balance.total_credit += amount
        elif transaction_type in [TransactionType.SPEND, TransactionType.FEE]:
            balance.current_balance -= amount
            balance.available_balance -= amount
            balance.total_debit += amount
        elif transaction_type == TransactionType.REFUND:
            balance.current_balance += amount
            balance.available_balance += amount
            balance.total_credit += amount
        # ADJUSTMENT 和 TRANSFER 需要根据具体情况处理

        balance.updated_at = datetime.utcnow()

    @staticmethod
    def _update_budget_allocation(
        session: Session,
        project_id: UUID,
        amount: Decimal,
        transaction_type: TransactionType
    ):
        """更新预算分配"""
        if transaction_type != TransactionType.SPEND:
            return

        # 更新默认的广告消耗预算
        allocation = session.query(BudgetAllocation).filter(
            and_(
                BudgetAllocation.project_id == project_id,
                BudgetAllocation.category == "ad_spend",
                BudgetAllocation.is_active == True
            )
            ).first()

        if allocation:
            allocation.spent_amount += amount
            allocation.remaining_amount = allocation.allocated_amount - allocation.spent_amount
            if allocation.allocated_amount > 0:
                allocation.percentage_used = (allocation.spent_amount / allocation.allocated_amount) * Decimal('100')
            allocation.updated_at = datetime.utcnow()

    @staticmethod
    def _transaction_to_dict(transaction: LedgerTransaction) -> Dict[str, Any]:
        """转换交易记录为字典"""
        return {
            "id": str(transaction.id),
            "transaction_number": transaction.transaction_number,
            "transaction_type": transaction.transaction_type.value,
            "amount": float(transaction.amount),
            "currency": transaction.currency,
            "status": transaction.status.value,
            "project_id": str(transaction.project_id) if transaction.project_id else None,
            "account_id": str(transaction.account_id) if transaction.account_id else None,
            "topup_id": str(transaction.topup_id) if transaction.topup_id else None,
            "reference_id": transaction.reference_id,
            "description": transaction.description,
            "metadata": transaction.transaction_metadata,
            "created_at": transaction.created_at.isoformat(),
            "updated_at": transaction.updated_at.isoformat() if transaction.updated_at else None
        }


def get_ledger_service() -> LedgerService:
    """获取财务服务实例"""
    return LedgerService()