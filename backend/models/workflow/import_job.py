"""
数据导入任务模型

用于追踪 CSV/Excel 数据导入任务的状态和结果。
支持 finance、ad_spend、leads 等多种导入类型。
"""
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import Column, BigInteger, String, Text, DateTime, Index, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func

from backend.models.base import Base, TimestampMixin


class ImportJobType(str, PyEnum):
    """导入任务类型枚举"""
    FINANCE = "finance"      # 财务数据导入
    AD_SPEND = "ad_spend"    # 广告消耗数据导入
    LEADS = "leads"          # 线索数据导入


class ImportJobStatus(str, PyEnum):
    """导入任务状态枚举"""
    PENDING = "pending"        # 待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败


class ImportJob(Base, TimestampMixin):
    """
    数据导入任务表

    用于记录和追踪数据导入操作，包括：
    - CSV/Excel 文件上传
    - 数据解析和验证
    - 导入结果和错误日志

    字段说明:
    - id: 任务唯一标识 (UUID)
    - type: 导入类型 (finance/ad_spend/leads)
    - status: 任务状态 (pending/processing/completed/failed)
    - file_path: 原始文件名/路径
    - file_hash: 文件 SHA256 哈希（用于去重检测）
    - error_log: 错误日志 (JSONB 数组)
    - created_by: 创建者用户 ID
    - updated_by: 最后更新者用户 ID
    """
    __tablename__ = 'import_jobs'

    # 主键 - 使用 UUID
    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="导入任务ID"
    )

    # 任务类型
    type = Column(
        String(50),
        nullable=False,
        default=ImportJobType.FINANCE.value,
        comment="导入类型: finance/ad_spend/leads"
    )

    # 任务状态
    status = Column(
        String(20),
        nullable=False,
        default=ImportJobStatus.PENDING.value,
        comment="任务状态: pending/processing/completed/failed"
    )

    # 文件信息
    file_path = Column(
        String(500),
        nullable=True,
        comment="原始文件名/路径"
    )

    file_hash = Column(
        String(64),
        nullable=True,
        index=True,
        comment="文件 SHA256 哈希"
    )

    # 错误日志 (JSONB 数组格式)
    error_log = Column(
        JSON,
        nullable=True,
        default=list,
        comment="错误日志，格式: [{row: int, error: str}, ...]"
    )

    # 用户关联
    created_by = Column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="创建者用户ID"
    )

    updated_by = Column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="最后更新者用户ID"
    )

    # 索引
    __table_args__ = (
        Index('idx_import_jobs_status', 'status'),
        Index('idx_import_jobs_type', 'type'),
        Index('idx_import_jobs_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<ImportJob(id={self.id}, type={self.type}, status={self.status})>"
