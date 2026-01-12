"""
对账管理扩展模块
包含对账批次、对账详情、差异处理等完整对账功能

⚠️ 注意：此文件名为 `reconciliation_extended.py`，但包含的是当前正在使用的模型类和枚举。
这些类正在被以下模块使用：
- backend/services/reconciliation_service_extended.py
- backend/tests/test_new_modules_integration.py

未来重构建议：将此文件重命名为 `reconciliation_models.py` 或移动到 `backend/models/finance/` 目录。
"""

from datetime import datetime, date
from sqlalchemy import Date
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Numeric, Boolean, Integer, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from backend.models.base import Base

# 从 finance 模块导入正式的 ReconciliationBatch 模型类（向后兼容）
from backend.models.finance.reconciliation import ReconciliationBatch


class ReconciliationStatus(str, Enum):
    """对账状态枚举"""
    PENDING = "pending"              # 待对账
    PROCESSING = "processing"        # 对账中
    COMPLETED = "completed"          # 已完成
    FAILED = "failed"                # 失败
    CANCELLED = "cancelled"          # 已取消


class ReconciliationType(str, Enum):
    """对账类型枚举"""
    DAILY = "daily"                  # 日对账
    WEEKLY = "weekly"                # 周对账
    MONTHLY = "monthly"              # 月对账
    CUSTOM = "custom"                # 自定义对账


class DifferenceType(str, Enum):
    """差异类型枚举"""
    SPEND_MISMATCH = "spend_mismatch"            # 消耗不匹配
    TOPUP_MISMATCH = "topup_mismatch"            # 充值不匹配
    TIMING_DIFFERENCE = "timing_difference"      # 时间差异
    CURRENCY_DIFFERENCE = "currency_difference"  # 货币差异
    FEE_DIFFERENCE = "fee_difference"            # 手续费差异
    OTHER = "other"                              # 其他差异


class DifferenceStatus(str, Enum):
    """差异状态枚举"""
    OPEN = "open"                    # 待处理
    INVESTIGATING = "investigating"  # 调查中
    RESOLVED = "resolved"            # 已解决
    IGNORED = "ignored"              # 忽略
    ESCALATED = "escalated"          # 已上报


# ⚠️ DEPRECATED: 此 ReconciliationBatch 类已被 backend/models/finance.py 替代
# 请使用 from backend.models.finance import ReconciliationBatch
# 保留此类仅用于向后兼容，但已禁用表定义以避免重复注册
class _ReconciliationBatchLegacy(Base):
    """对账批次表 - 对账任务的主要容器"""
    # __tablename__ = "reconciliation_batches"  # 已注释掉，避免重复定义表
    __abstract__ = True  # 标记为抽象类，不会创建表

    # 主键
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 对账基本信息
    batch_number = Column(String(50), unique=True, nullable=False, comment="对账批次号")
    title = Column(String(255), nullable=False, comment="对账标题")
    description = Column(Text, nullable=True, comment="对账描述")

    # 对账类型和范围
    reconciliation_type = Column(SQLEnum(ReconciliationType), nullable=False, comment="对账类型")
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, comment="项目ID（可选，全局对账时为空）")
    channel_id = Column(PG_UUID(as_uuid=True), ForeignKey("channels.id"), nullable=True, comment="渠道ID（可选）")

    # 对账时间范围
    start_date = Column(Date, nullable=False, comment="对账开始日期")
    end_date = Column(Date, nullable=False, comment="对账结束日期")

    # 对账状态
    status = Column(SQLEnum(ReconciliationStatus), default=ReconciliationStatus.PENDING, nullable=False, comment="对账状态")

    # 对账结果统计
    total_transactions = Column(Integer, default=0, comment="总交易数")
    matched_transactions = Column(Integer, default=0, comment="匹配交易数")
    unmatched_transactions = Column(Integer, default=0, comment="未匹配交易数")
    total_differences = Column(Integer, default=0, comment="差异总数")
    resolved_differences = Column(Integer, default=0, comment="已解决差异数")

    # 金额统计
    total_spend = Column(Numeric(15, 2), default=0, comment="总消耗")
    total_topup = Column(Numeric(15, 2), default=0, comment="总充值")
    total_difference = Column(Numeric(15, 2), default=0, comment="总差异金额")
    resolved_amount = Column(Numeric(15, 2), default=0, comment="已解决差异金额")

    # 执行信息
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    execution_time = Column(Integer, nullable=True, comment="执行时间（秒）")

    # 配置和参数
    auto_resolve_threshold = Column(Numeric(10, 2), default=0.01, comment="自动解决阈值")
    include_pending = Column(Boolean, default=False, comment="是否包含待处理交易")

    # 报表和输出
    report_path = Column(String(500), nullable=True, comment="报表文件路径")
    report_generated_at = Column(DateTime, nullable=True, comment="报表生成时间")

    # 审计信息
    created_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, comment="创建人")
    approved_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="审批人")
    approved_at = Column(DateTime, nullable=True, comment="审批时间")

    # 系统字段
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    deleted_at = Column(DateTime, nullable=True, comment="软删除时间")

    # 索引
    __table_args__ = (
        Index('idx_recon_batch_number', 'batch_number'),
        Index('idx_recon_type_status', 'reconciliation_type', 'status'),
        Index('idx_recon_project', 'project_id'),
        Index('idx_recon_channel', 'channel_id'),
        Index('idx_recon_dates', 'start_date', 'end_date'),
        Index('idx_recon_created_at', 'created_at'),
        Index('idx_recon_deleted_at', 'deleted_at'),
        {'comment': '对账批次表 - 对账任务的主要容器'}
    )

    # 关系
    project = relationship("Project", foreign_keys=[project_id])
    channel = relationship("Channel", foreign_keys=[channel_id])
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    details = relationship("ReconciliationDetail", back_populates="batch", cascade="all, delete-orphan")
    differences = relationship("ReconciliationDifference", back_populates="batch", cascade="all, delete-orphan")


class ReconciliationDetail(Base):
    """对账详情表 - 记录具体的对账匹配结果"""
    # __tablename__ = "reconciliation_details"  # 已注释掉，避免重复定义表
    __abstract__ = True  # 标记为抽象类，不会创建表

    # 主键
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 关联批次
    batch_id = Column(PG_UUID(as_uuid=True), ForeignKey("reconciliation_batches.id"), nullable=False, comment="对账批次ID")

    # 账户信息
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, comment="项目ID")
    ad_account_id = Column(PG_UUID(as_uuid=True), ForeignKey("ad_accounts.id"), nullable=False, comment="广告账户ID")
    channel_id = Column(PG_UUID(as_uuid=True), ForeignKey("channels.id"), nullable=True, comment="渠道ID")

    # 对账数据
    reconciliation_date = Column(Date, nullable=False, comment="对账日期")

    # 系统记录数据（日报系统）
    system_spend = Column(Numeric(15, 2), default=0, comment="系统记录消耗")
    system_leads = Column(Integer, default=0, comment="系统记录线索数")
    system_conversions = Column(Integer, default=0, comment="系统记录转化数")

    # 渠道/广告平台数据
    external_spend = Column(Numeric(15, 2), default=0, comment="外部记录消耗")
    external_leads = Column(Integer, default=0, comment="外部记录线索数")
    external_conversions = Column(Integer, default=0, comment="外部记录转化数")
    external_impressions = Column(Integer, default=0, comment="外部记录展示数")
    external_clicks = Column(Integer, default=0, comment="外部记录点击数")

    # 匹配状态
    is_matched = Column(Boolean, default=False, comment="是否匹配")
    match_score = Column(Numeric(5, 4), default=0, comment="匹配分数")
    match_status = Column(String(20), default="pending", comment="匹配状态: matched, partial, mismatched")

    # 差异计算
    spend_difference = Column(Numeric(15, 2), default=0, comment="消耗差异")
    leads_difference = Column(Integer, default=0, comment="线索差异")
    conversions_difference = Column(Integer, default=0, comment="转化差异")

    # 货币信息
    currency = Column(String(3), default="USD", comment="货币类型")
    exchange_rate = Column(Numeric(10, 6), default=1, comment="汇率")

    # 调整和处理
    adjustment_amount = Column(Numeric(15, 2), default=0, comment="调整金额")
    adjustment_reason = Column(Text, nullable=True, comment="调整原因")
    adjusted_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="调整人")
    adjusted_at = Column(DateTime, nullable=True, comment="调整时间")

    # 备注和说明
    notes = Column(Text, nullable=True, comment="备注说明")
    investigation_notes = Column(Text, nullable=True, comment="调查笔记")

    # 系统字段
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")

    # 索引
    __table_args__ = (
        Index('idx_recon_detail_batch', 'batch_id'),
        Index('idx_recon_detail_account', 'ad_account_id'),
        Index('idx_recon_detail_project', 'project_id'),
        Index('idx_recon_detail_date', 'reconciliation_date'),
        Index('idx_recon_detail_matched', 'is_matched'),
        Index('idx_recon_detail_status', 'match_status'),
        Index('idx_recon_detail_updated', 'updated_at'),
        {'comment': '对账详情表 - 记录具体的对账匹配结果'}
    )

    # 关系
    batch = relationship("ReconciliationBatch", back_populates="details")
    project = relationship("Project", foreign_keys=[project_id])
    ad_account = relationship("AdAccount", foreign_keys=[ad_account_id])
    channel = relationship("Channel", foreign_keys=[channel_id])
    adjuster = relationship("User", foreign_keys=[adjusted_by])


class ReconciliationDifference(Base):
    """对账差异表 - 记录和管理对账差异"""
    # __tablename__ = "reconciliation_differences"  # 已注释掉，避免重复定义表
    __abstract__ = True  # 标记为抽象类，不会创建表

    # 主键
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 关联信息
    batch_id = Column(PG_UUID(as_uuid=True), ForeignKey("reconciliation_batches.id"), nullable=False, comment="对账批次ID")
    detail_id = Column(PG_UUID(as_uuid=True), ForeignKey("reconciliation_details.id"), nullable=True, comment="对账详情ID")

    # 差异基本信息
    difference_number = Column(String(50), unique=True, nullable=False, comment="差异编号")
    title = Column(String(255), nullable=False, comment="差异标题")
    description = Column(Text, nullable=True, comment="差异描述")

    # 差异类型和状态
    difference_type = Column(SQLEnum(DifferenceType), nullable=False, comment="差异类型")
    status = Column(SQLEnum(DifferenceStatus), default=DifferenceStatus.OPEN, nullable=False, comment="差异状态")
    severity = Column(String(20), default="medium", comment="严重程度: low, medium, high, critical")

    # 账户信息
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, comment="项目ID")
    ad_account_id = Column(PG_UUID(as_uuid=True), ForeignKey("ad_accounts.id"), nullable=False, comment="广告账户ID")

    # 差异数据
    expected_amount = Column(Numeric(15, 2), default=0, comment="期望金额")
    actual_amount = Column(Numeric(15, 2), default=0, comment="实际金额")
    difference_amount = Column(Numeric(15, 2), default=0, comment="差异金额")
    difference_percentage = Column(Numeric(5, 2), default=0, comment="差异百分比")

    # 相关数据
    reference_id = Column(String(255), nullable=True, comment="关联业务ID")
    reference_type = Column(String(50), nullable=True, comment="关联业务类型")
    external_reference = Column(String(255), nullable=True, comment="外部参考")

    # 时间信息
    difference_date = Column(Date, nullable=False, comment="差异日期")
    detected_at = Column(DateTime, nullable=False, comment="发现时间")

    # 调查和处理
    investigation_notes = Column(Text, nullable=True, comment="调查笔记")
    resolution_notes = Column(Text, nullable=True, comment="解决方案笔记")
    resolution_amount = Column(Numeric(15, 2), default=0, comment="解决金额")

    # 责任人
    assigned_to = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="分配给")
    resolved_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="解决人")

    # 时间跟踪
    assigned_at = Column(DateTime, nullable=True, comment="分配时间")
    resolved_at = Column(DateTime, nullable=True, comment="解决时间")
    due_date = Column(DateTime, nullable=True, comment="截止时间")

    # 审计信息
    created_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, comment="创建人")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")

    # 索引
    __table_args__ = (
        Index('idx_recon_diff_number', 'difference_number'),
        Index('idx_recon_diff_batch', 'batch_id'),
        Index('idx_recon_diff_type_status', 'difference_type', 'status'),
        Index('idx_recon_diff_project', 'project_id'),
        Index('idx_recon_diff_account', 'ad_account_id'),
        Index('idx_recon_diff_severity', 'severity'),
        Index('idx_recon_diff_assigned', 'assigned_to'),
        Index('idx_recon_diff_date', 'difference_date'),
        Index('idx_recon_diff_created', 'created_at'),
        {'comment': '对账差异表 - 记录和管理对账差异'}
    )

    # 关系
    batch = relationship("ReconciliationBatch", back_populates="differences")
    detail = relationship("ReconciliationDetail", foreign_keys=[detail_id])
    project = relationship("Project", foreign_keys=[project_id])
    ad_account = relationship("AdAccount", foreign_keys=[ad_account_id])
    assignee = relationship("User", foreign_keys=[assigned_to])
    resolver = relationship("User", foreign_keys=[resolved_by])
    creator = relationship("User", foreign_keys=[created_by])