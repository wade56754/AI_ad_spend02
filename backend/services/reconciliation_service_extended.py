"""
对账管理扩展服务
处理对账批次、对账详情、差异处理等完整对账流程

.. deprecated::
    此模块计划在 v2.5 中合并到 reconciliation_service.py。
    请优先使用 reconciliation_service.py 中的 ReconciliationService。
    详见: 重构任务 P1-001
"""
import warnings

warnings.warn(
    "reconciliation_service_extended.py 已计划废弃。"
    "请使用 reconciliation_service.py 中的 ReconciliationService。",
    DeprecationWarning,
    stacklevel=2
)

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, case

from backend.core.db import get_db_session
from backend.core.error_codes import ErrorCode
from backend.core.response import ApiResponse, PaginatedResponse
from backend.models.reconciliation_extended import (
    ReconciliationBatch, ReconciliationDetail, ReconciliationDifference,
    ReconciliationStatus, DifferenceStatus, DifferenceType
)
from backend.services.audit_service import AuditService, BusinessAction


class ReconciliationServiceExtended:
    """对账管理扩展服务类"""

    @staticmethod
    def create_reconciliation_batch(
        name: str,
        start_date: date,
        end_date: date,
        project_ids: List[UUID] = None,
        description: str = None,
        user_id: str = None
    ) -> ReconciliationBatch:
        """创建对账批次"""
        with get_db_session() as session:
            batch = ReconciliationBatch(
                id=uuid4(),
                name=name,
                start_date=start_date,
                end_date=end_date,
                status=ReconciliationStatus.PENDING,
                project_ids=project_ids or [],
                description=description,
                created_by=user_id
            )

            session.add(batch)
            session.commit()

            # 记录审计日志
            AuditService.log_reconciliation_action(
                action=BusinessAction.RECONCILIATION_CREATE,
                reconciliation_id=str(batch.id),
                user_id=user_id,
                reconciliation_data={
                    "name": name,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "project_ids": [str(pid) for pid in project_ids] if project_ids else []
                }
            )

            return batch

    @staticmethod
    def process_reconciliation_batch(
        batch_id: UUID,
        user_id: str = None
    ) -> ReconciliationBatch:
        """执行对账批次"""
        with get_db_session() as session:
            batch = session.query(ReconciliationBatch).filter(
                ReconciliationBatch.id == batch_id
            ).first()

            if not batch:
                raise ValueError("对账批次不存在")

            if batch.status != ReconciliationStatus.PENDING:
                raise ValueError(f"对账批次状态不正确: {batch.status.value}")

            # 更新批次状态为处理中
            batch.status = ReconciliationStatus.PROCESSING
            batch.started_at = datetime.utcnow()
            session.commit()

            try:
                # 执行对账逻辑
                differences = ReconciliationServiceExtended._perform_reconciliation(
                    session=session,
                    batch=batch
                )

                # 更新批次状态和统计信息
                batch.status = ReconciliationStatus.COMPLETED
                batch.completed_at = datetime.utcnow()
                batch.total_records = len(differences)
                batch.difference_count = len([d for d in differences if d.difference_amount != 0])
                batch.matched_count = len(differences) - batch.difference_count

                session.commit()

                # 记录审计日志
                AuditService.log_reconciliation_action(
                    action=BusinessAction.RECONCILIATION_PROCESS,
                    reconciliation_id=str(batch_id),
                    user_id=user_id,
                    reconciliation_data={
                        "total_records": batch.total_records,
                        "difference_count": batch.difference_count,
                        "matched_count": batch.matched_count
                    },
                    difference_amount=float(sum(d.difference_amount for d in differences))
                )

                return batch

            except Exception as e:
                # 对账失败，更新状态
                batch.status = ReconciliationStatus.FAILED
                batch.error_message = str(e)
                batch.completed_at = datetime.utcnow()
                session.commit()
                raise

    @staticmethod
    def get_reconciliation_batches(
        status: ReconciliationStatus = None,
        start_date: date = None,
        end_date: date = None,
        page: int = 1,
        size: int = 20
    ) -> PaginatedResponse:
        """获取对账批次列表"""
        with get_db_session() as session:
            query = session.query(ReconciliationBatch)

            if status:
                query = query.filter(ReconciliationBatch.status == status)
            if start_date:
                query = query.filter(ReconciliationBatch.created_at >= start_date)
            if end_date:
                query = query.filter(ReconciliationBatch.created_at <= end_date)

            # 获取总数
            total = query.count()

            # 应用分页
            offset = (page - 1) * size
            batches = query.order_by(desc(ReconciliationBatch.created_at)).offset(offset).limit(size).all()

            return PaginatedResponse(
                items=[ReconciliationServiceExtended._batch_to_dict(b) for b in batches],
                total=total,
                page=page,
                size=size,
                pages=(total + size - 1) // size
            )

    @staticmethod
    def get_reconciliation_details(
        batch_id: UUID,
        page: int = 1,
        size: int = 20
    ) -> PaginatedResponse:
        """获取对账详情列表"""
        with get_db_session() as session:
            query = session.query(ReconciliationDetail).filter(
                ReconciliationDetail.batch_id == batch_id
            )

            # 获取总数
            total = query.count()

            # 应用分页
            offset = (page - 1) * size
            details = query.order_by(desc(ReconciliationDetail.created_at)).offset(offset).limit(size).all()

            return PaginatedResponse(
                items=[ReconciliationServiceExtended._detail_to_dict(d) for d in details],
                total=total,
                page=page,
                size=size,
                pages=(total + size - 1) // size
            )

    @staticmethod
    def get_reconciliation_differences(
        batch_id: UUID = None,
        status: DifferenceStatus = None,
        difference_type: DifferenceType = None,
        page: int = 1,
        size: int = 20
    ) -> PaginatedResponse:
        """获取对账差异列表"""
        with get_db_session() as session:
            query = session.query(ReconciliationDifference)

            if batch_id:
                query = query.filter(ReconciliationDifference.batch_id == batch_id)
            if status:
                query = query.filter(ReconciliationDifference.status == status)
            if difference_type:
                query = query.filter(ReconciliationDifference.difference_type == difference_type)

            # 获取总数
            total = query.count()

            # 应用分页
            offset = (page - 1) * size
            differences = query.order_by(desc(ReconciliationDifference.created_at)).offset(offset).limit(size).all()

            return PaginatedResponse(
                items=[ReconciliationServiceExtended._difference_to_dict(d) for d in differences],
                total=total,
                page=page,
                size=size,
                pages=(total + size - 1) // size
            )

    @staticmethod
    def resolve_difference(
        difference_id: UUID,
        resolution_note: str,
        adjustment_amount: Decimal = None,
        user_id: str = None
    ) -> Optional[ReconciliationDifference]:
        """解决对账差异"""
        with get_db_session() as session:
            difference = session.query(ReconciliationDifference).filter(
                ReconciliationDifference.id == difference_id
            ).first()

            if not difference:
                return None

            if difference.status != DifferenceStatus.PENDING:
                raise ValueError("差异已处理，无法重复解决")

            # 更新差异状态
            difference.status = DifferenceStatus.RESOLVED
            difference.resolution_note = resolution_note
            difference.adjustment_amount = adjustment_amount
            difference.resolved_by = user_id
            difference.resolved_at = datetime.utcnow()

            session.commit()

            # 记录审计日志
            AuditService.log_reconciliation_action(
                action=BusinessAction.RECONCILIATION_RESOLVE,
                reconciliation_id=str(difference.batch_id),
                user_id=user_id,
                reconciliation_data={
                    "difference_id": str(difference_id),
                    "resolution_note": resolution_note,
                    "adjustment_amount": float(adjustment_amount) if adjustment_amount else None
                },
                resolution_note=resolution_note
            )

            return difference

    @staticmethod
    def get_reconciliation_summary(
        batch_id: UUID
    ) -> Dict[str, Any]:
        """获取对账汇总信息"""
        with get_db_session() as session:
            batch = session.query(ReconciliationBatch).filter(
                ReconciliationBatch.id == batch_id
            ).first()

            if not batch:
                return None

            # 获取差异统计
            difference_stats = session.query(
                ReconciliationDifference.difference_type,
                func.count(ReconciliationDifference.id).label('count'),
                func.sum(ReconciliationDifference.difference_amount).label('total_amount')
            ).filter(
                ReconciliationDifference.batch_id == batch_id
            ).group_by(ReconciliationDifference.difference_type).all()

            # 获取状态统计
            status_stats = session.query(
                ReconciliationDifference.status,
                func.count(ReconciliationDifference.id).label('count')
            ).filter(
                ReconciliationDifference.batch_id == batch_id
            ).group_by(ReconciliationDifference.status).all()

            return {
                "batch_info": ReconciliationServiceExtended._batch_to_dict(batch),
                "by_difference_type": [
                    {
                        "type": stat.difference_type.value,
                        "count": stat.count,
                        "total_amount": float(stat.total_amount) if stat.total_amount else 0.0
                    }
                    for stat in difference_stats
                ],
                "by_status": [
                    {
                        "status": stat.status.value,
                        "count": stat.count
                    }
                    for stat in status_stats
                ]
            }

    @staticmethod
    def _perform_reconciliation(
        session: Session,
        batch: ReconciliationBatch
    ) -> List[ReconciliationDifference]:
        """执行对账逻辑"""
        differences = []

        # 这里应该实现具体的对账逻辑
        # 1. 获取指定时间范围内的所有交易记录
        # 2. 获取对应的外部系统数据（如银行流水、广告平台数据等）
        # 3. 逐条比对，发现差异
        # 4. 创建对账详情和差异记录

        # 示例实现：模拟对账过程
        from backend.models.ledger import LedgerTransaction, TransactionType, TransactionStatus

        # 获取时间范围内的充值和消费记录
        transactions = session.query(LedgerTransaction).filter(
            and_(
                LedgerTransaction.created_at >= batch.start_date,
                LedgerTransaction.created_at <= batch.end_date,
                LedgerTransaction.status == TransactionStatus.COMPLETED,
                or_(
                    LedgerTransaction.transaction_type == TransactionType.TOPUP,
                    LedgerTransaction.transaction_type == TransactionType.SPEND
                )
            )
        ).all()

        for transaction in transactions:
            # 创建对账详情
            detail = ReconciliationDetail(
                id=uuid4(),
                batch_id=batch.id,
                transaction_id=transaction.id,
                transaction_type=transaction.transaction_type,
                transaction_amount=transaction.amount,
                external_reference=transaction.reference_id,
                external_amount=transaction.amount,  # 假设外部数据一致
                match_status="matched" if transaction.amount == transaction.amount else "mismatched",
                difference_amount=Decimal('0'),
                created_by=batch.created_by
            )

            session.add(detail)

            # 如果存在差异，创建差异记录
            if detail.match_status == "mismatched":
                difference = ReconciliationDifference(
                    id=uuid4(),
                    batch_id=batch.id,
                    detail_id=detail.id,
                    difference_type=DifferenceType.AMOUNT_MISMATCH,
                    difference_amount=abs(detail.transaction_amount - detail.external_amount),
                    description=f"金额不匹配: 系统 {detail.transaction_amount} vs 外部 {detail.external_amount}",
                    status=DifferenceStatus.PENDING,
                    created_by=batch.created_by
                )

                session.add(difference)
                differences.append(difference)

        return differences

    @staticmethod
    def _batch_to_dict(batch: ReconciliationBatch) -> Dict[str, Any]:
        """转换对账批次为字典"""
        return {
            "id": str(batch.id),
            "name": batch.name,
            "start_date": batch.start_date.isoformat(),
            "end_date": batch.end_date.isoformat(),
            "status": batch.status.value,
            "project_ids": [str(pid) for pid in batch.project_ids] if batch.project_ids else [],
            "description": batch.description,
            "total_records": batch.total_records,
            "difference_count": batch.difference_count,
            "matched_count": batch.matched_count,
            "error_message": batch.error_message,
            "created_by": batch.created_by,
            "created_at": batch.created_at.isoformat(),
            "started_at": batch.started_at.isoformat() if batch.started_at else None,
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else None
        }

    @staticmethod
    def _detail_to_dict(detail: ReconciliationDetail) -> Dict[str, Any]:
        """转换对账详情为字典"""
        return {
            "id": str(detail.id),
            "batch_id": str(detail.batch_id),
            "transaction_id": str(detail.transaction_id) if detail.transaction_id else None,
            "transaction_type": detail.transaction_type.value if detail.transaction_type else None,
            "transaction_amount": float(detail.transaction_amount) if detail.transaction_amount else None,
            "external_reference": detail.external_reference,
            "external_amount": float(detail.external_amount) if detail.external_amount else None,
            "match_status": detail.match_status,
            "difference_amount": float(detail.difference_amount) if detail.difference_amount else None,
            "created_at": detail.created_at.isoformat(),
            "updated_at": detail.updated_at.isoformat() if detail.updated_at else None
        }

    @staticmethod
    def _difference_to_dict(difference: ReconciliationDifference) -> Dict[str, Any]:
        """转换对账差异为字典"""
        return {
            "id": str(difference.id),
            "batch_id": str(difference.batch_id),
            "detail_id": str(difference.detail_id) if difference.detail_id else None,
            "difference_type": difference.difference_type.value,
            "difference_amount": float(difference.difference_amount) if difference.difference_amount else None,
            "description": difference.description,
            "status": difference.status.value,
            "resolution_note": difference.resolution_note,
            "adjustment_amount": float(difference.adjustment_amount) if difference.adjustment_amount else None,
            "resolved_by": difference.resolved_by,
            "created_at": difference.created_at.isoformat(),
            "updated_at": difference.updated_at.isoformat() if difference.updated_at else None,
            "resolved_at": difference.resolved_at.isoformat() if difference.resolved_at else None
        }


def get_reconciliation_service_extended() -> ReconciliationServiceExtended:
    """获取对账服务实例"""
    return ReconciliationServiceExtended()