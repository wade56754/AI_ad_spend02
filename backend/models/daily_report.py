"""
日报管理数据模型
Version: 1.0
Author: Claude协作开发
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, BigInteger, String, Text, Date, DateTime,
    Numeric, ForeignKey, Index, UniqueConstraint, Integer
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.db import Base


class DailyReport(Base):
    """日报主表（对齐 DATA_SCHEMA.md 3.3.1）"""
    __tablename__ = "daily_reports"

    # 主键：BIGSERIAL（对齐 DATA_SCHEMA）
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="日报ID")
    report_date = Column(Date, nullable=False, index=True, comment="报表日期")
    ad_account_id = Column(
        BigInteger,
        ForeignKey("ad_accounts.id"),
        nullable=False,
        index=True,
        comment="广告账户ID"
    )

    # 广告信息
    campaign_name = Column(String(200), comment="广告系列名称")
    ad_group_name = Column(String(200), comment="广告组名称")
    ad_creative_name = Column(String(200), comment="广告创意名称")

    # 投放数据（对齐 DATA_SCHEMA）
    impressions = Column(Integer, default=0, server_default='0', comment="展示次数")
    clicks = Column(Integer, default=0, server_default='0', comment="点击次数")
    spend = Column(Numeric(15, 2), default=0.00, server_default='0.00', comment="消耗金额")
    conversions = Column(Integer, default=0, server_default='0', comment="转化次数")
    new_follows = Column(Integer, default=0, server_default='0', comment="新增粉丝数")
    
    # 比率字段（对齐 DATA_SCHEMA：DECIMAL(12,4)）
    cpc = Column(Numeric(12, 4), nullable=True, comment="CPC")
    cpa = Column(Numeric(12, 4), nullable=True, comment="CPA")
    ctr = Column(Numeric(12, 4), nullable=True, comment="CTR")
    roi = Column(Numeric(12, 4), nullable=True, comment="ROI")

    # 状态和备注（枚举值以 STATE_MACHINE.md 为准）
    status = Column(String(20), nullable=False, index=True, comment="审核状态")
    notes = Column(Text, nullable=True, comment="备注说明")
    attachments = Column(JSON, nullable=True, server_default='{}', comment="附件（JSONB）")

    # 审计字段（外键指向 user_profiles.id，UUID）
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=True,
        index=True,
        comment="创建人ID"
    )
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=True,
        comment="更新人ID"
    )
    submitted_by = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=True,
        comment="提交人ID"
    )
    audit_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=True,
        comment="审核人ID"
    )
    
    # 时间字段（对齐 DATA_SCHEMA：TIMESTAMPTZ）
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
    submitted_at = Column(DateTime(timezone=True), nullable=True, comment="提交时间")
    approved_at = Column(DateTime(timezone=True), nullable=True, comment="审核通过时间")

    # 唯一约束和索引（对齐 DATA_SCHEMA 3.3.1）
    __table_args__ = (
        UniqueConstraint('report_date', 'ad_account_id', name='uq_daily_reports_date_account'),
        Index('idx_daily_reports_date', 'report_date'),
        Index('idx_daily_reports_account', 'ad_account_id'),
        Index('idx_daily_reports_status', 'status'),
        Index('idx_daily_reports_created_by', 'created_by'),
        {'comment': '日报数据表'}
    )

    # 关联关系
    ad_account = relationship("AdAccount", back_populates="daily_reports")
    creator = relationship("UserProfile", foreign_keys=[created_by])
    updater = relationship("UserProfile", foreign_keys=[updated_by])
    submitter = relationship("UserProfile", foreign_keys=[submitted_by])
    auditor = relationship("UserProfile", foreign_keys=[audit_user_id])
    audit_logs = relationship("DailyReportAuditLog", back_populates="daily_report")

    def __repr__(self):
        return f"<DailyReport(id={self.id}, date={self.report_date}, account_id={self.ad_account_id})>"


class DailyReportAuditLog(Base):
    """日报审核日志表（对齐 DATA_SCHEMA.md 3.3.2）"""
    __tablename__ = "daily_report_audit_logs"

    # 主键：BIGSERIAL（对齐 DATA_SCHEMA）
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="日志ID")
    daily_report_id = Column(
        BigInteger,
        ForeignKey("daily_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="日报ID"
    )

    # 操作信息
    action = Column(
        String(20),
        nullable=False,
        comment="操作类型: created/updated/approved/rejected"
    )
    old_status = Column(String(20), comment="旧状态")
    new_status = Column(String(20), comment="新状态")

    # 审核信息（外键指向 user_profiles.id，UUID）
    audit_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=False,
        comment="操作人ID"
    )
    audit_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="操作时间")
    audit_notes = Column(Text, nullable=True, comment="操作说明")

    # 审计信息
    ip_address = Column(INET, comment="IP地址")
    user_agent = Column(Text, comment="用户代理")

    __table_args__ = (
        Index('idx_audit_logs_report', 'daily_report_id'),
        Index('idx_audit_logs_user', 'audit_user_id'),
        Index('idx_audit_logs_time', 'audit_time'),
        Index('idx_audit_logs_action', 'action'),
        {'comment': '日报操作审计日志表'}
    )

    # 关联关系
    daily_report = relationship("DailyReport", back_populates="audit_logs")
    audit_user = relationship("UserProfile", foreign_keys=[audit_user_id])

    def __repr__(self):
        return f"<DailyReportAuditLog(id={self.id}, report_id={self.daily_report_id}, action={self.action})>"