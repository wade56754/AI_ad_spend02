"""
AdSpendDaily Model - 外部导入日消耗
CodeBlock: CB-BE-002 (ResponseEnvelope pattern)

基准: DATA_SCHEMA.md v5.3 §3.3.3
功能: 存储从外部广告平台导入的消耗数据
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy import Column, String, Date, DateTime, Numeric, ForeignKey, Index, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base


class AdSpendDaily(Base):
    """
    外部导入日消耗表
    
    用途: 从 Facebook/Google/TikTok 等平台导入的原始消耗数据
    与 daily_reports 区别: 
      - daily_reports 是投手手动填写的日报
      - ad_spend_daily 是从广告平台 API/CSV 自动导入的数据
    """
    __tablename__ = "ad_spend_daily"

    # 主键 (UUID)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 数据来源
    source_platform = Column(String(50), nullable=False, index=True, 
                            comment="数据来源平台: facebook/google/tiktok/manual")
    
    # 账户标识 (外部平台的账户ID/Code)
    ad_account_code = Column(String(100), nullable=False, index=True,
                            comment="广告账户外部代码")
    
    # 关联内部账户 (可选)
    ad_account_id = Column(Integer, ForeignKey("ad_accounts.id"), nullable=True,
                          comment="关联的内部广告账户ID")
    
    # 消耗日期
    spend_date = Column(Date, nullable=False, index=True,
                       comment="消耗日期")
    
    # 消耗金额
    spend_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"),
                         comment="消耗金额")
    
    # 货币
    currency = Column(String(10), nullable=False, default="CNY",
                     comment="货币代码: CNY/USD/HKD")
    
    # 指标数据
    impressions = Column(Integer, default=0, comment="曝光量")
    clicks = Column(Integer, default=0, comment="点击量")
    conversions = Column(Integer, default=0, comment="转化数")
    
    # 原始数据 (JSONB)
    raw_payload = Column(JSONB, nullable=True,
                        comment="原始导入数据 (JSON格式)")
    
    # 导入信息
    imported_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True,
                        comment="导入人ID")
    imported_at = Column(DateTime(timezone=True), server_default=func.now(),
                        comment="导入时间")
    
    # 审计字段
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系 - 暂时注释，需要在 AdAccount 添加反向关系后启用
    # ad_account = relationship("AdAccount", back_populates="spend_records", lazy="joined")
    # importer = relationship("User", foreign_keys=[imported_by], lazy="joined")

    # 索引
    __table_args__ = (
        Index("idx_ad_spend_daily_date", "spend_date"),
        Index("idx_ad_spend_daily_account", "ad_account_code"),
        Index("idx_ad_spend_daily_platform", "source_platform"),
        Index("idx_ad_spend_daily_date_account", "spend_date", "ad_account_code"),
    )

    def __repr__(self):
        return f"<AdSpendDaily {self.spend_date} {self.ad_account_code} {self.spend_amount}>"
