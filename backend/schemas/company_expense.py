"""
公司运营支出 Pydantic 模型

SoT References:
- LEDGER_SOT.md v1.1 (不进入账本)
- BUSINESS_RULES.md v3.2 (金额规范)

Version: 1.0
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CompanyExpenseCreate(BaseModel):
    """创建公司支出请求"""
    model_config = ConfigDict(from_attributes=True)

    expense_type: str = Field(..., max_length=50, description="支出类型: salary/setup_fee/service_fee/exchange/reimbursement/other")
    category: str = Field(..., pattern="^(operation|hr|infrastructure|tools|other)$", description="分类")
    amount: Decimal = Field(..., gt=0, description="金额")
    currency: str = Field("USD", max_length=10, description="币种")
    occurred_at: date = Field(..., description="发生日期")
    description: Optional[str] = Field(None, description="描述")
    receipt_url: Optional[str] = Field(None, description="收据URL")


class CompanyExpenseUpdate(BaseModel):
    """更新公司支出请求"""
    model_config = ConfigDict(from_attributes=True)

    expense_type: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, pattern="^(operation|hr|infrastructure|tools|other)$")
    amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=10)
    occurred_at: Optional[date] = None
    description: Optional[str] = None
    receipt_url: Optional[str] = None


class CompanyExpenseResponse(BaseModel):
    """公司支出响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    expense_type: str
    category: str
    amount: Decimal
    currency: str
    occurred_at: date
    description: Optional[str]
    receipt_url: Optional[str]
    status: str
    created_by: Optional[str]
    approved_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class CompanyExpenseApproval(BaseModel):
    """审批请求"""
    model_config = ConfigDict(from_attributes=True)

    action: str = Field(..., pattern="^(approve|reject)$", description="审批动作")
    reason: Optional[str] = Field(None, max_length=500, description="审批原因（拒绝时必填）")
