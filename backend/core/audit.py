"""
数据库审计和日志模块
提供数据操作审计和安全日志功能
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, List
from enum import Enum

from sqlalchemy import Column, String, DateTime, Text, Integer, event, DDL
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from backend.core.db import Base, get_db_session


class AuditAction(str, Enum):
    """审计操作类型"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SELECT = "select"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    IMPORT = "import"
    BACKUP = "backup"
    RESTORE = "restore"


class AuditLevel(str, Enum):
    """审计级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# 审计日志表
class AuditLog(Base):
    """审计日志表"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=True, index=True)  # 操作用户ID
    action = Column(String(50), nullable=False, index=True)   # 操作类型
    table_name = Column(String(255), nullable=True, index=True)  # 表名
    record_id = Column(String(255), nullable=True, index=True)  # 记录ID
    old_values = Column(Text, nullable=True)  # 旧值（JSON）
    new_values = Column(Text, nullable=True)  # 新值（JSON）
    ip_address = Column(String(45), nullable=True)  # IP地址
    user_agent = Column(Text, nullable=True)   # 用户代理
    level = Column(String(20), nullable=False, default=AuditLevel.MEDIUM.value)
    description = Column(Text, nullable=True)  # 操作描述
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user_id={self.user_id})>"


class SecurityEvent(Base):
    """安全事件表"""
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(100), nullable=False, index=True)  # 事件类型
    user_id = Column(String(255), nullable=True, index=True)     # 用户ID
    ip_address = Column(String(45), nullable=True)                # IP地址
    user_agent = Column(Text, nullable=True)                     # 用户代理
    details = Column(Text, nullable=True)                        # 事件详情（JSON）
    severity = Column(String(20), nullable=False, default="medium")  # 严重程度
    resolved = Column(String(10), default="false")               # 是否已解决
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<SecurityEvent(id={self.id}, type={self.event_type}, severity={self.severity})>"


class AuditLogger:
    """审计日志记录器"""

    def __init__(self):
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)

        # 创建文件处理器
        handler = logging.FileHandler("logs/audit.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_action(
        self,
        action: AuditAction,
        user_id: str = None,
        table_name: str = None,
        record_id: str = None,
        old_values: Dict[str, Any] = None,
        new_values: Dict[str, Any] = None,
        ip_address: str = None,
        user_agent: str = None,
        level: AuditLevel = AuditLevel.MEDIUM,
        description: str = None
    ) -> AuditLog:
        """记录审计日志"""
        try:
            # 创建审计记录
            audit_log = AuditLog(
                user_id=user_id,
                action=action.value,
                table_name=table_name,
                record_id=str(record_id) if record_id else None,
                old_values=json.dumps(old_values, ensure_ascii=False) if old_values else None,
                new_values=json.dumps(new_values, ensure_ascii=False) if new_values else None,
                ip_address=ip_address,
                user_agent=user_agent,
                level=level.value,
                description=description
            )

            # 保存到数据库
            with get_db_session() as session:
                session.add(audit_log)
                session.commit()

            # 记录到文件日志
            log_message = f"{action.value} - {table_name} - {record_id} - User: {user_id}"
            if description:
                log_message += f" - {description}"

            if level == AuditLevel.CRITICAL:
                self.logger.critical(log_message)
            elif level == AuditLevel.HIGH:
                self.logger.error(log_message)
            elif level == AuditLevel.MEDIUM:
                self.logger.warning(log_message)
            else:
                self.logger.info(log_message)

            return audit_log

        except Exception as e:
            self.logger.error(f"审计日志记录失败: {e}")
            raise

    def log_create(
        self,
        table_name: str,
        record_id: str,
        new_values: Dict[str, Any],
        user_id: str = None,
        **kwargs
    ):
        """记录创建操作"""
        return self.log_action(
            action=AuditAction.CREATE,
            table_name=table_name,
            record_id=record_id,
            new_values=new_values,
            user_id=user_id,
            **kwargs
        )

    def log_update(
        self,
        table_name: str,
        record_id: str,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        user_id: str = None,
        **kwargs
    ):
        """记录更新操作"""
        return self.log_action(
            action=AuditAction.UPDATE,
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values,
            user_id=user_id,
            **kwargs
        )

    def log_delete(
        self,
        table_name: str,
        record_id: str,
        old_values: Dict[str, Any],
        user_id: str = None,
        **kwargs
    ):
        """记录删除操作"""
        return self.log_action(
            action=AuditAction.DELETE,
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            user_id=user_id,
            **kwargs
        )

    def log_login(self, user_id: str, ip_address: str = None, user_agent: str = None, success: bool = True):
        """记录登录操作"""
        level = AuditLevel.LOW if success else AuditLevel.HIGH
        description = "用户登录成功" if success else "用户登录失败"

        return self.log_action(
            action=AuditAction.LOGIN,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            level=level,
            description=description
        )

    def log_logout(self, user_id: str, ip_address: str = None, user_agent: str = None):
        """记录登出操作"""
        return self.log_action(
            action=AuditAction.LOGOUT,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            level=AuditLevel.LOW,
            description="用户登出"
        )

    def log_export(
        self,
        table_name: str,
        record_count: int,
        user_id: str = None,
        **kwargs
    ):
        """记录数据导出操作"""
        description = f"导出数据: {table_name} ({record_count}条记录)"
        level = AuditLevel.MEDIUM if record_count < 1000 else AuditLevel.HIGH

        return self.log_action(
            action=AuditAction.EXPORT,
            table_name=table_name,
            user_id=user_id,
            level=level,
            description=description,
            **kwargs
        )


class SecurityEventLogger:
    """安全事件记录器"""

    def __init__(self):
        self.logger = logging.getLogger("security")
        self.logger.setLevel(logging.WARNING)

        # 创建文件处理器
        handler = logging.FileHandler("logs/security.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_security_event(
        self,
        event_type: str,
        severity: str = "medium",
        user_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        details: Dict[str, Any] = None,
        description: str = None
    ) -> SecurityEvent:
        """记录安全事件"""
        try:
            # 创建安全事件记录
            security_event = SecurityEvent(
                event_type=event_type,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details=json.dumps(details, ensure_ascii=False) if details else None,
                severity=severity
            )

            # 保存到数据库
            with get_db_session() as session:
                session.add(security_event)
                session.commit()

            # 记录到文件日志
            log_message = f"{event_type} - User: {user_id} - IP: {ip_address}"
            if description:
                log_message += f" - {description}"
            if details:
                log_message += f" - Details: {json.dumps(details, ensure_ascii=False)}"

            if severity == "critical":
                self.logger.critical(log_message)
            elif severity == "high":
                self.logger.error(log_message)
            elif severity == "medium":
                self.logger.warning(log_message)
            else:
                self.logger.info(log_message)

            return security_event

        except Exception as e:
            self.logger.error(f"安全事件记录失败: {e}")
            raise

    def log_failed_login(self, username: str, ip_address: str, user_agent: str = None, reason: str = None):
        """记录登录失败"""
        details = {
            "username": username,
            "reason": reason or "invalid_credentials"
        }

        return self.log_security_event(
            event_type="login_failed",
            severity="high",
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            description=f"登录失败: {username} - {reason or '凭据无效'}"
        )

    def log_brute_force_attempt(self, ip_address: str, attempts: int, usernames: List[str]):
        """记录暴力破解尝试"""
        details = {
            "attempts": attempts,
            "usernames": usernames,
            "ip_address": ip_address
        }

        return self.log_security_event(
            event_type="brute_force_attempt",
            severity="critical",
            ip_address=ip_address,
            details=details,
            description=f"检测到暴力破解尝试: {attempts}次失败尝试"
        )

    def log_suspicious_activity(self, user_id: str, activity_type: str, ip_address: str, details: Dict = None):
        """记录可疑活动"""
        return self.log_security_event(
            event_type=f"suspicious_{activity_type}",
            severity="high",
            user_id=user_id,
            ip_address=ip_address,
            details=details,
            description=f"检测到可疑活动: {activity_type}"
        )

    def log_data_access_violation(self, user_id: str, resource: str, ip_address: str, details: Dict = None):
        """记录数据访问违规"""
        return self.log_security_event(
            event_type="data_access_violation",
            severity="critical",
            user_id=user_id,
            ip_address=ip_address,
            details=details,
            description=f"数据访问违规: {resource}"
        )

    def log_privilege_escalation(self, user_id: str, attempted_role: str, ip_address: str):
        """记录权限提升尝试"""
        details = {
            "attempted_role": attempted_role,
            "current_role": None  # 可以从用户数据获取
        }

        return self.log_security_event(
            event_type="privilege_escalation_attempt",
            severity="critical",
            user_id=user_id,
            ip_address=ip_address,
            details=details,
            description=f"权限提升尝试: {attempted_role}"
        )


# 全局审计记录器实例
audit_logger = AuditLogger()
security_logger = SecurityEventLogger()


# SQLAlchemy事件监听器，用于自动审计
def setup_audit_triggers():
    """设置审计触发器"""

    @event.listens_for(Session, "before_flush")
    def receive_before_flush(session, context, instances):
        """在会话刷新前记录审计日志"""
        try:
            for instance in session.new:
                # 新建记录
                if hasattr(instance, '__tablename__') and hasattr(instance, 'id'):
                    audit_logger.log_create(
                        table_name=instance.__tablename__,
                        record_id=str(instance.id),
                        new_values=instance_to_dict(instance),
                        user_id=get_current_user_from_session(session)
                    )

            for instance in session.dirty:
                # 更新记录
                if hasattr(instance, '__tablename__') and hasattr(instance, 'id'):
                    # 获取旧值
                    old_values = get_old_values(session, instance)
                    new_values = instance_to_dict(instance)

                    if old_values != new_values:
                        audit_logger.log_update(
                            table_name=instance.__tablename__,
                            record_id=str(instance.id),
                            old_values=old_values,
                            new_values=new_values,
                            user_id=get_current_user_from_session(session)
                        )

            for instance in session.deleted:
                # 删除记录
                if hasattr(instance, '__tablename__') and hasattr(instance, 'id'):
                    audit_logger.log_delete(
                        table_name=instance.__tablename__,
                        record_id=str(instance.id),
                        old_values=instance_to_dict(instance),
                        user_id=get_current_user_from_session(session)
                    )

        except Exception as e:
            print(f"审计触发器错误: {e}")


def instance_to_dict(instance) -> Dict[str, Any]:
    """将实例转换为字典"""
    result = {}
    for column in instance.__table__.columns:
        value = getattr(instance, column.name)
        if value is not None:
            result[column.name] = value
    return result


def get_old_values(session, instance) -> Dict[str, Any]:
    """获取实例的旧值"""
    try:
        # 从数据库获取原始值
        original = session.query(instance.__class__).get(instance.id)
        if original:
            return instance_to_dict(original)
    except:
        pass
    return {}


def get_current_user_from_session(session) -> Optional[str]:
    """从会话中获取当前用户ID"""
    try:
        # 这里需要根据实际的认证系统实现
        # 可以从session的info中获取用户信息
        if hasattr(session, 'info') and 'user_id' in session.info:
            return session.info['user_id']
    except:
        pass
    return None


# 审计查询功能
class AuditQuery:
    """审计查询工具"""

    @staticmethod
    def get_user_actions(
        user_id: str,
        start_date: datetime = None,
        end_date: datetime = None,
        action: AuditAction = None
    ) -> List[AuditLog]:
        """获取用户操作记录"""
        with get_db_session() as session:
            query = session.query(AuditLog).filter(AuditLog.user_id == user_id)

            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)
            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)
            if action:
                query = query.filter(AuditLog.action == action.value)

            return query.order_by(AuditLog.created_at.desc()).all()

    @staticmethod
    def get_table_actions(
        table_name: str,
        start_date: datetime = None,
        end_date: datetime = None,
        action: AuditAction = None
    ) -> List[AuditLog]:
        """获取表操作记录"""
        with get_db_session() as session:
            query = session.query(AuditLog).filter(AuditLog.table_name == table_name)

            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)
            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)
            if action:
                query = query.filter(AuditLog.action == action.value)

            return query.order_by(AuditLog.created_at.desc()).all()

    @staticmethod
    def get_security_events(
        severity: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        resolved: bool = None
    ) -> List[SecurityEvent]:
        """获取安全事件"""
        with get_db_session() as session:
            query = session.query(SecurityEvent)

            if severity:
                query = query.filter(SecurityEvent.severity == severity)
            if start_date:
                query = query.filter(SecurityEvent.created_at >= start_date)
            if end_date:
                query = query.filter(SecurityEvent.created_at <= end_date)
            if resolved is not None:
                query = query.filter(SecurityEvent.resolved == str(resolved).lower())

            return query.order_by(SecurityEvent.created_at.desc()).all()


# 初始化审计系统
def init_audit_system():
    """初始化审计系统"""
    try:
        # 创建日志目录
        import os
        os.makedirs("logs", exist_ok=True)

        # 设置审计触发器
        setup_audit_triggers()

        print("✅ 审计系统初始化完成")
        return True
    except Exception as e:
        print(f"❌ 审计系统初始化失败: {e}")
        return False