"""
审计日志服务
记录所有关键操作的审计日志
"""
import json
from datetime import datetime
from typing import Any, Dict, Optional, Union
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.models.users import User


class AuditEvent:
    """审计事件类型"""
    # 用户操作
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    USER_CREATE = "USER_CREATE"
    USER_UPDATE = "USER_UPDATE"
    USER_DELETE = "USER_DELETE"
    USER_PASSWORD_CHANGE = "USER_PASSWORD_CHANGE"

    # 项目操作
    PROJECT_CREATE = "PROJECT_CREATE"
    PROJECT_UPDATE = "PROJECT_UPDATE"
    PROJECT_DELETE = "PROJECT_DELETE"
    PROJECT_STATUS_CHANGE = "PROJECT_STATUS_CHANGE"

    # 账户操作
    ACCOUNT_CREATE = "ACCOUNT_CREATE"
    ACCOUNT_UPDATE = "ACCOUNT_UPDATE"
    ACCOUNT_DELETE = "ACCOUNT_DELETE"
    ACCOUNT_ASSIGN = "ACCOUNT_ASSIGN"
    ACCOUNT_STATUS_CHANGE = "ACCOUNT_STATUS_CHANGE"

    # 财务操作
    TOPUP_REQUEST = "TOPUP_REQUEST"
    TOPUP_APPROVE = "TOPUP_APPROVE"
    TOPUP_REJECT = "TOPUP_REJECT"
    TOPUP_CONFIRM = "TOPUP_CONFIRM"
    RECONCILIATION_CREATE = "RECONCILIATION_CREATE"
    RECONCILIATION_APPROVE = "RECONCILIATION_APPROVE"

    # 报表操作
    REPORT_SUBMIT = "REPORT_SUBMIT"
    REPORT_REVIEW = "REPORT_REVIEW"
    REPORT_APPROVE = "REPORT_APPROVE"
    REPORT_REJECT = "REPORT_REJECT"

    # 数据操作
    DATA_IMPORT = "DATA_IMPORT"
    DATA_EXPORT = "DATA_EXPORT"
    DATA_MODIFY = "DATA_MODIFY"

    # 系统操作
    SYSTEM_CONFIG_CHANGE = "SYSTEM_CONFIG_CHANGE"
    SYSTEM_BACKUP = "SYSTEM_BACKUP"
    SYSTEM_RESTORE = "SYSTEM_RESTORE"

    # 安全操作
    SECURITY_BREACH = "SECURITY_BREACH"
    SECURITY_VIOLATION = "SECURITY_VIOLATION"
    PERMISSION_CHANGE = "PERMISSION_CHANGE"


class AuditLogger:
    """审计日志记录器"""

    def __init__(self, db: Session = None):
        self.db = db

    async def log(
        self,
        event_type: str,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[Union[int, str]] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> str:
        """记录审计日志

        Args:
            event_type: 事件类型
            user_id: 用户ID
            user_email: 用户邮箱
            resource_type: 资源类型（如：project, account, user）
            resource_id: 资源ID
            details: 详细信息（JSON格式）
            ip_address: IP地址
            user_agent: 用户代理
            request_id: 请求ID
            success: 是否成功
            error_message: 错误信息

        Returns:
            审计日志ID
        """
        audit_id = str(uuid4())

        # 构建审计日志记录
        audit_record = {
            "id": audit_id,
            "event_type": event_type,
            "user_id": user_id,
            "user_email": user_email,
            "resource_type": resource_type,
            "resource_id": str(resource_id) if resource_id else None,
            "details": json.dumps(details) if details else None,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "request_id": request_id,
            "success": success,
            "error_message": error_message,
            "created_at": datetime.utcnow(),
        }

        # 如果有数据库连接，保存到数据库
        if self.db:
            try:
                # TODO: 创建audit_logs表并保存
                # 目前先记录到应用日志
                pass
            except Exception as e:
                print(f"Failed to save audit log: {e}")

        # 记录到应用日志
        self._log_to_file(audit_record)

        return audit_id

    def _log_to_file(self, audit_record: Dict[str, Any]):
        """将审计日志记录到文件"""
        import logging

        # 创建审计日志记录器
        logger = logging.getLogger("audit")
        if not logger.handlers:
            handler = logging.FileHandler("logs/audit.log")
            formatter = logging.Formatter(
                '%(asctime)s - AUDIT - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        # 记录日志
        logger.info(json.dumps(audit_record, default=str, ensure_ascii=False))

    async def log_user_action(
        self,
        event_type: str,
        user: User,
        resource_type: Optional[str] = None,
        resource_id: Optional[Union[int, str]] = None,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Any] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> str:
        """记录用户操作日志

        Args:
            event_type: 事件类型
            user: 用户对象
            resource_type: 资源类型
            resource_id: 资源ID
            details: 详细信息
            request: FastAPI请求对象
            success: 是否成功
            error_message: 错误信息

        Returns:
            审计日志ID
        """
        # 从请求中提取信息
        ip_address = None
        user_agent = None
        request_id = None

        if request:
            ip_address = request.client.host
            user_agent = request.headers.get("user-agent")
            request_id = getattr(request.state, "request_id", None)

        return await self.log(
            event_type=event_type,
            user_id=user.id,
            user_email=user.email,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            success=success,
            error_message=error_message
        )

    async def log_login(
        self,
        user: User,
        ip_address: str,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> str:
        """记录登录日志"""
        return await self.log(
            event_type=AuditEvent.USER_LOGIN if success else AuditEvent.SECURITY_VIOLATION,
            user_id=user.id,
            user_email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
            details={"login_method": "jwt"}
        )

    async def log_permission_change(
        self,
        target_user_id: int,
        target_user_email: str,
        old_permissions: List[str],
        new_permissions: List[str],
        operator: User,
        ip_address: Optional[str] = None
    ) -> str:
        """记录权限变更日志"""
        return await self.log(
            event_type=AuditEvent.PERMISSION_CHANGE,
            user_id=operator.id,
            user_email=operator.email,
            resource_type="user",
            resource_id=target_user_id,
            ip_address=ip_address,
            details={
                "target_user": {
                    "id": target_user_id,
                    "email": target_user_email
                },
                "old_permissions": old_permissions,
                "new_permissions": new_permissions
            }
        )

    async def log_data_access(
        self,
        event_type: str,
        user: User,
        resource_type: str,
        resource_ids: List[Union[int, str]],
        access_type: str = "read",
        request: Optional[Any] = None
    ) -> str:
        """记录数据访问日志"""
        return await self.log(
            event_type=event_type,
            user_id=user.id,
            user_email=user.email,
            resource_type=resource_type,
            resource_id=", ".join(map(str, resource_ids)),
            details={
                "access_type": access_type,
                "count": len(resource_ids)
            },
            request=request
        )

    async def log_security_event(
        self,
        event_type: str,
        details: Dict[str, Any],
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """记录安全事件日志"""
        return await self.log(
            event_type=event_type,
            user_id=user_id,
            user_email=user_email,
            resource_type="system",
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False  # 安全事件默认为失败
        )


# 创建全局审计日志实例
audit_logger = AuditLogger()


# 便捷函数
async def log_audit(
    event_type: str,
    user: User,
    resource_type: Optional[str] = None,
    resource_id: Optional[Union[int, str]] = None,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Any] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> str:
    """记录审计日志的便捷函数"""
    return await audit_logger.log_user_action(
        event_type=event_type,
        user=user,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        request=request,
        success=success,
        error_message=error_message
    )


# 创建审计日志装饰器
def audit_action(event_type: str, resource_type: str = None):
    """审计装饰器

    Args:
        event_type: 事件类型
        resource_type: 资源类型
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # TODO: 实现装饰器逻辑
            # 需要从参数中提取用户、请求等信息
            return await func(*args, **kwargs)
        return wrapper
    return decorator