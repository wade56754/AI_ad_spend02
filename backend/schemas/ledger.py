"""
账本流水相关的Pydantic模型 (TASK-LEDGER-001)

Version: 1.0
SoT: LEDGER_SOT.md v1.2, DATA_SCHEMA.md v5.6 §ledger_entries
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

from backend.schemas.response import PaginationMeta


class LedgerEntryTypeEnum(str, Enum):
    """
    账本分录类型枚举

    对齐 LEDGER_SOT.md v1.2:
    - TOPUP: 充值入账
    - COST: 广告消耗 (spend)
    - REVENUE: 收入
    - TRANSFER_OUT: 转出
    - TRANSFER_IN: 转入
    - REVERSAL: 红冲
    """
    TOPUP = "TOPUP"
    COST = "COST"
    REVENUE = "REVENUE"
    TRANSFER_OUT = "TRANSFER_OUT"
    TRANSFER_IN = "TRANSFER_IN"
    REVERSAL = "REVERSAL"


class LedgerEntryResponse(BaseModel):
    """
    账本流水响应 (TASK-LEDGER-001)

    返回字段: id, ad_account_id, entry_type, amount, balance_after, created_at
    """
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="分录ID")
    ad_account_id: int = Field(..., description="广告账户ID")
    entry_type: str = Field(..., description="分录类型: TOPUP, COST, REVENUE, TRANSFER_OUT, TRANSFER_IN, REVERSAL")
    amount: Decimal = Field(..., description="金额")
    balance_after: Decimal = Field(..., description="交易后余额")
    reference_id: Optional[int] = Field(None, description="关联记录ID")
    reference_type: Optional[str] = Field(None, description="关联记录类型")
    notes: Optional[str] = Field(None, description="备注")
    entry_date: datetime = Field(..., description="分录日期")
    created_at: datetime = Field(..., description="创建时间")


class LedgerEntryListResponse(BaseModel):
    """
    账本流水列表响应 (TASK-LEDGER-001)

    支持分页查询
    """
    model_config = ConfigDict(from_attributes=True)

    items: List[LedgerEntryResponse] = Field(default_factory=list, description="流水列表")
    meta: PaginationMeta = Field(..., description="分页信息")


class LedgerEntryQueryParams(BaseModel):
    """
    账本流水查询参数

    支持筛选: ad_account_id, entry_type, date_range
    """
    ad_account_id: Optional[int] = Field(None, description="广告账户ID")
    entry_type: Optional[str] = Field(None, description="分录类型")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")


# ========== TASK-LEDGER-003: 红冲 API Schema ==========

class ReversalRequest(BaseModel):
    """
    红冲请求 (TASK-LEDGER-003)

    SoT: LEDGER_SOT.md v1.2 §红冲规则, BR-FIN-008
    """
    reason: str = Field(..., min_length=1, description="红冲原因（必填）")


class ReversalResponse(BaseModel):
    """
    红冲响应 (TASK-LEDGER-003)
    """
    model_config = ConfigDict(from_attributes=True)

    original_id: int = Field(..., description="原分录ID")
    reversal_id: int = Field(..., description="红冲分录ID")
    amount: Decimal = Field(..., description="红冲金额（负数）")
