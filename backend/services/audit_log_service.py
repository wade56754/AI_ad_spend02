"""
审计日志服务
Version: 1.0
Author: Claude Code (full_pipeline)

提供简单的审计日志记录功能，与 ad_account_service 等服务集成。
"""

import logging
from datetime import datetime
from typing import Optional, Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AuditLogService:
    """审计日志服务类"""

    def __init__(self, db: Session):
        """
        初始化审计日志服务

        Args:
            db: 数据库会话
        """
        self.db = db

    async def log_action(
        self,
        user_id: Any,
        action: str,
        resource_type: str,
        resource_id: Any,
        details: Optional[str] = None,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None
    ) -> None:
        """
        记录审计日志

        Args:
            user_id: 执行操作的用户ID
            action: 操作类型 (create, update, delete, status_change, etc.)
            resource_type: 资源类型 (ad_account, project, etc.)
            resource_id: 资源ID
            details: 操作详情描述
            old_value: 变更前的值
            new_value: 变更后的值
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": str(user_id) if user_id else None,
            "action": action,
            "resource_type": resource_type,
            "resource_id": str(resource_id) if resource_id else None,
            "details": details,
            "old_value": old_value,
            "new_value": new_value
        }

        # 记录到日志系统
        logger.info(f"AUDIT: {log_entry}")

        # TODO: 如果需要持久化到数据库，可以在这里添加
        # 例如写入 AuditLog 模型
        # audit_log = AuditLog(**log_entry)
        # self.db.add(audit_log)
        # self.db.commit()

    def log_action_sync(
        self,
        user_id: Any,
        action: str,
        resource_type: str,
        resource_id: Any,
        details: Optional[str] = None,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None
    ) -> None:
        """
        同步版本的审计日志记录

        与 log_action 功能相同，但不是异步方法
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": str(user_id) if user_id else None,
            "action": action,
            "resource_type": resource_type,
            "resource_id": str(resource_id) if resource_id else None,
            "details": details,
            "old_value": old_value,
            "new_value": new_value
        }

        logger.info(f"AUDIT: {log_entry}")
