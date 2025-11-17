"""
系统日志模型
用于记录系统操作日志
"""

from datetime import datetime, timezone
from typing import Dict, Any
from uuid import UUID

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.declarative import declarative_base

from core.db import Base


class Log(Base):
    """系统日志表"""
    __tablename__ = "system_logs"

    id = Column(String(36), primary_key=True)
    actor_id = Column(String(255), nullable=True, index=True)  # 操作者ID
    action = Column(String(100), nullable=False, index=True)   # 操作类型
    target_table = Column(String(255), nullable=True, index=True)  # 目标表名
    target_id = Column(String(255), nullable=True, index=True)  # 目标记录ID
    before_data = Column(JSON, nullable=True)  # 操作前数据
    after_data = Column(JSON, nullable=True)   # 操作后数据
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    def __repr__(self):
        return f"<Log(id={self.id}, action={self.action}, actor_id={self.actor_id})>"