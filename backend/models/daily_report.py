"""
日报管理数据模型
Version: 1.0
Author: Claude协作开发
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime,
    DECIMAL, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class DailyReport(Base):
    """日报主表"""
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_date = Column(Date, nullable=False, comment="报表日期")
    ad_account_id = Column(Integer, ForeignKey("ad_accounts.id"), nullable=False, comment="广告账户ID")

    # 广告信息
    campaign_name = Column(String(200), comment="广告系列名称")
    ad_group_name = Column(String(200), comment="广告组名称")
    ad_creative_name = Column(String(200), comment="广告创意名称")

    # 投放数据
    impressions = Column(Integer, default=0, comment="展示次数")
    clicks = Column(Integer, default=0, comment="点击次数")
    spend = Column(DECIMAL(12, 2), default=0.00, comment="消耗金额")
    conversions = Column(Integer, default=0, comment="转化次数")
    new_follows = Column(Integer, default=0, comment="新增粉丝数")
    cpa = Column(DECIMAL(10, 2), comment="CPA")
    roas = Column(DECIMAL(10, 2), comment="ROAS")

    # 状态和备注
    status = Column(
        String(20),
        default="pending",
        comment="审核状态: pending/approved/rejected"
    )
    notes = Column(Text, comment="备注说明")
    audit_notes = Column(Text, comment="审核说明")
    audit_user_id = Column(Integer, ForeignKey("users.id"), comment="审核人ID")
    audit_time = Column(DateTime, comment="审核时间")

    # 创建和更新信息
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    # 唯一约束：每个账户每天只能有一条日报
    __table_args__ = (
        UniqueConstraint('report_date', 'ad_account_id', name='uq_daily_reports_date_account'),
        Index('idx_daily_reports_date', 'report_date'),
        Index('idx_daily_reports_account', 'ad_account_id'),
        Index('idx_daily_reports_status', 'status'),
        Index('idx_daily_reports_created_by', 'created_by'),
        Index('idx_daily_reports_audit_user', 'audit_user_id'),
        # 复合索引优化查询
        Index('idx_daily_reports_date_status', 'report_date', 'status'),
        Index('idx_daily_reports_account_date', 'ad_account_id', 'report_date'),
        {'comment': '日报数据表'}
    )

    # 关联关系
    ad_account = relationship("AdAccount", back_populates="daily_reports")
    creator = relationship("User", foreign_keys=[created_by])
    auditor = relationship("User", foreign_keys=[audit_user_id])
    audit_logs = relationship("DailyReportAuditLog", back_populates="daily_report")

    def __repr__(self):
        return f"<DailyReport(id={self.id}, date={self.report_date}, account_id={self.ad_account_id})>"


class DailyReportAuditLog(Base):
    """日报审核日志表"""
    __tablename__ = "daily_report_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    daily_report_id = Column(
        Integer,
        ForeignKey("daily_reports.id", ondelete="CASCADE"),
        nullable=False,
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

    # 审核信息
    audit_user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="操作人ID"
    )
    audit_time = Column(DateTime, default=func.now(), comment="操作时间")
    audit_notes = Column(Text, comment="操作说明")

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
    audit_user = relationship("User", foreign_keys=[audit_user_id])

    def __repr__(self):
        return f"<DailyReportAuditLog(id={self.id}, report_id={self.daily_report_id}, action={self.action})>"