"""
账本过账服务 (Ledger Posting Service)

Phase 3: Event → Ledger 映射实现

职责:
1. 将 FinancialEvent 过账到 LedgerEntry
2. 根据事件类型应用映射规则
3. 生成多条分录并更新余额
4. 支持事件冲正 (reverse)

SoT 文档:
- LEDGER_SOT.md v1.1 (账本规则)
- FINANCIAL_SOT_DESIGN.md v1.0 (事件驱动架构)
- STATE_MACHINE.md v2.6 (事件状态机)
- ERROR_CODES_SOT.md v2.1 (错误码)

Author: Claude Code (AI 代码工厂)
Version: 1.0
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.models.finance.financial_event import FinancialEvent, EventType, EventStatus
from backend.models.finance.ledger import LedgerEntry
from backend.models.enums import LedgerEntryType
from backend.core.error_codes import BusinessErrorCodes, StateErrorCodes
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    StateTransitionError,
    ResourceNotFoundError
)

logger = logging.getLogger(__name__)


class PostingDirection:
    """过账方向常量"""
    DEBIT = "DEBIT"    # 借方 (减少余额)
    CREDIT = "CREDIT"  # 贷方 (增加余额)


class EntityType:
    """账本实体类型常量"""
    SUPPLIER = "SUPPLIER"
    PROJECT = "PROJECT"
    ACCOUNT = "ACCOUNT"
    TEAM = "TEAM"


class LedgerPostingService:
    """
    账本过账服务

    核心功能:
    - post_event: 将事件过账到账本
    - reverse_event: 冲正已入账事件
    - validate_event_for_posting: 验证事件是否可入账

    映射规则 (FINANCIAL_REFACTOR_PLAN.md):
    - SPEND: SUPPLIER(DEBIT) + ACCOUNT(DEBIT)
    - TOPUP: SUPPLIER(CREDIT) + TEAM(DEBIT)
    - PAYMENT: PROJECT(CREDIT) + TEAM(CREDIT)
    - TRANSFER: FROM_ENTITY(DEBIT) + TO_ENTITY(CREDIT)
    - FEE: SUPPLIER(DEBIT)
    - REFUND: SUPPLIER(CREDIT)
    - ADJUSTMENT: 根据 payload 决定
    """

    # 事件类型到分录的映射规则
    # 格式: event_type -> [(entity_type, entity_field, direction, amount_field, entry_type)]
    MAPPING_RULES: Dict[str, List[Tuple[str, str, str, str, str]]] = {
        EventType.SPEND.value: [
            # SPEND 事件: 供应商成本增加 (DEBIT)
            (EntityType.SUPPLIER, 'supplier_id', PostingDirection.DEBIT, 'gross_amount', LedgerEntryType.COST.value),
            # 账户消耗记录 (DEBIT)
            (EntityType.ACCOUNT, 'ad_account_id', PostingDirection.DEBIT, 'gross_amount', LedgerEntryType.COST.value),
        ],
        EventType.TOPUP.value: [
            # TOPUP 事件: 供应商余额增加 (CREDIT)
            (EntityType.SUPPLIER, 'supplier_id', PostingDirection.CREDIT, 'gross_amount', LedgerEntryType.TOPUP.value),
        ],
        EventType.PAYMENT.value: [
            # PAYMENT 事件: 项目收入 (CREDIT)
            (EntityType.PROJECT, 'project_id', PostingDirection.CREDIT, 'amount', LedgerEntryType.REVENUE.value),
        ],
        EventType.TRANSFER.value: [
            # TRANSFER 事件: 需要根据 payload 中的 from/to 信息处理
            # 这里使用特殊标记，在 _create_transfer_entries 中单独处理
        ],
        EventType.FEE.value: [
            # FEE 事件: 供应商手续费 (DEBIT)
            (EntityType.SUPPLIER, 'supplier_id', PostingDirection.DEBIT, 'fee_amount', LedgerEntryType.COST.value),
        ],
        EventType.REFUND.value: [
            # REFUND 事件: 供应商退款 (CREDIT)
            (EntityType.SUPPLIER, 'supplier_id', PostingDirection.CREDIT, 'amount', LedgerEntryType.TOPUP.value),
        ],
        EventType.ADJUSTMENT.value: [
            # ADJUSTMENT 事件: 根据 payload.direction 决定
            # 在 _create_adjustment_entries 中单独处理
        ],
    }

    @staticmethod
    def validate_event_for_posting(event: FinancialEvent) -> Tuple[bool, Optional[str]]:
        """
        验证事件是否可以入账

        Args:
            event: 财务事件对象

        Returns:
            (is_valid, error_message): 是否有效及错误消息

        业务规则:
        - 只有 CONFIRMED 状态的事件才能入账
        - 事件必须有有效的金额
        - 必须关联有效的实体 (supplier_id/project_id/ad_account_id)
        """
        # 检查状态
        if event.event_status != EventStatus.CONFIRMED.value:
            return False, f"事件状态必须为 confirmed，当前状态: {event.event_status}"

        # 检查金额
        if event.amount is None or event.amount <= 0:
            return False, f"事件金额无效: {event.amount}"

        # 检查实体关联
        event_type = event.event_type
        if event_type == EventType.SPEND.value:
            if not event.supplier_id:
                return False, "SPEND 事件必须关联供应商"
            if not event.ad_account_id:
                return False, "SPEND 事件必须关联广告账户"
        elif event_type == EventType.TOPUP.value:
            if not event.supplier_id:
                return False, "TOPUP 事件必须关联供应商"
        elif event_type == EventType.PAYMENT.value:
            if not event.project_id:
                return False, "PAYMENT 事件必须关联项目"
        elif event_type == EventType.TRANSFER.value:
            payload = event.payload or {}
            if not payload.get('from_account_id') or not payload.get('to_account_id'):
                return False, "TRANSFER 事件必须指定源账户和目标账户"

        return True, None

    @classmethod
    def post_event(
        cls,
        event: FinancialEvent,
        db: Session,
        user_id: Optional[UUID] = None
    ) -> List[LedgerEntry]:
        """
        将事件过账到账本

        Args:
            event: 待过账的财务事件 (必须是 CONFIRMED 状态)
            db: 数据库会话
            user_id: 操作用户ID

        Returns:
            List[LedgerEntry]: 生成的分录列表

        Raises:
            StateTransitionError: 事件状态不允许入账
            BusinessLogicError: 业务规则验证失败

        业务流程:
        1. 验证事件状态 (必须是 CONFIRMED)
        2. 根据 event_type 获取映射规则
        3. 生成多条 ledger_entries
        4. 更新事件状态为 POSTED
        5. 提交事务
        """
        logger.info(f"开始过账事件: {event.id}, 类型: {event.event_type}")

        # 1. 验证事件
        is_valid, error_msg = cls.validate_event_for_posting(event)
        if not is_valid:
            logger.error(f"事件验证失败: {error_msg}")
            raise BusinessLogicError(
                code=BusinessErrorCodes.LEDGER_CREATE_ERROR.code,
                message=error_msg
            )

        # 2. 检查幂等性 - 是否已存在相关分录
        existing_entries = db.query(LedgerEntry).filter(
            LedgerEntry.event_id == event.id
        ).first()
        if existing_entries:
            logger.warning(f"事件 {event.id} 已存在分录，跳过重复过账")
            return db.query(LedgerEntry).filter(LedgerEntry.event_id == event.id).all()

        # 3. 根据事件类型生成分录
        entries = []
        event_type = event.event_type

        if event_type == EventType.TRANSFER.value:
            entries = cls._create_transfer_entries(event, db)
        elif event_type == EventType.ADJUSTMENT.value:
            entries = cls._create_adjustment_entries(event, db)
        else:
            entries = cls._create_standard_entries(event, db)

        # 4. 保存分录
        for entry in entries:
            db.add(entry)

        # 5. 更新事件状态为 POSTED
        event.event_status = EventStatus.POSTED.value
        event.posted_at = datetime.utcnow()

        db.flush()

        logger.info(f"事件 {event.id} 过账成功，生成 {len(entries)} 条分录")
        return entries

    @classmethod
    def _create_standard_entries(
        cls,
        event: FinancialEvent,
        db: Session
    ) -> List[LedgerEntry]:
        """
        创建标准分录 (非 TRANSFER/ADJUSTMENT 类型)

        根据 MAPPING_RULES 生成分录
        """
        entries = []
        rules = cls.MAPPING_RULES.get(event.event_type, [])

        for entity_type, entity_field, direction, amount_field, entry_type in rules:
            # 获取实体ID
            entity_id = getattr(event, entity_field, None)
            if not entity_id:
                logger.warning(f"事件 {event.id} 缺少 {entity_field}，跳过该分录")
                continue

            # 获取金额
            amount = cls._get_amount(event, amount_field)
            if amount is None or amount == 0:
                logger.warning(f"事件 {event.id} 金额为 0，跳过该分录")
                continue

            # 根据方向调整金额符号
            # DEBIT (借方): 负数 (减少余额)
            # CREDIT (贷方): 正数 (增加余额)
            signed_amount = amount if direction == PostingDirection.CREDIT else -amount

            # 创建分录
            entry = cls._build_ledger_entry(
                event=event,
                entity_type=entity_type,
                entity_id=str(entity_id),
                entry_type=entry_type,
                amount=signed_amount,
                direction=direction,
                db=db
            )
            entries.append(entry)

        return entries

    @classmethod
    def _create_transfer_entries(
        cls,
        event: FinancialEvent,
        db: Session
    ) -> List[LedgerEntry]:
        """
        创建转账分录 (TRANSFER 类型)

        TRANSFER 事件需要生成两条分录:
        - TRANSFER_OUT: 源账户减少 (DEBIT)
        - TRANSFER_IN: 目标账户增加 (CREDIT)
        """
        entries = []
        payload = event.payload or {}

        from_account_id = payload.get('from_account_id')
        to_account_id = payload.get('to_account_id')
        amount = event.amount

        if not from_account_id or not to_account_id:
            raise BusinessLogicError(
                code=BusinessErrorCodes.LEDGER_CREATE_ERROR.code,
                message="TRANSFER 事件缺少源账户或目标账户"
            )

        # 源账户转出 (DEBIT, 负数)
        out_entry = cls._build_ledger_entry(
            event=event,
            entity_type=EntityType.ACCOUNT,
            entity_id=str(from_account_id),
            entry_type=LedgerEntryType.TRANSFER_OUT.value,
            amount=-amount,
            direction=PostingDirection.DEBIT,
            db=db,
            notes=f"转出到账户 {to_account_id}"
        )
        entries.append(out_entry)

        # 目标账户转入 (CREDIT, 正数)
        in_entry = cls._build_ledger_entry(
            event=event,
            entity_type=EntityType.ACCOUNT,
            entity_id=str(to_account_id),
            entry_type=LedgerEntryType.TRANSFER_IN.value,
            amount=amount,
            direction=PostingDirection.CREDIT,
            db=db,
            notes=f"从账户 {from_account_id} 转入"
        )
        entries.append(in_entry)

        return entries

    @classmethod
    def _create_adjustment_entries(
        cls,
        event: FinancialEvent,
        db: Session
    ) -> List[LedgerEntry]:
        """
        创建调整分录 (ADJUSTMENT 类型)

        ADJUSTMENT 事件根据 payload.direction 决定方向
        """
        entries = []
        payload = event.payload or {}

        direction = payload.get('direction', PostingDirection.CREDIT)
        entity_type = payload.get('entity_type', EntityType.SUPPLIER)
        entity_id = payload.get('entity_id') or event.supplier_id or event.project_id

        if not entity_id:
            raise BusinessLogicError(
                code=BusinessErrorCodes.LEDGER_CREATE_ERROR.code,
                message="ADJUSTMENT 事件缺少实体ID"
            )

        amount = event.amount
        signed_amount = amount if direction == PostingDirection.CREDIT else -amount

        # 根据方向选择 entry_type
        if entity_type == EntityType.PROJECT:
            entry_type = LedgerEntryType.REVENUE.value
        else:
            entry_type = LedgerEntryType.COST.value if direction == PostingDirection.DEBIT else LedgerEntryType.TOPUP.value

        entry = cls._build_ledger_entry(
            event=event,
            entity_type=entity_type,
            entity_id=str(entity_id),
            entry_type=entry_type,
            amount=signed_amount,
            direction=direction,
            db=db,
            notes=payload.get('reason', '人工调整')
        )
        entries.append(entry)

        return entries

    @classmethod
    def reverse_event(
        cls,
        event: FinancialEvent,
        reason: str,
        db: Session,
        user_id: Optional[UUID] = None
    ) -> List[LedgerEntry]:
        """
        冲正事件 (生成反向分录)

        Args:
            event: 待冲正的财务事件 (必须是 POSTED 状态)
            reason: 冲正原因
            db: 数据库会话
            user_id: 操作用户ID

        Returns:
            List[LedgerEntry]: 生成的冲正分录列表

        Raises:
            StateTransitionError: 事件状态不允许冲正
            BusinessLogicError: 业务规则验证失败

        业务流程:
        1. 验证事件状态 (必须是 POSTED)
        2. 查找原始分录
        3. 生成反向分录 (金额取反, entry_type=REVERSAL)
        4. 更新事件状态为 REVERSED
        """
        logger.info(f"开始冲正事件: {event.id}, 原因: {reason}")

        # 1. 验证状态
        if not event.can_reverse:
            raise StateTransitionError(
                error_code=StateErrorCodes.FORBIDDEN_TRANSITION.code,
                message=f"事件状态 {event.event_status} 不允许冲正，只有 POSTED 状态可以冲正"
            )

        # 2. 查找原始分录
        original_entries = db.query(LedgerEntry).filter(
            LedgerEntry.event_id == event.id
        ).all()

        if not original_entries:
            raise BusinessLogicError(
                code=BusinessErrorCodes.TRANSACTION_NOT_FOUND.code,
                message=f"未找到事件 {event.id} 的原始分录"
            )

        # 3. 生成反向分录
        reversal_entries = []
        for original in original_entries:
            # 生成冲正幂等键
            reversal_key = f"REVERSAL:{original.idempotency_key or event.idempotency_key}:{datetime.utcnow().timestamp()}"

            reversal = LedgerEntry(
                ad_account_id=original.ad_account_id,
                entry_type=LedgerEntryType.REVERSAL.value,
                amount=-original.amount,  # 金额取反
                reference_id=original.id,
                notes=f"冲正原因: {reason} | 来源: ledger_entry_reversal",
                entry_date=datetime.utcnow(),
                entity_type=original.entity_type,
                entity_id=original.entity_id,
                event_id=event.id,
                idempotency_key=reversal_key,
                direction=PostingDirection.CREDIT if original.direction == PostingDirection.DEBIT else PostingDirection.DEBIT
            )
            db.add(reversal)
            reversal_entries.append(reversal)

        # 4. 更新事件状态
        event.event_status = EventStatus.REVERSED.value

        db.flush()

        logger.info(f"事件 {event.id} 冲正成功，生成 {len(reversal_entries)} 条冲正分录")
        return reversal_entries

    @classmethod
    def _build_ledger_entry(
        cls,
        event: FinancialEvent,
        entity_type: str,
        entity_id: str,
        entry_type: str,
        amount: Decimal,
        direction: str,
        db: Session,
        notes: str = None
    ) -> LedgerEntry:
        """
        构建账本分录对象

        Args:
            event: 关联的财务事件
            entity_type: 实体类型 (SUPPLIER/PROJECT/ACCOUNT/TEAM)
            entity_id: 实体ID
            entry_type: 分录类型 (REVENUE/COST/TOPUP/TRANSFER_OUT/TRANSFER_IN/REVERSAL)
            amount: 金额 (已含正负号)
            direction: 方向 (DEBIT/CREDIT)
            db: 数据库会话
            notes: 备注

        Returns:
            LedgerEntry: 分录对象
        """
        # 生成幂等键
        idempotency_key = f"{event.idempotency_key}:{entity_type}:{entity_id}"

        # 获取 ad_account_id (如果适用)
        ad_account_id = event.ad_account_id

        entry = LedgerEntry(
            ad_account_id=ad_account_id or 0,  # 暂时使用 0，后续优化
            entry_type=entry_type,
            amount=amount,
            reference_id=None,
            notes=notes or f"{event.event_type} 事件自动生成 | 来源: financial_event:{event.event_type}",
            entry_date=event.event_date or datetime.utcnow().date(),
            entity_type=entity_type,
            entity_id=entity_id,
            event_id=event.id,
            idempotency_key=idempotency_key,
            direction=direction
        )

        return entry

    @staticmethod
    def _get_amount(event: FinancialEvent, amount_field: str) -> Decimal:
        """
        获取事件的金额字段值

        Args:
            event: 财务事件
            amount_field: 金额字段名 (amount/fee_amount/gross_amount)

        Returns:
            Decimal: 金额值
        """
        if amount_field == 'gross_amount':
            return event.calculate_gross_amount()
        return getattr(event, amount_field, Decimal('0')) or Decimal('0')

    # ========== 批量操作方法 ==========

    @classmethod
    def post_events_batch(
        cls,
        event_ids: List[UUID],
        db: Session,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        批量过账事件

        Args:
            event_ids: 事件ID列表
            db: 数据库会话
            user_id: 操作用户ID

        Returns:
            Dict: 批量处理结果
            {
                "total": 10,
                "success": 8,
                "failed": 2,
                "entries_created": 16,
                "errors": [{"event_id": "xxx", "error": "xxx"}]
            }
        """
        result = {
            "total": len(event_ids),
            "success": 0,
            "failed": 0,
            "entries_created": 0,
            "errors": []
        }

        for event_id in event_ids:
            try:
                event = db.query(FinancialEvent).filter(
                    FinancialEvent.id == event_id
                ).first()

                if not event:
                    result["failed"] += 1
                    result["errors"].append({
                        "event_id": str(event_id),
                        "error": "事件不存在"
                    })
                    continue

                entries = cls.post_event(event, db, user_id)
                result["success"] += 1
                result["entries_created"] += len(entries)

            except Exception as e:
                result["failed"] += 1
                result["errors"].append({
                    "event_id": str(event_id),
                    "error": str(e)
                })
                logger.error(f"批量过账事件 {event_id} 失败: {e}")

        return result

    @classmethod
    def get_event_entries(
        cls,
        event_id: UUID,
        db: Session
    ) -> List[LedgerEntry]:
        """
        获取事件关联的所有分录

        Args:
            event_id: 事件ID
            db: 数据库会话

        Returns:
            List[LedgerEntry]: 分录列表
        """
        return db.query(LedgerEntry).filter(
            LedgerEntry.event_id == event_id
        ).order_by(LedgerEntry.created_at).all()


# ========== 服务实例获取函数 ==========

def get_ledger_posting_service() -> LedgerPostingService:
    """获取账本过账服务实例"""
    return LedgerPostingService()
