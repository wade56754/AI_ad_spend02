"""
通知系统模块
包含通知、消息、系统配置等相关模型
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, BigInteger, DateTime, ForeignKey, String, Text, Boolean, Integer, Index, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, UUID, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.db import Base


class NotificationType(str, Enum):
    """通知类型枚举"""
    SYSTEM = "system"                    # 系统通知
    ANOMALY = "anomaly"                  # 异常告警
    APPROVAL = "approval"                # 审批通知
    REMINDER = "reminder"                # 提醒通知
    REPORT = "report"                    # 报表通知
    MAINTENANCE = "maintenance"          # 维护通知
    SECURITY = "security"                # 安全通知
    PERFORMANCE = "performance"          # 性能通知


class NotificationChannel(str, Enum):
    """通知渠道枚举"""
    IN_APP = "in_app"                    # 应用内通知
    EMAIL = "email"                      # 邮件通知
    SMS = "sms"                          # 短信通知
    WEBHOOK = "webhook"                  # Webhook通知
    BROWSER = "browser"                  # 浏览器推送
    SLACK = "slack"                      # Slack通知
    WECHAT = "wechat"                    # 微信通知


class NotificationPriority(str, Enum):
    """通知优先级枚举"""
    LOW = "low"                          # 低优先级
    NORMAL = "normal"                    # 普通优先级
    HIGH = "high"                        # 高优先级
    URGENT = "urgent"                    # 紧急优先级


class NotificationStatus(str, Enum):
    """通知状态枚举"""
    PENDING = "pending"                  # 待发送
    SENDING = "sending"                  # 发送中
    SENT = "sent"                        # 已发送
    DELIVERED = "delivered"              # 已送达
    READ = "read"                        # 已读
    FAILED = "failed"                    # 发送失败
    CANCELLED = "cancelled"              # 已取消


class Notification(Base):
    """通知表 - 统一管理所有系统通知"""
    __tablename__ = "notifications"

    # 主键
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 通知基本信息
    notification_number = Column(String(50), unique=True, nullable=False, comment="通知编号")
    title = Column(String(255), nullable=False, comment="通知标题")
    content = Column(Text, nullable=False, comment="通知内容")
    summary = Column(String(500), nullable=True, comment="通知摘要")

    # 通知分类
    notification_type = Column(SQLEnum(NotificationType), nullable=False, comment="通知类型")
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL, comment="优先级")
    category = Column(String(50), nullable=True, comment="业务分类")

    # 接收者信息
    recipient_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, comment="接收人ID")
    recipient_role = Column(String(50), nullable=True, comment="接收人角色")
    recipient_email = Column(String(255), nullable=True, comment="接收人邮箱")
    recipient_phone = Column(String(20), nullable=True, comment="接收人电话")

    # 发送者信息
    sender_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="发送人ID")
    sender_name = Column(String(255), nullable=True, comment="发送人姓名")
    is_system_notification = Column(Boolean, default=False, comment="是否系统通知")

    # 发送渠道
    channels = Column(JSON, nullable=False, comment="发送渠道配置")
    primary_channel = Column(SQLEnum(NotificationChannel), nullable=False, comment="主要渠道")

    # 关联信息
    related_entity_type = Column(String(50), nullable=True, comment="关联实体类型")
    related_entity_id = Column(PG_UUID(as_uuid=True), nullable=True, comment="关联实体ID")
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, comment="项目ID")
    ad_account_id = Column(PG_UUID(as_uuid=True), ForeignKey("ad_accounts.id"), nullable=True, comment="广告账户ID")

    # 通知状态和时间
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False, comment="通知状态")
    scheduled_at = Column(DateTime, nullable=True, comment="计划发送时间")
    sent_at = Column(DateTime, nullable=True, comment="发送时间")
    read_at = Column(DateTime, nullable=True, comment="阅读时间")
    expires_at = Column(DateTime, nullable=True, comment="过期时间")

    # 发送结果
    delivery_attempts = Column(Integer, default=0, comment="发送尝试次数")
    last_error = Column(Text, nullable=True, comment="最后错误信息")
    delivery_details = Column(JSON, nullable=True, comment="发送详情")

    # 动作配置
    action_buttons = Column(JSON, nullable=True, comment="动作按钮配置")
    action_url = Column(String(500), nullable=True, comment="动作链接")
    action_required = Column(Boolean, default=False, comment="是否需要动作")

    # 通知模板和参数
    template_name = Column(String(100), nullable=True, comment="模板名称")
    template_parameters = Column(JSON, nullable=True, comment="模板参数")

    # 批次信息
    batch_id = Column(String(100), nullable=True, comment="批次ID")
    is_batch_notification = Column(Boolean, default=False, comment="是否批量通知")

    # 元数据和上下文
    notification_metadata = Column(JSON, nullable=True, comment="通知元数据")
    context_data = Column(JSON, nullable=True, comment="上下文数据")

    # 系统字段
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    deleted_at = Column(DateTime, nullable=True, comment="软删除时间")

    # 索引
    __table_args__ = (
        Index('idx_notification_number', 'notification_number'),
        Index('idx_notification_recipient', 'recipient_id'),
        Index('idx_notification_type_status', 'notification_type', 'status'),
        Index('idx_notification_priority', 'priority'),
        Index('idx_notification_channel', 'primary_channel'),
        Index('idx_notification_project', 'project_id'),
        Index('idx_notification_account', 'ad_account_id'),
        Index('idx_notification_created', 'created_at'),
        Index('idx_notification_scheduled', 'scheduled_at'),
        Index('idx_notification_read', 'read_at'),
        Index('idx_notification_deleted_at', 'deleted_at'),
        {'comment': '通知表 - 统一管理所有系统通知'}
    )

    # 关系
    recipient = relationship("User", foreign_keys=[recipient_id])
    sender = relationship("User", foreign_keys=[sender_id])
    project = relationship("Project", foreign_keys=[project_id])
    ad_account = relationship("AdAccount", foreign_keys=[ad_account_id])


class NotificationTemplate(Base):
    """通知模板表 - 管理通知消息模板"""
    __tablename__ = "notification_templates"

    # 主键
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 模板基本信息
    template_name = Column(String(100), unique=True, nullable=False, comment="模板名称")
    template_code = Column(String(50), unique=True, nullable=False, comment="模板代码")
    title = Column(String(255), nullable=False, comment="模板标题")
    content = Column(Text, nullable=False, comment="模板内容")
    summary = Column(String(500), nullable=True, comment="模板摘要")

    # 模板分类
    notification_type = Column(SQLEnum(NotificationType), nullable=False, comment="通知类型")
    language = Column(String(10), default="zh-CN", comment="语言")
    category = Column(String(50), nullable=True, comment="业务分类")

    # 模板状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_default = Column(Boolean, default=False, comment="是否默认模板")
    version = Column(Integer, default=1, comment="模板版本")

    # 模板参数
    parameters = Column(JSON, nullable=True, comment="模板参数定义")
    default_parameters = Column(JSON, nullable=True, comment="默认参数值")
    validation_rules = Column(JSON, nullable=True, comment="参数验证规则")

    # 支持的渠道
    supported_channels = Column(JSON, nullable=True, comment="支持的渠道")
    channel_specific_content = Column(JSON, nullable=True, comment="渠道特定内容")

    # 使用统计
    usage_count = Column(Integer, default=0, comment="使用次数")
    last_used_at = Column(DateTime, nullable=True, comment="最后使用时间")

    # 维护信息
    created_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, comment="创建人")
    updated_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="更新人")
    notes = Column(Text, nullable=True, comment="备注信息")

    # 系统字段
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    deleted_at = Column(DateTime, nullable=True, comment="软删除时间")

    # 索引
    __table_args__ = (
        Index('idx_template_code', 'template_code'),
        Index('idx_template_type', 'notification_type'),
        Index('idx_template_language', 'language'),
        Index('idx_template_active', 'is_active'),
        Index('idx_template_category', 'category'),
        Index('idx_template_created', 'created_at'),
        Index('idx_template_deleted_at', 'deleted_at'),
        {'comment': '通知模板表 - 管理通知消息模板'}
    )

    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])


class SystemConfig(Base):
    """系统配置表 - 管理系统全局配置"""
    __tablename__ = "system_configs"

    # 主键
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 配置基本信息
    config_key = Column(String(100), unique=True, nullable=False, comment="配置键")
    config_name = Column(String(255), nullable=False, comment="配置名称")
    config_description = Column(Text, nullable=True, comment="配置描述")

    # 配置分类
    category = Column(String(50), nullable=False, comment="配置分类")
    subcategory = Column(String(50), nullable=True, comment="子分类")

    # 配置值
    config_value = Column(JSON, nullable=True, comment="配置值")
    default_value = Column(JSON, nullable=True, comment="默认值")
    data_type = Column(String(20), default="string", comment="数据类型")

    # 配置约束
    is_required = Column(Boolean, default=False, comment="是否必需")
    is_encrypted = Column(Boolean, default=False, comment="是否加密")
    is_readonly = Column(Boolean, default=False, comment="是否只读")
    validation_rules = Column(JSON, nullable=True, comment="验证规则")

    # 配置状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    environment = Column(String(20), default="production", comment="环境: development, staging, production")

    # 权限控制
    access_roles = Column(JSON, nullable=True, comment="访问角色")
    edit_roles = Column(JSON, nullable=True, comment="编辑角色")

    # 版本控制
    version = Column(Integer, default=1, comment="配置版本")
    previous_value = Column(JSON, nullable=True, comment="之前的值")

    # 缓存相关
    cache_ttl = Column(Integer, nullable=True, comment="缓存时间（秒）")
    cache_key = Column(String(255), nullable=True, comment="缓存键")

    # 使用统计
    last_accessed_at = Column(DateTime, nullable=True, comment="最后访问时间")
    access_count = Column(Integer, default=0, comment="访问次数")

    # 维护信息
    created_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, comment="创建人")
    updated_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="更新人")
    change_reason = Column(Text, nullable=True, comment="变更原因")

    # 系统字段
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    deleted_at = Column(DateTime, nullable=True, comment="软删除时间")

    # 索引
    __table_args__ = (
        Index('idx_config_key', 'config_key'),
        Index('idx_config_category', 'category'),
        Index('idx_config_subcategory', 'subcategory'),
        Index('idx_config_active', 'is_active'),
        Index('idx_config_environment', 'environment'),
        Index('idx_config_created', 'created_at'),
        Index('idx_config_updated', 'updated_at'),
        Index('idx_config_deleted_at', 'deleted_at'),
        {'comment': '系统配置表 - 管理系统全局配置'}
    )

    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])


class AuditLog(Base):
    """审计日志表（对齐 DATA_SCHEMA.md 3.1.4）"""
    __tablename__ = "audit_logs"

    # 主键：BIGSERIAL（对齐 DATA_SCHEMA）
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="审计日志ID")

    # 审计基本信息（对齐 DATA_SCHEMA）
    module = Column(String(100), nullable=False, comment="业务模块名")
    action = Column(String(50), nullable=False, comment="操作类型：create/update/delete/approve/...")
    entity_id = Column(String(64), nullable=True, comment="关联实体主键或编号")
    
    # 操作者信息（外键指向 user_profiles.id，UUID）
    performed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=False,
        comment="操作人ID"
    )
    role = Column(String(20), nullable=True, comment="操作者角色")
    
    # 审计信息（对齐 DATA_SCHEMA）
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(Text, nullable=True, comment="用户代理")
    payload_before = Column(JSON, nullable=True, server_default='{}', comment="变更前数据（JSONB）")
    payload_after = Column(JSON, nullable=True, server_default='{}', comment="变更后数据（JSONB）")
    
    # 时间信息（对齐 DATA_SCHEMA：TIMESTAMPTZ）
    created_at = Column(
        func.now(),
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )

    # 索引
    __table_args__ = (
        Index('idx_audit_module', 'module'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_performed_by', 'performed_by'),
        Index('idx_audit_created_at', 'created_at'),
        {'comment': '系统级审计日志表'}
    )

    # 关系
    performer = relationship("UserProfile", foreign_keys=[performed_by])