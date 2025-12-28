"""
死号余额迁移申请 Pydantic Schemas
Version: 1.0
Author: Claude协作开发

SoT References:
- docs/sot/STATE_MACHINE.md v2.6 第12章 (transfer_requests 状态机)
- docs/sot/DATA_SCHEMA.md v5.2 第3.4.6节 (transfer_requests 表结构)
- docs/sot/API_SOT.md v9.0 (API 规范)
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class TransferRequestCreate(BaseModel):
    """创建迁移申请请求体"""
    source_ad_account_id: int = Field(..., description="源账户ID（死号）")
    target_ad_account_id: int = Field(..., description="目标账户ID（接收方）")
    transfer_amount: Decimal = Field(..., gt=0, description="迁移金额（必须大于0）")
    reason: Optional[str] = Field(None, max_length=500, description="迁移原因")

    @field_validator('transfer_amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("迁移金额必须大于0")
        return v

    @model_validator(mode='after')
    def validate_accounts(self):
        if self.source_ad_account_id == self.target_ad_account_id:
            raise ValueError("源账户和目标账户不能相同")
        return self

    model_config = {"extra": "forbid"}


class TransferRequestSubmit(BaseModel):
    """提交迁移申请请求体（draft → pending_approval）"""
    pass  # 无额外字段

    model_config = {"extra": "forbid"}


class TransferRequestApprove(BaseModel):
    """审批迁移申请请求体（pending_approval → approved）"""
    approval_notes: Optional[str] = Field(None, max_length=500, description="审批意见")

    model_config = {"extra": "forbid"}


class TransferRequestReject(BaseModel):
    """拒绝迁移申请请求体（→ rejected）"""
    rejection_reason: str = Field(..., min_length=1, max_length=500, description="拒绝原因")

    model_config = {"extra": "forbid"}


class TransferRequestComplete(BaseModel):
    """完成迁移请求体（approved → completed）"""
    pass  # 无额外字段

    model_config = {"extra": "forbid"}


class TransferRequestResponse(BaseModel):
    """迁移申请响应体"""
    id: int
    request_no: str
    source_ad_account_id: int
    source_ad_account_name: Optional[str] = None
    target_ad_account_id: int
    target_ad_account_name: Optional[str] = None
    transfer_amount: str  # 返回字符串格式，保持精度
    status: str
    reason: Optional[str] = None
    approval_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_by: Optional[str] = None  # UUID 字符串
    created_by_name: Optional[str] = None
    approved_by: Optional[str] = None  # UUID 字符串
    approved_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TransferRequestListResponse(BaseModel):
    """迁移申请列表响应体"""
    items: List[TransferRequestResponse]
    meta: dict

    model_config = {"from_attributes": True}
