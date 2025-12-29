"""
渠道管理服务层 (TASK-CHAN-002)

SoT References:
- DATA_SCHEMA.md v5.6 §3.2.4 channels 表
- MASTER.md v4.6 §2.4 (6角色模型)
- ERROR_CODES_SOT.md v2.1 (错误码)

业务规则:
- BR-CHAN-002: 仅 account_manager/admin 可创建渠道
- BR-CHAN-003: 渠道名称唯一

Version: 1.0
Author: Claude Code (AI 代码工厂)
"""
import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from backend.models import Channel, User
from backend.exceptions.custom_exceptions import (
    ResourceConflictError,
    PermissionDeniedError,
)

logger = logging.getLogger(__name__)


class ChannelService:
    """渠道管理服务"""

    # BR-CHAN-002: 允许创建渠道的角色
    ALLOWED_CREATE_ROLES = ["admin", "account_manager"]

    def __init__(self, db: Session):
        self.db = db

    def _get_user_role(self, user: User) -> str:
        """获取用户角色字符串"""
        role = user.role
        if hasattr(role, 'value'):
            return role.value
        return str(role)

    def _can_create_channel(self, user: User) -> bool:
        """
        BR-CHAN-002: 检查用户是否有权限创建渠道
        仅 account_manager/admin 可创建
        """
        user_role = self._get_user_role(user)
        return user_role in self.ALLOWED_CREATE_ROLES

    def _check_name_unique(self, name: str, exclude_id: Optional[UUID] = None) -> bool:
        """
        BR-CHAN-003: 检查渠道名称是否唯一
        """
        query = self.db.query(Channel).filter(Channel.name == name)
        if exclude_id:
            query = query.filter(Channel.id != exclude_id)
        return query.first() is None

    def create_channel(
        self,
        name: str,
        platform: str,
        current_user: User,
        fee_rate: Optional[Decimal] = None,
        status: str = "active",
        risk_level: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Channel:
        """
        创建渠道 (TASK-CHAN-002)

        Args:
            name: 渠道名称 (必填, 唯一)
            platform: 平台 (必填)
            current_user: 当前用户
            fee_rate: 手续费率 (存储到 metadata)
            status: 渠道状态 (默认 active)
            risk_level: 风险等级
            metadata: 扩展数据

        Returns:
            创建的 Channel 对象

        Raises:
            PermissionDeniedError: 无权限创建渠道 (AUTH_403)
            ResourceConflictError: 渠道名称已存在 (BIZ_001)
        """
        # BR-CHAN-002: 权限检查
        if not self._can_create_channel(current_user):
            logger.warning(
                f"[AUDIT] 渠道创建权限拒绝: user_id={current_user.id}, role={self._get_user_role(current_user)}"
            )
            raise PermissionDeniedError("无权限创建渠道")

        # BR-CHAN-003: 名称唯一性检查
        if not self._check_name_unique(name):
            logger.info(f"[AUDIT] 渠道名称冲突: name={name}")
            raise ResourceConflictError("渠道名称已存在")

        # 构建 metadata (含 fee_rate)
        channel_metadata = metadata or {}
        if fee_rate is not None:
            channel_metadata["fee_rate"] = str(fee_rate)

        # 创建渠道
        channel = Channel(
            id=uuid4(),
            name=name,
            platform=platform,
            status=status,
            risk_level=risk_level,
            created_by=current_user.id,
            channel_metadata=channel_metadata,
        )

        self.db.add(channel)
        self.db.flush()

        logger.info(
            f"[AUDIT] 渠道创建成功: channel_id={channel.id}, name={name}, "
            f"platform={platform}, operator={current_user.id}"
        )

        return channel


def get_channel_service(db: Session) -> ChannelService:
    """获取渠道服务实例"""
    return ChannelService(db)
