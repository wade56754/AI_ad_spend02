from decimal import Decimal
from math import ceil
from typing import Dict, List, Optional
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.response import success_response, error_response
from backend.core.error_codes import BusinessErrorCodes, ValidationErrorCodes, SystemErrorCodes
from backend.core.dependencies import get_current_user
from backend.models import User
from backend.core.logging import log_requests
from backend.models import AdAccount
# from models import Log  # Log模型不存在，暂时注释
from backend.schemas import AdAccountCreate, AdAccountRead, AdAccountStatusUpdate
from backend.schemas.transfer import TransferRequestCreate, TransferRequestResponse
# from services.log_service import LogService  # 暂时注释，Log模型不存在
from backend.services.ad_account_service import AdAccountService  # 用于测试 mock
from backend.services.transfer_service import TransferService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/ad-accounts", tags=["ad_accounts"])


# ========== 请求体模型 ==========

class BalanceTransferRequest(BaseModel):
    """
    死号余额迁移请求体

    SoT Ref: docs/sot/TRANSFER_SOT.md v1.0
    """
    target_ad_account_id: int = Field(..., description="目标账户ID（接收余额的活跃账户）")
    transfer_amount: Optional[Decimal] = Field(
        None,
        gt=0,
        description="迁移金额（可选，默认迁移全部余额）"
    )
    reason: Optional[str] = Field(None, max_length=500, description="迁移原因")

    model_config = {"extra": "forbid"}

ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
    "new": ["testing"],
    "testing": ["active"],
    "active": ["suspended", "dead"],
    "suspended": ["dead", "active"],
    "dead": ["archived"],
    "archived": [],
}


@log_requests("ad_accounts")
@router.get("", response_model=dict)
def list_ad_accounts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    project_id: Optional[UUID] = Query(None),
    channel_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    获取广告账户列表

    RLS 规则 (AUTH_SPEC.md v2.0 §5.3.1):
    - admin/data_operator: 可见所有账户 (WHERE 1=1)
    - account_manager: 可见所管项目的账户 (JOIN projects WHERE account_manager_id = :user_id)
    - media_buyer: 仅可见分配给自己的账户 (WHERE assigned_to = :user_id)
    - finance: 仅可见账户列表（只读）
    """
    from backend.models import Project

    query = db.query(AdAccount)

    # ===== RLS: 按角色自动过滤数据范围 =====
    user_role = current_user.role
    user_id = current_user.id

    if user_role in ["admin", "data_operator"]:
        # 全局视野，无过滤
        pass

    elif user_role == "account_manager":
        # 仅可见自己管理的项目的账户
        managed_project_ids = (
            db.query(Project.id)
            .filter(Project.account_manager_id == user_id)
            .subquery()
        )
        query = query.filter(AdAccount.project_id.in_(managed_project_ids))

    elif user_role == "media_buyer":
        # 仅可见分配给自己的账户 (owner_id 对齐 init_schema.sql)
        query = query.filter(AdAccount.owner_id == user_id)

    elif user_role == "finance":
        # finance 可以只读查看所有账户
        pass

    else:
        # 其他角色禁止访问
        return error_response(
            code="AUTH_500",
            message="权限不足，无法访问广告账户",
            status_code=403
        )

    # ===== 应用额外过滤条件 =====
    if status_filter:
        query = query.filter(AdAccount.status == status_filter)

    if project_id:
        query = query.filter(AdAccount.project_id == project_id)

    if channel_id:
        query = query.filter(AdAccount.channel_id == channel_id)

    total = query.count()
    items: List[AdAccount] = (
        query.order_by(AdAccount.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    data = [AdAccountRead.model_validate(item, from_attributes=True).model_dump() for item in items]
    pagination = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": ceil(total / page_size) if page_size else 0,
    }
    return success_response(data={"items": data, "meta": {"pagination": pagination}}, message="获取广告账户列表成功")


@log_requests("ad_accounts")
@router.get("/{account_id}", response_model=dict)
def get_ad_account(
    account_id: int,  # BigInteger in model
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    获取单个广告账户详情

    RLS 规则 (AUTH_SPEC.md v2.0 §5.3.1):
    - admin/data_operator/finance: 可访问所有账户
    - account_manager: 仅可访问所管项目的账户
    - media_buyer: 仅可访问分配给自己的账户
    """
    from backend.models import Project

    account = db.query(AdAccount).filter(AdAccount.id == account_id).first()
    if not account:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message="广告账户不存在",
            status_code=404
        )

    # ===== RLS: 权限检查 =====
    user_role = current_user.role
    user_id = current_user.id

    if user_role in ["admin", "data_operator", "finance"]:
        # 全局视野，无过滤
        pass

    elif user_role == "account_manager":
        # 检查账户所属项目是否由当前用户管理
        project = db.query(Project).filter(Project.id == account.project_id).first()
        if not project or project.account_manager_id != user_id:
            return error_response(
                code="AUTH_500",
                message="权限不足，无法访问此广告账户",
                status_code=403
            )

    elif user_role == "media_buyer":
        # 仅可访问分配给自己的账户
        if account.assigned_to != user_id:
            return error_response(
                code="AUTH_500",
                message="权限不足，无法访问未分配给您的账户",
                status_code=403
            )

    else:
        # 其他角色禁止访问
        return error_response(
            code="AUTH_500",
            message="权限不足，无法访问广告账户",
            status_code=403
        )

    data = AdAccountRead.model_validate(account, from_attributes=True).model_dump()
    return success_response(data=data)


@log_requests("ad_accounts")
@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_ad_account(
    payload: AdAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    account = AdAccount(**payload.model_dump())  # id is autoincrement BigInteger
    db.add(account)
    db.commit()
    db.refresh(account)
    data = AdAccountRead.model_validate(account, from_attributes=True).model_dump()

    # LogService.write(
    #     db,
    #     action="create_ad_account",
    #     operator_id=current_user.id,
    #     target="ad_accounts",
    #     target_id=account.id,
    #     detail=data,
    # )

    return success_response(data=data, message="广告账户创建成功", status_code=201)


@log_requests("ad_accounts")
@router.put("/{account_id}/status", response_model=dict)
def update_ad_account_status(
    account_id: int,  # BigInteger in model
    payload: AdAccountStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    account = db.query(AdAccount).filter(AdAccount.id == account_id).first()
    if not account:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message="广告账户不存在",
            status_code=404
        )

    target_status = payload.status
    current_status = account.status

    if target_status == current_status:
        return error_response(
            code=ValidationErrorCodes.VALIDATION_ERROR.code,
            message="状态未改变",
            status_code=422
        )

    allowed = ALLOWED_TRANSITIONS.get(current_status, [])
    if target_status not in allowed:
        return error_response(
            code="STATE_400",
            message=f"状态从 {current_status} 到 {target_status} 的转换不允许",
            status_code=422
        )

    before_state = jsonable_encoder(AdAccountRead.model_validate(account, from_attributes=True).model_dump())

    account.status = target_status
    if payload.dead_reason is not None:
        account.dead_reason = payload.dead_reason
    if payload.updated_by is not None:
        account.updated_by = payload.updated_by

    # log_entry = Log(
    #     actor_id=payload.updated_by,
    #     action="update_ad_account_status",
    #     target_table="ad_accounts",
    #     target_id=account.id,
    #     before_data=before_state,
    #     after_data=None,
    # )
    # db.add(log_entry)

    db.commit()
    db.refresh(account)

    after_state = jsonable_encoder(AdAccountRead.model_validate(account, from_attributes=True).model_dump())
    # log_entry.after_data = after_state
    # db.commit()

    return success_response(data=after_state, message="广告账户状态更新成功")


@log_requests("ad_accounts")
@router.delete("/{account_id}", response_model=dict)
def delete_ad_account(
    account_id: int,  # BigInteger in model
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """删除广告账户（仅允许删除归档状态的账户）"""
    account = db.query(AdAccount).filter(AdAccount.id == account_id).first()
    if not account:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message="广告账户不存在",
            status_code=404
        )

    # 只有归档状态的账户才能删除
    if account.status != "archived":
        return error_response(
            code="STATE_400",
            message="只有归档状态的账户才能删除",
            status_code=400
        )

    db.delete(account)
    db.commit()

    return success_response(data={"message": "广告账户删除成功"}, message="广告账户删除成功")


@log_requests("ad_accounts")
@router.post("/{account_id}/balance-transfer", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_balance_transfer(
    account_id: int,
    payload: BalanceTransferRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    从死号账户发起余额迁移

    **业务规则** (SoT: TRANSFER_SOT.md v1.0):
    - 源账户状态必须为 dead
    - 目标账户状态必须为 active
    - 源账户与目标账户必须属于同一供应商 (supplier_id)
    - 迁移金额必须 > 0 且 <= 源账户余额
    - 迁移不可逆，完成后需通过调账修正

    **状态流转** (SoT: STATE_MACHINE.md v2.6 第12章):
    创建后状态为 draft → 提交后 pending_approval → 审批后 approved → 执行后 completed

    **权限**:
    - account_manager: 可发起（仅自己管理的项目）
    - finance: 可发起和审批
    - admin: 全部权限

    **错误码** (SoT: ERROR_CODES_SOT.md v2.1):
    - E-TRANS-001: 申请单号已存在
    - E-TRANS-002: 源账户不是 dead
    - E-TRANS-003: 目标账户不是 active
    - E-TRANS-004: 跨供应商迁移不允许
    - E-TRANS-006: 余额不足
    """
    # 验证源账户存在
    source_account = db.query(AdAccount).filter(AdAccount.id == account_id).first()
    if not source_account:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message=f"源账户 {account_id} 不存在",
            status_code=404
        )

    # 验证源账户状态必须为 dead
    if source_account.status != "dead":
        return error_response(
            code=BusinessErrorCodes.TRANSFER_SOURCE_NOT_DEAD.code,
            message=f"源账户状态必须为 dead，当前状态: {source_account.status}",
            status_code=400
        )

    # 验证目标账户存在
    target_account = db.query(AdAccount).filter(
        AdAccount.id == payload.target_ad_account_id
    ).first()
    if not target_account:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message=f"目标账户 {payload.target_ad_account_id} 不存在",
            status_code=404
        )

    # 验证目标账户状态必须为 active
    if target_account.status != "active":
        return error_response(
            code=BusinessErrorCodes.TRANSFER_TARGET_NOT_ACTIVE.code,
            message=f"目标账户状态必须为 active，当前状态: {target_account.status}",
            status_code=400
        )

    # 验证源账户和目标账户不能相同
    if account_id == payload.target_ad_account_id:
        return error_response(
            code=BusinessErrorCodes.TRANSFER_SAME_ACCOUNT.code,
            message="源账户和目标账户不能相同",
            status_code=400
        )

    # 验证同供应商限制 (如果有 supplier_id 字段)
    source_supplier_id = getattr(source_account, 'supplier_id', None)
    target_supplier_id = getattr(target_account, 'supplier_id', None)
    if source_supplier_id and target_supplier_id and source_supplier_id != target_supplier_id:
        return error_response(
            code=BusinessErrorCodes.TRANSFER_CROSS_SUPPLIER.code,
            message="禁止跨供应商迁移余额，必须拆分为退款 + 充值",
            status_code=400
        )

    # 获取源账户余额
    source_balance = getattr(source_account, 'balance', Decimal('0.00')) or Decimal('0.00')

    # 确定迁移金额（如果未指定，则迁移全部余额）
    transfer_amount = payload.transfer_amount if payload.transfer_amount else source_balance

    # 验证迁移金额
    if transfer_amount <= 0:
        return error_response(
            code=BusinessErrorCodes.TRANSFER_INVALID_AMOUNT.code,
            message="迁移金额必须大于 0",
            status_code=400
        )

    if transfer_amount > source_balance:
        return error_response(
            code=BusinessErrorCodes.TRANSFER_INSUFFICIENT_BALANCE.code,
            message=f"迁移金额 {transfer_amount} 超过源账户余额 {source_balance}",
            status_code=400
        )

    # 调用 TransferService 创建迁移申请
    try:
        transfer_service = TransferService(db)

        # 构建 TransferRequestCreate
        transfer_request = TransferRequestCreate(
            source_ad_account_id=account_id,
            target_ad_account_id=payload.target_ad_account_id,
            transfer_amount=transfer_amount,
            reason=payload.reason or f"死号余额迁移: 账户 {account_id} → {payload.target_ad_account_id}"
        )

        # 创建迁移申请
        from backend.models import User
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            return error_response(
                code="AUTH-001",
                message="用户不存在",
                status_code=401
            )

        transfer = transfer_service.create_transfer(transfer_request, user)

        # 构建响应
        response_data = {
            "id": transfer.id,
            "request_no": transfer.request_no,
            "source_ad_account_id": transfer.source_ad_account_id,
            "target_ad_account_id": transfer.target_ad_account_id,
            "transfer_amount": str(transfer.transfer_amount),
            "status": transfer.status,
            "reason": transfer.reason,
            "created_at": transfer.created_at.isoformat() if transfer.created_at else None,
        }

        logger.info(
            "Balance transfer created",
            transfer_id=transfer.id,
            source_account=account_id,
            target_account=payload.target_ad_account_id,
            amount=str(transfer_amount),
            user_id=str(current_user.id)
        )

        return success_response(data=response_data, message="余额迁移申请已创建，请等待审批", status_code=201)

    except Exception as e:
        logger.error(
            "Failed to create balance transfer",
            error=str(e),
            source_account=account_id,
            target_account=payload.target_ad_account_id
        )
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message=f"创建迁移申请失败: {str(e)}",
            status_code=500
        )


