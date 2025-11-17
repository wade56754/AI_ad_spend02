"""
AI监控和风控模块
包含AI异常检测、账户生命周期预测、风控规则等模型
"""

from datetime import datetime, date
from sqlalchemy import Date
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Numeric, Boolean, Integer, Index, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from core.db import Base


class AnomalyType(str, Enum):
    """异常类型枚举"""
    SPENDING_SPIKE = "spending_spike"              # 支出异常激增
    PERFORMANCE_DECLINE = "performance_decline"    # 性能下降
    LEAD_QUALITY_DROP = "lead_quality_drop"        # 线索质量下降
    ACCOUNT_RISK = "account_risk"                  # 账户风险
    CONVERSION_ANOMALY = "conversion_anomaly"      # 转化异常
    TRAFFIC_ANOMALY = "traffic_anomaly"            # 流量异常
    BUDGET_DEPLETION = "budget_depletion"          # 预算耗尽
    FREQUENCY_ANOMALY = "frequency_anomaly"        # 频率异常


class AnomalySeverity(str, Enum):
    """异常严重程度枚举"""
    LOW = "low"                    # 低风险
    MEDIUM = "medium"              # 中风险
    HIGH = "high"                  # 高风险
    CRITICAL = "critical"          # 严重风险


class AnomalyStatus(str, Enum):
    """异常状态枚举"""
    DETECTED = "detected"          # 已检测
    INVESTIGATING = "investigating"  # 调查中
    CONFIRMED = "confirmed"        # 已确认
    RESOLVED = "resolved"          # 已解决
    IGNORED = "ignored"            # 忽略
    FALSE_POSITIVE = "false_positive"  # 误报


class RiskLevel(str, Enum):
    """风险等级枚举"""
    VERY_LOW = "very_low"          # 极低风险
    LOW = "low"                    # 低风险
    MEDIUM = "medium"              # 中等风险
    HIGH = "high"                  # 高风险
    VERY_HIGH = "very_high"        # 极高风险
    CRITICAL = "critical"          # 严重风险


class AIAnomalyDetection(Base):
    """AI异常检测表 - 记录系统检测到的各种异常"""
    __tablename__ = "ai_anomaly_detections"

    # 主键
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 异常基本信息
    anomaly_number = Column(String(50), unique=True, nullable=False, comment="异常编号")
    title = Column(String(255), nullable=False, comment="异常标题")
    description = Column(Text, nullable=True, comment="异常描述")

    # 异常分类
    anomaly_type = Column(SQLEnum(AnomalyType), nullable=False, comment="异常类型")
    severity = Column(SQLEnum(AnomalySeverity), nullable=False, comment="严重程度")
    status = Column(SQLEnum(AnomalyStatus), default=AnomalyStatus.DETECTED, nullable=False, comment="异常状态")

    # 关联信息
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, comment="项目ID")
    ad_account_id = Column(PG_UUID(as_uuid=True), ForeignKey("ad_accounts.id"), nullable=True, comment="广告账户ID")
    channel_id = Column(PG_UUID(as_uuid=True), ForeignKey("channels.id"), nullable=True, comment="渠道ID")
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="用户ID")

    # 异常数据和时间
    anomaly_date = Column(Date, nullable=False, comment="异常日期")
    detection_time = Column(DateTime, nullable=False, comment="检测时间")

    # 异常指标
    baseline_value = Column(Numeric(15, 2), default=0, comment="基线值")
    actual_value = Column(Numeric(15, 2), default=0, comment="实际值")
    deviation_percentage = Column(Numeric(5, 2), default=0, comment="偏差百分比")
    confidence_score = Column(Numeric(5, 4), default=0, comment="置信度分数")

    # 具体指标（根据异常类型）
    metric_name = Column(String(100), nullable=True, comment="指标名称")
    metric_value = Column(Numeric(15, 2), default=0, comment="指标值")
    threshold_value = Column(Numeric(15, 2), default=0, comment="阈值")

    # AI模型信息
    model_version = Column(String(50), nullable=True, comment="模型版本")
    model_parameters = Column(JSON, nullable=True, comment="模型参数")
    feature_importance = Column(JSON, nullable=True, comment="特征重要性")

    # 影响评估
    financial_impact = Column(Numeric(15, 2), default=0, comment="财务影响")
    performance_impact = Column(Numeric(5, 2), default=0, comment="性能影响")
    risk_impact = Column(Numeric(5, 2), default=0, comment="风险影响")

    # 处理信息
    auto_resolution = Column(Boolean, default=False, comment="是否自动解决")
    resolution_action = Column(Text, nullable=True, comment="解决方案")
    resolution_time = Column(DateTime, nullable=True, comment="解决时间")

    # 通知和分配
    notification_sent = Column(Boolean, default=False, comment="是否已发送通知")
    assigned_to = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="分配给")
    assigned_at = Column(DateTime, nullable=True, comment="分配时间")

    # 原始数据和上下文
    context_data = Column(JSON, nullable=True, comment="上下文数据")
    raw_data = Column(JSON, nullable=True, comment="原始数据")

    # 备注和日志
    investigation_notes = Column(Text, nullable=True, comment="调查笔记")
    resolution_notes = Column(Text, nullable=True, comment="解决笔记")

    # 审计信息
    created_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, comment="创建人")
    resolved_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="解决人")

    # 系统字段
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    deleted_at = Column(DateTime, nullable=True, comment="软删除时间")

    # 索引
    __table_args__ = (
        Index('idx_ai_anomaly_number', 'anomaly_number'),
        Index('idx_ai_anomaly_type_status', 'anomaly_type', 'status'),
        Index('idx_ai_anomaly_severity', 'severity'),
        Index('idx_ai_anomaly_project', 'project_id'),
        Index('idx_ai_anomaly_account', 'ad_account_id'),
        Index('idx_ai_anomaly_date', 'anomaly_date'),
        Index('idx_ai_anomaly_created', 'created_at'),
        Index('idx_ai_anomaly_assigned', 'assigned_to'),
        Index('idx_ai_anomaly_deleted_at', 'deleted_at'),
        {'comment': 'AI异常检测表 - 记录系统检测到的各种异常'}
    )

    # 关系
    project = relationship("Project", foreign_keys=[project_id])
    ad_account = relationship("AdAccount", foreign_keys=[ad_account_id])
    channel = relationship("Channel", foreign_keys=[channel_id])
    user = relationship("User", foreign_keys=[user_id])
    assignee = relationship("User", foreign_keys=[assigned_to])
    creator = relationship("User", foreign_keys=[created_by])
    resolver = relationship("User", foreign_keys=[resolved_by])


class AccountLifecyclePrediction(Base):
    """账户生命周期预测表 - AI预测账户剩余寿命和风险"""
    __tablename__ = "account_lifecycle_predictions"

    # 主键
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 关联账户
    ad_account_id = Column(PG_UUID(as_uuid=True), ForeignKey("ad_accounts.id"), nullable=False, comment="广告账户ID")
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, comment="项目ID")

    # 预测基本信息
    prediction_date = Column(Date, nullable=False, comment="预测日期")
    model_version = Column(String(50), nullable=True, comment="预测模型版本")

    # 预测结果
    predicted_lifetime_days = Column(Integer, nullable=False, comment="预测剩余天数")
    predicted_death_date = Column(Date, nullable=True, comment="预测死亡日期")
    confidence_score = Column(Numeric(5, 4), default=0, comment="置信度分数")

    # 风险评估
    risk_level = Column(SQLEnum(RiskLevel), nullable=False, comment="风险等级")
    risk_score = Column(Numeric(5, 2), default=0, comment="风险分数")
    probability_of_survival = Column(Numeric(5, 4), default=0, comment="生存概率")

    # 关键影响因素
    key_factors = Column(JSON, nullable=True, comment="关键影响因素")
    feature_contributions = Column(JSON, nullable=True, comment="特征贡献度")

    # 性能指标
    current_spend_trend = Column(String(20), nullable=True, comment="当前消耗趋势")
    current_performance_score = Column(Numeric(5, 2), default=0, comment="当前性能分数")
    stability_score = Column(Numeric(5, 2), default=0, comment="稳定性分数")

    # 预测建议
    recommended_actions = Column(JSON, nullable=True, comment="推荐行动")
    optimization_suggestions = Column(Text, nullable=True, comment="优化建议")

    # 历史验证
    previous_prediction_id = Column(PG_UUID(as_uuid=True), nullable=True, comment="上次预测ID")
    prediction_accuracy = Column(Numeric(5, 4), default=0, comment="预测准确度")

    # 模型参数
    model_parameters = Column(JSON, nullable=True, comment="模型参数")
    training_data_period = Column(String(50), nullable=True, comment="训练数据周期")

    # 状态和处理
    is_active = Column(Boolean, default=True, comment="是否活跃预测")
    reviewed_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="审核人")
    reviewed_at = Column(DateTime, nullable=True, comment="审核时间")
    review_notes = Column(Text, nullable=True, comment="审核备注")

    # 系统字段
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    deleted_at = Column(DateTime, nullable=True, comment="软删除时间")

    # 索引
    __table_args__ = (
        Index('idx_lifecycle_account', 'ad_account_id'),
        Index('idx_lifecycle_project', 'project_id'),
        Index('idx_lifecycle_date', 'prediction_date'),
        Index('idx_lifecycle_risk', 'risk_level'),
        Index('idx_lifetime_prediction', 'predicted_lifetime_days'),
        Index('idx_lifecycle_created', 'created_at'),
        Index('idx_lifecycle_active', 'is_active'),
        Index('idx_lifecycle_deleted_at', 'deleted_at'),
        {'comment': '账户生命周期预测表 - AI预测账户剩余寿命和风险'}
    )

    # 关系
    ad_account = relationship("AdAccount", foreign_keys=[ad_account_id])
    project = relationship("Project", foreign_keys=[project_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class MonitoringRule(Base):
    """监控规则表 - 定义系统的监控和风控规则"""
    __tablename__ = "monitoring_rules"

    # 主键
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 规则基本信息
    rule_name = Column(String(100), unique=True, nullable=False, comment="规则名称")
    rule_code = Column(String(50), unique=True, nullable=False, comment="规则代码")
    title = Column(String(255), nullable=False, comment="规则标题")
    description = Column(Text, nullable=True, comment="规则描述")

    # 规则分类
    rule_category = Column(String(50), nullable=False, comment="规则分类: anomaly, performance, security, compliance")
    rule_type = Column(String(50), nullable=False, comment="规则类型: threshold, pattern, ml_model")

    # 规则状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    priority = Column(Integer, default=5, comment="优先级(1-10)")

    # 触发条件
    trigger_condition = Column(JSON, nullable=False, comment="触发条件配置")
    threshold_value = Column(Numeric(15, 2), nullable=True, comment="阈值")
    comparison_operator = Column(String(10), nullable=True, comment="比较运算符: >, <, =, !=, >=, <=")

    # 监控范围
    target_entity = Column(String(50), nullable=False, comment="监控目标: account, project, user, system")
    scope_filter = Column(JSON, nullable=True, comment="范围过滤条件")

    # 执行配置
    check_frequency = Column(String(20), default="daily", comment="检查频率: hourly, daily, weekly")
    check_time = Column(String(10), nullable=True, comment="检查时间")
    timezone = Column(String(50), default="UTC", comment="时区")

    # 响应动作
    alert_actions = Column(JSON, nullable=True, comment="告警动作配置")
    auto_actions = Column(JSON, nullable=True, comment="自动动作配置")
    notification_config = Column(JSON, nullable=True, comment="通知配置")

    # 规则参数
    rule_parameters = Column(JSON, nullable=True, comment="规则参数")
    ml_model_config = Column(JSON, nullable=True, comment="ML模型配置")

    # 统计信息
    total_triggers = Column(Integer, default=0, comment="总触发次数")
    total_alerts = Column(Integer, default=0, comment="总告警次数")
    false_positives = Column(Integer, default=0, comment="误报次数")
    accuracy_rate = Column(Numeric(5, 4), default=0, comment="准确率")

    # 最后执行信息
    last_check_at = Column(DateTime, nullable=True, comment="最后检查时间")
    last_trigger_at = Column(DateTime, nullable=True, comment="最后触发时间")
    last_trigger_details = Column(JSON, nullable=True, comment="最后触发详情")

    # 维护信息
    version = Column(Integer, default=1, comment="规则版本")
    created_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, comment="创建人")
    updated_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="更新人")

    # 系统字段
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    deleted_at = Column(DateTime, nullable=True, comment="软删除时间")

    # 索引
    __table_args__ = (
        Index('idx_monitoring_rule_code', 'rule_code'),
        Index('idx_monitoring_rule_category', 'rule_category'),
        Index('idx_monitoring_rule_type', 'rule_type'),
        Index('idx_monitoring_rule_active', 'is_active'),
        Index('idx_monitoring_rule_priority', 'priority'),
        Index('idx_monitoring_rule_target', 'target_entity'),
        Index('idx_monitoring_rule_frequency', 'check_frequency'),
        Index('idx_monitoring_rule_created', 'created_at'),
        Index('idx_monitoring_rule_deleted_at', 'deleted_at'),
        {'comment': '监控规则表 - 定义系统的监控和风控规则'}
    )

    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])