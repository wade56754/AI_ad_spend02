"""
死号余额迁移服务
Version: 1.0
Author: Claude协作开发

SoT References:
- docs/2.sot/STATE_MACHINE.md v2.6 第12章 (transfer_requests 状态机)
- docs/2.sot/DATA_SCHEMA.md v5.2 第3.4.6节 (transfer_requests 表结构)
- docs/2.sot/ERROR_CODES_SOT.md v2.1 (错误码)
- docs/2.sot/LEDGER_SOT.md v1.1 (TRANSFER_OUT/TRANSFER_IN)
"""

import logging
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import uuid4

from sqlalchemy import and_, or_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError
)
from backend.models import AdAccount, User, TransferRequest
from backend.models.enums import TransferRequestStatus, UserRole, LedgerEntryType
from backend.models.finance.ledger import LedgerEntry
from backend.schemas.transfer import (
    TransferRequestCreate,
    TransferRequestApprove,
    TransferRequestReject,
    TransferRequestResponse,
)

logger = logging.getLogger(__name__)


# 状态流转白名单 (STATE_MACHINE.md v2.6 第12章)
TRANSFER_STATE_TRANSITIONS = {
    TransferRequestStatus.DRAFT.value: [
        TransferRequestStatus.PENDING_APPROVAL.value,
        TransferRequestStatus.REJECTED.value
    ],
    TransferRequestStatus.PENDING_APPROVAL.value: [
        TransferRequestStatus.APPROVED.value,
        TransferRequestStatus.REJECTED.value
    ],
    TransferRequestStatus.APPROVED.value: [
        TransferRequestStatus.COMPLETED.value
    ],
    TransferRequestStatus.REJECTED.value: [],  # 终态
    TransferRequestStatus.COMPLETED.value: [],  # 终态
}


class TransferService:
    """死号余额迁移服务类"""

    def __init__(self, db: Session):
        self.db = db

    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        try:
            yield
            self.db.commit()
            logger.debug("Transaction committed successfully")
        except Exception as e:
            logger.error(f"Transaction failed, rolling back: {str(e)}", exc_info=True)
            self.db.rollback()
            raise

    def _can_transition(self, from_status: str, to_status: str) -> bool:
        """检查状态流转是否合法"""
        allowed = TRANSFER_STATE_TRANSITIONS.get(from_status, [])
        return to_status in allowed

    def _generate_request_no(self) -> str:
        """生成迁移申请单号"""
        # 格式: TRF + 年月日时分秒 + 随机4位
        now = datetime.now()
        random_suffix = str(uuid4().int)[:4]
        return f"TRF{now.strftime('%Y%m%d%H%M%S')}{random_suffix}"

    def _build_response(self, transfer: TransferRequest) -> TransferRequestResponse:
        """构建迁移申请响应"""
        return TransferRequestResponse(
            id=transfer.id,
            request_no=transfer.request_no,
            source_ad_account_id=transfer.source_ad_account_id,
            source_ad_account_name=(
                transfer.source_ad_account.account_name or
                transfer.source_ad_account.account_code
                if transfer.source_ad_account else None
            ),
            target_ad_account_id=transfer.target_ad_account_id,
            target_ad_account_name=(
                transfer.target_ad_account.account_name or
                transfer.target_ad_account.account_code
                if transfer.target_ad_account else None
            ),
            transfer_amount=str(transfer.transfer_amount),
            status=transfer.status,
            reason=transfer.reason,
            approval_notes=transfer.approval_notes,
            rejection_reason=transfer.rejection_reason,
            created_by=str(transfer.created_by) if transfer.created_by else None,
            created_by_name=transfer.creator.username if transfer.creator else None,
            approved_by=str(transfer.approved_by) if transfer.approved_by else None,
            approved_by_name=transfer.approver.username if transfer.approver else None,
            created_at=transfer.created_at,
            updated_at=transfer.updated_at,
            approved_at=transfer.approved_at,
            completed_at=transfer.completed_at,
        )

    def create_transfer(
        self,
        request: TransferRequestCreate,
        current_user: User
    ) -> TransferRequest:
        """
        创建迁移申请

        权限: account_manager, finance, admin
        初始状态: draft

        SoT Ref: STATE_MACHINE.md v2.6 第12章
        """
        logger.info(
            f"Creating transfer: source={request.source_ad_account_id}, "
            f"target={request.target_ad_account_id}, amount={request.transfer_amount}, "
            f"user={current_user.id}"
        )

        # 权限检查
        if current_user.role not in [
            UserRole.ADMIN.value, UserRole.ACCOUNT_MANAGER.value, UserRole.FINANCE.value
        ]:
            raise PermissionDeniedError(
                "无权限创建迁移申请，仅 admin/account_manager/finance 可操作",
                error_code="AUTH_500"
            )

        # 验证源账户存在
        source_account = self.db.query(AdAccount).filter(
            AdAccount.id == request.source_ad_account_id
        ).first()
        if not source_account:
            raise ResourceNotFoundError(
                f"源账户 {request.source_ad_account_id} 不存在",
                error_code="BIZ_002"
            )

        # 验证目标账户存在
        target_account = self.db.query(AdAccount).filter(
            AdAccount.id == request.target_ad_account_id
        ).first()
        if not target_account:
            raise ResourceNotFoundError(
                f"目标账户 {request.target_ad_account_id} 不存在",
                error_code="BIZ_002"
            )

        # 业务校验: 源账户和目标账户不能相同 (已在 schema 中校验，此处双重保险)
        if request.source_ad_account_id == request.target_ad_account_id:
            raise BusinessLogicError(
                "源账户和目标账户不能相同",
                error_code="BIZ_001"
            )

        # 业务校验: 同供应商约束 (DATA_SCHEMA.md v5.2 §3.2.5)
        # 如果两个账户都有 supplier_id，则必须相同；否则跳过校验
        source_supplier_id = getattr(source_account, 'supplier_id', None)
        target_supplier_id = getattr(target_account, 'supplier_id', None)
        if source_supplier_id and target_supplier_id and source_supplier_id != target_supplier_id:
            raise BusinessLogicError(
                f"禁止跨供应商迁移余额。源账户供应商={source_supplier_id}，"
                f"目标账户供应商={target_supplier_id}。请拆分为退款 + 充值操作",
                error_code="E-TRANS-004"  # 跨供应商迁移不允许
            )

        # 业务校验: 迁移金额不能超过源账户余额
        source_balance = getattr(source_account, 'balance', Decimal('0.00')) or Decimal('0.00')
        if request.transfer_amount > source_balance:
            raise BusinessLogicError(
                f"迁移金额 {request.transfer_amount} 超过源账户余额 {source_balance}",
                error_code="BIZ_001"
            )

        with self.transaction():
            transfer = TransferRequest(
                request_no=self._generate_request_no(),
                source_ad_account_id=request.source_ad_account_id,
                target_ad_account_id=request.target_ad_account_id,
                transfer_amount=request.transfer_amount,
                status=TransferRequestStatus.DRAFT.value,
                reason=request.reason,
                created_by=current_user.id,
            )
            self.db.add(transfer)
            self.db.flush()  # 获取 ID

            logger.info(f"Transfer created: id={transfer.id}, request_no={transfer.request_no}")
            return transfer

    def get_transfer_by_id(
        self,
        transfer_id: int,
        current_user: User
    ) -> TransferRequest:
        """获取迁移申请详情"""
        transfer = self.db.query(TransferRequest).options(
            joinedload(TransferRequest.source_ad_account),
            joinedload(TransferRequest.target_ad_account),
            joinedload(TransferRequest.creator),
            joinedload(TransferRequest.approver),
        ).filter(
            TransferRequest.id == transfer_id
        ).first()

        if not transfer:
            raise ResourceNotFoundError(
                f"迁移申请 {transfer_id} 不存在",
                error_code="BIZ_002"
            )

        return transfer

    def get_transfers(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> Tuple[List[TransferRequest], int]:
        """获取迁移申请列表"""
        query = self.db.query(TransferRequest).options(
            joinedload(TransferRequest.source_ad_account),
            joinedload(TransferRequest.target_ad_account),
            joinedload(TransferRequest.creator),
        )

        if status:
            query = query.filter(TransferRequest.status == status)

        # 按创建时间倒序
        query = query.order_by(TransferRequest.created_at.desc())

        total = query.count()
        transfers = query.offset((page - 1) * page_size).limit(page_size).all()

        return transfers, total

    def submit_transfer(
        self,
        transfer_id: int,
        current_user: User
    ) -> TransferRequest:
        """
        提交迁移申请 (draft → pending_approval)

        权限: 创建人或 admin
        """
        transfer = self.get_transfer_by_id(transfer_id, current_user)

        # 权限检查
        if (str(transfer.created_by) != str(current_user.id) and
            current_user.role != UserRole.ADMIN.value):
            raise PermissionDeniedError(
                "只有申请人或管理员可以提交",
                error_code="AUTH_500"
            )

        # 状态检查
        if not self._can_transition(
            transfer.status, TransferRequestStatus.PENDING_APPROVAL.value
        ):
            raise BusinessLogicError(
                f"当前状态 {transfer.status} 不能提交审批",
                error_code="STATE_001"
            )

        with self.transaction():
            transfer.status = TransferRequestStatus.PENDING_APPROVAL.value
            transfer.version += 1
            logger.info(f"Transfer {transfer_id} submitted for approval")
            return transfer

    def approve_transfer(
        self,
        transfer_id: int,
        approval: TransferRequestApprove,
        current_user: User
    ) -> TransferRequest:
        """
        审批迁移申请 (pending_approval → approved)

        权限: finance, admin
        """
        transfer = self.get_transfer_by_id(transfer_id, current_user)

        # 权限检查
        if current_user.role not in [UserRole.ADMIN.value, UserRole.FINANCE.value]:
            raise PermissionDeniedError(
                "只有 finance/admin 可以审批",
                error_code="AUTH_500"
            )

        # 状态检查
        if not self._can_transition(
            transfer.status, TransferRequestStatus.APPROVED.value
        ):
            raise BusinessLogicError(
                f"当前状态 {transfer.status} 不能审批通过",
                error_code="STATE_001"
            )

        with self.transaction():
            transfer.status = TransferRequestStatus.APPROVED.value
            transfer.approved_by = current_user.id
            transfer.approved_at = datetime.now()
            transfer.approval_notes = approval.approval_notes
            transfer.version += 1
            logger.info(f"Transfer {transfer_id} approved by {current_user.id}")
            return transfer

    def reject_transfer(
        self,
        transfer_id: int,
        rejection: TransferRequestReject,
        current_user: User
    ) -> TransferRequest:
        """
        拒绝迁移申请 (draft/pending_approval → rejected)

        权限: finance, admin
        """
        transfer = self.get_transfer_by_id(transfer_id, current_user)

        # 权限检查
        if current_user.role not in [UserRole.ADMIN.value, UserRole.FINANCE.value]:
            raise PermissionDeniedError(
                "只有 finance/admin 可以拒绝",
                error_code="AUTH_500"
            )

        # 状态检查
        if not self._can_transition(
            transfer.status, TransferRequestStatus.REJECTED.value
        ):
            raise BusinessLogicError(
                f"当前状态 {transfer.status} 不能拒绝",
                error_code="STATE_001"
            )

        with self.transaction():
            transfer.status = TransferRequestStatus.REJECTED.value
            transfer.approved_by = current_user.id
            transfer.approved_at = datetime.now()
            transfer.rejection_reason = rejection.rejection_reason
            transfer.version += 1
            logger.info(f"Transfer {transfer_id} rejected by {current_user.id}")
            return transfer

    def complete_transfer(
        self,
        transfer_id: int,
        current_user: User
    ) -> TransferRequest:
        """
        完成迁移 (approved → completed)

        权限: admin (system 自动执行或 admin 手动完成)
        业务: 生成 TRANSFER_OUT/TRANSFER_IN Ledger 记录

        SoT Ref: STATE_MACHINE.md v2.6 第12章, LEDGER_SOT.md v1.1
        """
        transfer = self.get_transfer_by_id(transfer_id, current_user)

        # 权限检查
        if current_user.role != UserRole.ADMIN.value:
            raise PermissionDeniedError(
                "只有 admin 可以完成迁移",
                error_code="AUTH_500"
            )

        # 状态检查
        if not self._can_transition(
            transfer.status, TransferRequestStatus.COMPLETED.value
        ):
            raise BusinessLogicError(
                f"当前状态 {transfer.status} 不能完成，必须先审批通过",
                error_code="STATE_001"
            )

        with self.transaction():
            # ====== LEDGER_SOT.md v1.1: TRANSFER_OUT/TRANSFER_IN 双条目生成 ======

            # 1. 获取源账户和目标账户（带行锁）
            source_account = self.db.query(AdAccount).filter(
                AdAccount.id == transfer.source_ad_account_id
            ).with_for_update().first()

            target_account = self.db.query(AdAccount).filter(
                AdAccount.id == transfer.target_ad_account_id
            ).with_for_update().first()

            if not source_account or not target_account:
                raise BusinessLogicError(
                    "源账户或目标账户不存在",
                    error_code="BIZ_002"
                )

            # 2. 获取当前余额
            source_balance = LedgerEntry.get_account_balance(self.db, transfer.source_ad_account_id)
            target_balance = LedgerEntry.get_account_balance(self.db, transfer.target_ad_account_id)
            transfer_amount = transfer.transfer_amount

            # 3. 验证余额充足
            if source_balance < transfer_amount:
                raise BusinessLogicError(
                    f"源账户余额不足: 当前余额 {source_balance}, 迁移金额 {transfer_amount}",
                    error_code="BIZ_616"
                )

            # 4. 创建 TRANSFER_OUT 分录（源账户，负数）
            transfer_out_entry = LedgerEntry(
                ad_account_id=transfer.source_ad_account_id,
                entry_type=LedgerEntryType.TRANSFER_OUT.value,
                amount=-transfer_amount,  # 负数表示转出
                balance_after=source_balance - transfer_amount,
                reference_type="transfer_request",
                reference_id=transfer.id,
                notes=f"余额迁移转出 #{transfer.request_no} 至账户 {transfer.target_ad_account_id}"
            )
            self.db.add(transfer_out_entry)

            # 5. 创建 TRANSFER_IN 分录（目标账户，正数）
            transfer_in_entry = LedgerEntry(
                ad_account_id=transfer.target_ad_account_id,
                entry_type=LedgerEntryType.TRANSFER_IN.value,
                amount=transfer_amount,  # 正数表示转入
                balance_after=target_balance + transfer_amount,
                reference_type="transfer_request",
                reference_id=transfer.id,
                notes=f"余额迁移转入 #{transfer.request_no} 从账户 {transfer.source_ad_account_id}"
            )
            self.db.add(transfer_in_entry)

            # 6. 更新广告账户余额 (LEDGER_SOT.md v1.1 §3.2 余额真相源)
            source_account.balance = (source_account.balance or Decimal('0.00')) - transfer_amount
            target_account.balance = (target_account.balance or Decimal('0.00')) + transfer_amount

            # 7. 更新迁移申请状态
            transfer.status = TransferRequestStatus.COMPLETED.value
            transfer.completed_at = datetime.now()
            transfer.version += 1

            logger.info(
                f"Transfer {transfer_id} completed by {current_user.id}: "
                f"amount={transfer_amount}, "
                f"source_balance_after={source_balance - transfer_amount}, "
                f"target_balance_after={target_balance + transfer_amount}"
            )
            return transfer
