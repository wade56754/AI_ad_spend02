"""
财务总账服务 (Ledger Service)

处理财务流水、账户余额、预算分配等业务逻辑

SoT 文档: LEDGER_SOT.md v1.1

合法操作说明 (Legal Operations):
=====================================

1. 交易类型 (TransactionType):
   - TOPUP: 充值入账 (增加余额)
   - SPEND: 广告消耗 (减少余额)
   - REFUND: 退款返还 (增加余额)
   - FEE: 手续费扣除 (减少余额)
   - ADJUSTMENT: 人工调账 (需审批)
   - TRANSFER: 账户间调拨 (需审批)

2. 账本规则 (Ledger Rules - 参考 LEDGER_SOT.md §2):
   - 所有资金变动必须通过本服务进行，禁止直接修改 balance 字段
   - 每笔交易生成唯一流水号 (TXN{日期}{类型}{序号})
   - 交易记录不可删除，只能通过 REVERSAL 类型冲销
   - 双账本体系: PROJECT 账本 (项目资金) + SUPPLIER 账本 (供应商成本)

3. 余额更新规则:
   - TOPUP/REFUND: +amount (贷方)
   - SPEND/FEE: -amount (借方)
   - 冻结余额 (frozen_balance): 预留审批中的金额
   - 可用余额 = current_balance - frozen_balance

4. 审计要求:
   - 所有操作记录审计日志 (AuditService)
   - 关联实体追溯: related_entity_type + related_entity_id
   - 操作人记录: user_id (system 表示系统自动)

5. 禁止操作 (Anti-patterns):
   ❌ 直接修改 ad_accounts.balance 字段
   ❌ 跳过本服务直接 INSERT ledger_transactions
   ❌ 删除或修改已完成的交易记录
   ❌ 创建负余额交易 (需先检查可用余额)

业务规则引用: BR-LED-001 ~ BR-LED-010 (BUSINESS_RULES.md v3.2)
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID, uuid4
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from backend.core.db import get_db_session
from backend.core.error_codes import ErrorCode
from backend.core.response import ApiResponse, PaginatedResponse
from backend.core.phase_config import (
    get_phase_config,
    should_block_negative_balance,
    should_lock_settlement,
    log_phase_warning,
)
from backend.models.ledger import (
    LedgerTransaction,
    AccountBalance,
    BudgetAllocation,
    TransactionType,
    TransactionStatus,
)
from backend.services.audit_service import AuditService, BusinessAction

import logging

logger = logging.getLogger(__name__)


class LedgerService:
    """
    财务总账服务类

    核心职责:
    - 创建和管理财务交易记录
    - 维护账户余额一致性
    - 管理预算分配和消耗
    - 提供交易统计和查询

    合法调用方:
    - TopupService: 充值流程
    - DailyReportService: 消耗记账
    - ReconciliationService: 对账调整
    - TransferService: 资金调拨

    禁止直接在 Router/API 层调用，必须通过业务 Service 层
    """

    @staticmethod
    def validate_spend_balance(
        account_id: UUID, amount: Decimal, project_id: UUID = None
    ) -> tuple[bool, Optional[str]]:
        """
        验证消耗前余额是否充足

        Phase-aware 行为 (MASTER.md v4.4 §8):
        - Phase 1: 余额不足时记录警告，但允许继续（负余额投放）
        - Phase 2: 余额不足时返回 False，阻止交易

        Args:
            account_id: 账户ID
            amount: 消耗金额
            project_id: 项目ID（可选）

        Returns:
            tuple[bool, Optional[str]]: (是否可继续, 消息)
        """
        with get_db_session() as session:
            # 获取当前余额
            balance = (
                session.query(AccountBalance)
                .filter(
                    and_(
                        AccountBalance.account_id == account_id
                        if account_id
                        else AccountBalance.account_id.is_(None),
                        AccountBalance.project_id == project_id
                        if project_id
                        else AccountBalance.project_id.is_(None),
                    )
                )
                .first()
            )

            if not balance:
                # 没有余额记录，视为余额为 0
                available = Decimal("0")
            else:
                available = balance.available_balance or Decimal("0")

            # 检查是否会产生负余额
            if available < amount:
                message = (
                    f"账户余额不足: 可用余额={available}, 消耗金额={amount}, "
                    f"缺口={amount - available}"
                )

                if should_block_negative_balance():
                    # Phase 2: 阻止负余额交易
                    logger.warning(f"[Phase2] {message}")
                    return False, message
                else:
                    # Phase 1: 警告但允许
                    log_phase_warning(
                        feature="negative_balance_block",
                        message=message,
                        account_id=str(account_id),
                        available_balance=str(available),
                        spend_amount=str(amount),
                    )
                    return True, f"[警告] {message}"

            return True, None

    @staticmethod
    def check_settlement_lock(transaction_date: date) -> tuple[bool, Optional[str]]:
        """
        检查交易日期是否在结算锁定期内

        Phase-aware 行为 (MASTER.md v4.4 §8):
        - Phase 1: 锁定期修改仅警告
        - Phase 2: 锁定期内禁止修改

        Args:
            transaction_date: 交易日期

        Returns:
            tuple[bool, Optional[str]]: (是否可操作, 消息)
        """
        # TODO: 实现结算期判断逻辑
        # 暂时返回允许
        if should_lock_settlement():
            logger.debug(
                f"[Phase2] Settlement lock enabled, checking date {transaction_date}"
            )
            # 这里应该检查 transaction_date 是否在已结算期间
            pass

        return True, None

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
        user_id: str = None,
        session: Session = None,
    ) -> LedgerTransaction:
        """
        创建财务交易记录

        合法操作 (BR-LED-001):
        - 必须指定 transaction_type (6种类型之一)
        - amount 必须为正数 (方向由 type 决定)
        - 必须关联 project_id 或 account_id

        副作用:
        - 自动更新关联账户余额
        - 自动更新预算分配 (SPEND 类型)
        - 记录审计日志

        Args:
            session: 可选的数据库会话。如果提供，将使用该会话而不是创建新会话。
                     用于测试和需要在同一事务中执行多个操作的场景。
        """
        # 如果提供了 session，使用它；否则使用 get_db_session()
        if session is not None:
            return LedgerService._create_transaction_impl(
                session=session,
                transaction_type=transaction_type,
                amount=amount,
                currency=currency,
                project_id=project_id,
                account_id=account_id,
                topup_id=topup_id,
                reference_id=reference_id,
                description=description,
                metadata=metadata,
                user_id=user_id,
                should_commit=False,  # 由调用者控制提交
            )

        with get_db_session() as session:
            # 生成交易流水号
            transaction_number = LedgerService._generate_transaction_number(
                transaction_type, session
            )

            # 创建交易记录
            # NOTE: id 使用 BigInteger autoincrement，不需要手动设置
            # transaction_type 和 status 是 String 列，需要传 .value
            # transaction_metadata 是 Text 列，需要序列化为 JSON 字符串
            transaction = LedgerTransaction(
                transaction_number=transaction_number,
                transaction_type=transaction_type.value,
                amount=amount,
                currency=currency,
                status=TransactionStatus.PENDING.value,
                project_id=project_id,
                account_id=account_id,
                topup_id=topup_id,
                reference_id=reference_id,
                description=description,
                transaction_metadata=json.dumps(metadata) if metadata else None,
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
                transaction_id=transaction.id,
            )

            # 更新预算分配
            if project_id and transaction_type in [TransactionType.SPEND]:
                LedgerService._update_budget_allocation(
                    session=session,
                    project_id=project_id,
                    amount=amount,
                    transaction_type=transaction_type,
                )

            session.commit()

            # 记录审计日志
            AuditService.log_business_action(
                action=BusinessAction.TOPUP_SUBMIT
                if transaction_type == TransactionType.TOPUP
                else BusinessAction.PROJECT_CREATE,
                user_id=user_id or "system",
                resource_type="ledger_transactions",
                resource_id=str(transaction.id),
                new_data={
                    "transaction_number": transaction_number,
                    "transaction_type": transaction_type.value,
                    "amount": float(amount),
                    "currency": currency,
                    "project_id": str(project_id) if project_id else None,
                    "account_id": str(account_id) if account_id else None,
                },
                description=f"创建财务交易: {transaction_number} - {transaction_type.value} {amount}",
            )

            return transaction

    @staticmethod
    def _create_transaction_impl(
        session: Session,
        transaction_type: TransactionType,
        amount: Decimal,
        currency: str = "USD",
        project_id: UUID = None,
        account_id: UUID = None,
        topup_id: UUID = None,
        reference_id: str = None,
        description: str = None,
        metadata: Dict[str, Any] = None,
        user_id: str = None,
        should_commit: bool = True,
    ) -> LedgerTransaction:
        """
        创建财务交易记录的内部实现（可测试版本）

        用于需要传入自定义 session 的场景（如测试）。
        """
        # 生成交易流水号
        transaction_number = LedgerService._generate_transaction_number(
            transaction_type, session
        )

        # 创建交易记录
        # NOTE: id 使用 BigInteger autoincrement，不需要手动设置
        # transaction_type 和 status 是 String 列，需要传 .value
        # transaction_metadata 是 Text 列，需要序列化为 JSON 字符串
        transaction = LedgerTransaction(
            transaction_number=transaction_number,
            transaction_type=transaction_type.value,
            amount=amount,
            currency=currency,
            status=TransactionStatus.PENDING.value,
            project_id=project_id,
            account_id=account_id,
            topup_id=topup_id,
            reference_id=reference_id,
            description=description,
            transaction_metadata=json.dumps(metadata) if metadata else None,
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
            transaction_id=transaction.id,
        )

        # 更新预算分配
        if project_id and transaction_type in [TransactionType.SPEND]:
            LedgerService._update_budget_allocation(
                session=session,
                project_id=project_id,
                amount=amount,
                transaction_type=transaction_type,
            )

        if should_commit:
            session.commit()

        return transaction

    @staticmethod
    def update_transaction_status(
        transaction_id: UUID,
        status: TransactionStatus,
        user_id: str = None,
        note: str = None,
    ) -> Optional[LedgerTransaction]:
        """更新交易状态"""
        with get_db_session() as session:
            transaction = (
                session.query(LedgerTransaction)
                .filter(LedgerTransaction.id == transaction_id)
                .first()
            )

            if not transaction:
                return None

            old_status = transaction.status  # 现在是字符串
            new_status_value = status.value  # 转换为字符串
            transaction.status = new_status_value
            transaction.updated_at = datetime.utcnow()

            if note:
                # transaction_metadata 是 JSON 字符串，需要解析和序列化
                metadata = {}
                if transaction.transaction_metadata:
                    try:
                        metadata = json.loads(transaction.transaction_metadata)
                    except (json.JSONDecodeError, TypeError):
                        metadata = {}
                metadata["status_note"] = note
                transaction.transaction_metadata = json.dumps(metadata)

            # 如果状态变为完成，重新更新余额
            # old_status 是字符串，需要与字符串比较
            if (
                new_status_value == TransactionStatus.COMPLETED.value
                and old_status != TransactionStatus.COMPLETED.value
            ):
                # transaction_type 现在是字符串，需要转换为 Enum
                txn_type = TransactionType(transaction.transaction_type)
                LedgerService._update_account_balance(
                    session=session,
                    account_id=transaction.account_id,
                    project_id=transaction.project_id,
                    amount=transaction.amount,
                    transaction_type=txn_type,
                    transaction_id=transaction.id,
                )

            session.commit()

            # 记录审计日志
            # transaction_type 现在是字符串
            AuditService.log_business_action(
                action=BusinessAction.TOPUP_APPROVE_FINANCE
                if transaction.transaction_type == TransactionType.TOPUP.value
                else BusinessAction.PROJECT_UPDATE,
                user_id=user_id,
                resource_type="ledger_transactions",
                resource_id=str(transaction_id),
                old_data={"status": old_status},  # 已经是字符串
                new_data={"status": new_status_value, "note": note},
                description=f"更新交易状态: {transaction.transaction_number} - {old_status} -> {new_status_value}",
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
        size: int = 20,
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
                # transaction_type 存储为字符串，需要用 .value 比较
                query = query.filter(
                    LedgerTransaction.transaction_type == transaction_type.value
                )
            if status:
                # status 存储为字符串，需要用 .value 比较
                query = query.filter(LedgerTransaction.status == status.value)
            if start_date:
                query = query.filter(LedgerTransaction.created_at >= start_date)
            if end_date:
                query = query.filter(LedgerTransaction.created_at <= end_date)

            # 获取总数
            total = query.count()

            # 应用分页
            offset = (page - 1) * size
            transactions = (
                query.order_by(desc(LedgerTransaction.created_at))
                .offset(offset)
                .limit(size)
                .all()
            )

            return PaginatedResponse(
                items=[LedgerService._transaction_to_dict(t) for t in transactions],
                total=total,
                page=page,
                size=size,
                pages=(total + size - 1) // size,
            )

    @staticmethod
    def get_account_balance(
        account_id: UUID = None, project_id: UUID = None
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
                "last_updated": balance.updated_at.isoformat()
                if balance.updated_at
                else None,
            }

    @staticmethod
    def get_project_budget_allocation(project_id: UUID) -> List[Dict[str, Any]]:
        """获取项目预算分配"""
        with get_db_session() as session:
            allocations = (
                session.query(BudgetAllocation)
                .filter(BudgetAllocation.project_id == project_id)
                .all()
            )

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
                    "updated_at": allocation.updated_at.isoformat()
                    if allocation.updated_at
                    else None,
                }
                for allocation in allocations
            ]

    @staticmethod
    def create_budget_allocation(
        project_id: UUID, category: str, allocated_amount: Decimal, user_id: str = None
    ) -> BudgetAllocation:
        """创建预算分配"""
        with get_db_session() as session:
            # NOTE: id 使用 BigInteger autoincrement，不需要手动设置
            allocation = BudgetAllocation(
                project_id=project_id,
                category=category,
                allocated_amount=allocated_amount,
                spent_amount=Decimal("0"),
                remaining_amount=allocated_amount,
                percentage_used=Decimal("0"),
                is_active=True,
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
                    "allocated_amount": float(allocated_amount),
                },
                description=f"创建预算分配: {category} - {allocated_amount}",
            )

            return allocation

    @staticmethod
    def get_transaction_statistics(
        project_id: UUID = None,
        account_id: UUID = None,
        start_date: date = None,
        end_date: date = None,
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
            # status 存储为字符串，需要用 .value 比较
            type_stats = (
                session.query(
                    LedgerTransaction.transaction_type,
                    func.count(LedgerTransaction.id).label("count"),
                    func.sum(LedgerTransaction.amount).label("total_amount"),
                )
                .filter(
                    and_(
                        LedgerTransaction.status == TransactionStatus.COMPLETED.value,
                        *(
                            [LedgerTransaction.project_id == project_id]
                            if project_id
                            else []
                        ),
                        *(
                            [LedgerTransaction.account_id == account_id]
                            if account_id
                            else []
                        ),
                        *(
                            [LedgerTransaction.created_at >= start_date]
                            if start_date
                            else []
                        ),
                        *(
                            [LedgerTransaction.created_at <= end_date]
                            if end_date
                            else []
                        ),
                    )
                )
                .group_by(LedgerTransaction.transaction_type)
                .all()
            )

            # 按状态统计
            status_stats = (
                session.query(
                    LedgerTransaction.status,
                    func.count(LedgerTransaction.id).label("count"),
                    func.sum(LedgerTransaction.amount).label("total_amount"),
                )
                .filter(
                    and_(
                        *(
                            [LedgerTransaction.project_id == project_id]
                            if project_id
                            else []
                        ),
                        *(
                            [LedgerTransaction.account_id == account_id]
                            if account_id
                            else []
                        ),
                        *(
                            [LedgerTransaction.created_at >= start_date]
                            if start_date
                            else []
                        ),
                        *(
                            [LedgerTransaction.created_at <= end_date]
                            if end_date
                            else []
                        ),
                    )
                )
                .group_by(LedgerTransaction.status)
                .all()
            )

            return {
                "by_transaction_type": [
                    {
                        # transaction_type 现在存储为字符串
                        "type": stat.transaction_type,
                        "count": stat.count,
                        "total_amount": float(stat.total_amount)
                        if stat.total_amount
                        else 0.0,
                    }
                    for stat in type_stats
                ],
                "by_status": [
                    {
                        # status 现在存储为字符串
                        "status": stat.status,
                        "count": stat.count,
                        "total_amount": float(stat.total_amount)
                        if stat.total_amount
                        else 0.0,
                    }
                    for stat in status_stats
                ],
            }

    @staticmethod
    def _generate_transaction_number(
        transaction_type: TransactionType, session: Session
    ) -> str:
        """生成交易流水号"""
        # 格式: TXN{YYYYMMDD}{类型代码}{4位序号}
        date_str = datetime.now().strftime("%Y%m%d")
        type_code = {
            TransactionType.TOPUP: "TP",
            TransactionType.SPEND: "SP",
            TransactionType.REFUND: "RF",
            TransactionType.FEE: "FE",
            TransactionType.ADJUSTMENT: "AD",
            TransactionType.TRANSFER: "TR",
        }[transaction_type]

        # 查询当天同类型的最大序号
        max_number = (
            session.query(func.max(LedgerTransaction.transaction_number))
            .filter(
                LedgerTransaction.transaction_number.like(f"TXN{date_str}{type_code}%")
            )
            .scalar()
        )

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
        transaction_id: UUID,
    ):
        """
        更新账户余额 (内部方法)

        合法操作 (BR-LED-003):
        - 只能通过 create_transaction 间接调用
        - 根据 transaction_type 自动决定加减方向
        - 同时更新 current_balance 和 available_balance

        余额计算规则:
        - TOPUP/REFUND: +amount (贷方增加)
        - SPEND/FEE: -amount (借方减少)
        - ADJUSTMENT/TRANSFER: 根据具体场景处理
        """
        # 获取或创建余额记录
        balance = (
            session.query(AccountBalance)
            .filter(
                and_(
                    AccountBalance.account_id == account_id
                    if account_id
                    else AccountBalance.account_id.is_(None),
                    AccountBalance.project_id == project_id
                    if project_id
                    else AccountBalance.project_id.is_(None),
                )
            )
            .first()
        )

        if not balance:
            # NOTE: id 使用 BigInteger autoincrement，不需要手动设置
            balance = AccountBalance(
                account_id=account_id,
                project_id=project_id,
                currency="USD",
                current_balance=Decimal("0"),
                available_balance=Decimal("0"),
                frozen_balance=Decimal("0"),
                total_credit=Decimal("0"),
                total_debit=Decimal("0"),
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
        transaction_type: TransactionType,
    ):
        """更新预算分配"""
        if transaction_type != TransactionType.SPEND:
            return

        # 更新默认的广告消耗预算
        allocation = (
            session.query(BudgetAllocation)
            .filter(
                and_(
                    BudgetAllocation.project_id == project_id,
                    BudgetAllocation.category == "ad_spend",
                    BudgetAllocation.is_active == True,
                )
            )
            .first()
        )

        if allocation:
            allocation.spent_amount += amount
            allocation.remaining_amount = (
                allocation.allocated_amount - allocation.spent_amount
            )
            if allocation.allocated_amount > 0:
                allocation.percentage_used = (
                    allocation.spent_amount / allocation.allocated_amount
                ) * Decimal("100")
            allocation.updated_at = datetime.utcnow()

    @staticmethod
    def _transaction_to_dict(transaction: LedgerTransaction) -> Dict[str, Any]:
        """转换交易记录为字典"""
        # transaction_type 和 status 现在存储为字符串，不再是 Enum 对象
        # transaction_metadata 存储为 JSON 字符串，需要反序列化
        metadata = transaction.transaction_metadata
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                pass

        return {
            "id": str(transaction.id),
            "transaction_number": transaction.transaction_number,
            "transaction_type": transaction.transaction_type,  # 已经是字符串
            "amount": float(transaction.amount),
            "currency": transaction.currency,
            "status": transaction.status,  # 已经是字符串
            "project_id": str(transaction.project_id)
            if transaction.project_id
            else None,
            "account_id": str(transaction.account_id)
            if transaction.account_id
            else None,
            "topup_id": str(transaction.topup_id) if transaction.topup_id else None,
            "reference_id": transaction.reference_id,
            "description": transaction.description,
            "metadata": metadata,
            "created_at": transaction.created_at.isoformat(),
            "updated_at": transaction.updated_at.isoformat()
            if transaction.updated_at
            else None,
        }


def get_ledger_service() -> LedgerService:
    """获取财务服务实例"""
    return LedgerService()


# ========== Phase 3 集成: Event → Ledger ==========


def create_ledger_from_event(event, db):
    """
    从 FinancialEvent 创建分录 (Phase 3 新接口)

    这是 LedgerService 与 LedgerPostingService 的集成点。
    调用 LedgerPostingService.post_event 来处理事件过账。

    Args:
        event: FinancialEvent 对象
        db: 数据库会话

    Returns:
        List[LedgerEntry]: 生成的分录列表

    Usage:
        from backend.services.ledger_service import create_ledger_from_event
        entries = create_ledger_from_event(event, db)
    """
    from backend.services.ledger_posting_service import LedgerPostingService

    return LedgerPostingService.post_event(event, db)
