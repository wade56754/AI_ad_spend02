"""
AI监控服务
提供异常检测、账户寿命预测、监控规则管理等功能
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID, uuid4
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, case

from backend.core.db import get_db_session
from backend.core.error_codes import ErrorCode
from backend.core.response import ApiResponse, PaginatedResponse
from backend.models.ai_monitoring import (
    AIAnomalyDetection, AccountLifecyclePrediction, MonitoringRule,
    AnomalyType, AnomalySeverity, PredictionStatus, RuleStatus
)
from backend.services.audit_service import AuditService, BusinessAction


class AIMonitoringService:
    """AI监控服务类"""

    @staticmethod
    def create_anomaly_detection(
        account_id: UUID,
        anomaly_type: AnomalyType,
        severity: AnomalySeverity,
        description: str,
        metrics_data: Dict[str, Any] = None,
        prediction_data: Dict[str, Any] = None,
        confidence_score: float = None,
        user_id: str = None
    ) -> AIAnomalyDetection:
        """创建异常检测记录"""
        with get_db_session() as session:
            anomaly = AIAnomalyDetection(
                id=uuid4(),
                account_id=account_id,
                anomaly_type=anomaly_type,
                severity=severity,
                description=description,
                metrics_data=metrics_data or {},
                prediction_data=prediction_data or {},
                confidence_score=confidence_score,
                status="active",
                created_by=user_id
            )

            session.add(anomaly)
            session.commit()

            # 记录审计日志
            AuditService.log_ai_action(
                action=BusinessAction.AI_ANOMALY_DETECTED,
                resource_id=str(anomaly.id),
                user_id=user_id,
                ai_data={
                    "account_id": str(account_id),
                    "anomaly_type": anomaly_type.value,
                    "severity": severity.value,
                    "description": description
                },
                anomaly_type=anomaly_type.value
            )

            return anomaly

    @staticmethod
    def create_account_lifecycle_prediction(
        account_id: UUID,
        predicted_remaining_days: int,
        prediction_model: str = "default",
        confidence_score: float = None,
        feature_importance: Dict[str, float] = None,
        recommendation: str = None,
        user_id: str = None
    ) -> AccountLifecyclePrediction:
        """创建账户寿命预测"""
        with get_db_session() as session:
            prediction = AccountLifecyclePrediction(
                id=uuid4(),
                account_id=account_id,
                predicted_remaining_days=predicted_remaining_days,
                prediction_model=prediction_model,
                confidence_score=confidence_score,
                feature_importance=feature_importance or {},
                recommendation=recommendation,
                status=PredictionStatus.ACTIVE,
                created_by=user_id
            )

            session.add(prediction)
            session.commit()

            # 记录审计日志
            AuditService.log_ai_action(
                action=BusinessAction.AI_PREDICTION_GENERATED,
                resource_id=str(prediction.id),
                user_id=user_id,
                ai_data={
                    "account_id": str(account_id),
                    "predicted_remaining_days": predicted_remaining_days,
                    "prediction_model": prediction_model,
                    "confidence_score": confidence_score
                },
                prediction_result={"predicted_remaining_days": predicted_remaining_days}
            )

            return prediction

    @staticmethod
    def create_monitoring_rule(
        name: str,
        rule_type: str,
        conditions: Dict[str, Any],
        actions: Dict[str, Any],
        severity: AnomalySeverity = AnomalySeverity.MEDIUM,
        is_active: bool = True,
        description: str = None,
        user_id: str = None
    ) -> MonitoringRule:
        """创建监控规则"""
        with get_db_session() as session:
            rule = MonitoringRule(
                id=uuid4(),
                name=name,
                rule_type=rule_type,
                conditions=conditions,
                actions=actions,
                severity=severity,
                is_active=is_active,
                status=RuleStatus.ACTIVE,
                description=description,
                created_by=user_id
            )

            session.add(rule)
            session.commit()

            # 记录审计日志
            AuditService.log_ai_action(
                action=BusinessAction.AI_RULE_TRIGGERED,
                resource_id=str(rule.id),
                user_id=user_id,
                ai_data={
                    "name": name,
                    "rule_type": rule_type,
                    "conditions": conditions,
                    "actions": actions,
                    "severity": severity.value
                },
                rule_name=name
            )

            return rule

    @staticmethod
    def get_anomaly_detections(
        account_id: UUID = None,
        anomaly_type: AnomalyType = None,
        severity: AnomalySeverity = None,
        status: str = None,
        start_date: date = None,
        end_date: date = None,
        page: int = 1,
        size: int = 20
    ) -> PaginatedResponse:
        """获取异常检测列表"""
        with get_db_session() as session:
            query = session.query(AIAnomalyDetection)

            if account_id:
                query = query.filter(AIAnomalyDetection.account_id == account_id)
            if anomaly_type:
                query = query.filter(AIAnomalyDetection.anomaly_type == anomaly_type)
            if severity:
                query = query.filter(AIAnomalyDetection.severity == severity)
            if status:
                query = query.filter(AIAnomalyDetection.status == status)
            if start_date:
                query = query.filter(AIAnomalyDetection.anomaly_date >= start_date)
            if end_date:
                query = query.filter(AIAnomalyDetection.anomaly_date <= end_date)

            # 获取总数
            total = query.count()

            # 应用分页
            offset = (page - 1) * size
            anomalies = query.order_by(desc(AIAnomalyDetection.created_at)).offset(offset).limit(size).all()

            return PaginatedResponse(
                items=[AIMonitoringService._anomaly_to_dict(a) for a in anomalies],
                total=total,
                page=page,
                size=size,
                pages=(total + size - 1) // size
            )

    @staticmethod
    def get_account_lifecycle_predictions(
        account_id: UUID = None,
        status: PredictionStatus = None,
        prediction_model: str = None,
        page: int = 1,
        size: int = 20
    ) -> PaginatedResponse:
        """获取账户寿命预测列表"""
        with get_db_session() as session:
            query = session.query(AccountLifecyclePrediction)

            if account_id:
                query = query.filter(AccountLifecyclePrediction.account_id == account_id)
            if status:
                query = query.filter(AccountLifecyclePrediction.status == status)
            if prediction_model:
                query = query.filter(AccountLifecyclePrediction.prediction_model == prediction_model)

            # 获取总数
            total = query.count()

            # 应用分页
            offset = (page - 1) * size
            predictions = query.order_by(desc(AccountLifecyclePrediction.created_at)).offset(offset).limit(size).all()

            return PaginatedResponse(
                items=[AIMonitoringService._prediction_to_dict(p) for p in predictions],
                total=total,
                page=page,
                size=size,
                pages=(total + size - 1) // size
            )

    @staticmethod
    def get_monitoring_rules(
        rule_type: str = None,
        is_active: bool = None,
        page: int = 1,
        size: int = 20
    ) -> PaginatedResponse:
        """获取监控规则列表"""
        with get_db_session() as session:
            query = session.query(MonitoringRule)

            if rule_type:
                query = query.filter(MonitoringRule.rule_type == rule_type)
            if is_active is not None:
                query = query.filter(MonitoringRule.is_active == is_active)

            # 获取总数
            total = query.count()

            # 应用分页
            offset = (page - 1) * size
            rules = query.order_by(desc(MonitoringRule.created_at)).offset(offset).limit(size).all()

            return PaginatedResponse(
                items=[AIMonitoringService._rule_to_dict(r) for r in rules],
                total=total,
                page=page,
                size=size,
                pages=(total + size - 1) // size
            )

    @staticmethod
    def update_anomaly_status(
        anomaly_id: UUID,
        status: str,
        resolution_note: str = None,
        user_id: str = None
    ) -> Optional[AIAnomalyDetection]:
        """更新异常状态"""
        with get_db_session() as session:
            anomaly = session.query(AIAnomalyDetection).filter(
                AIAnomalyDetection.id == anomaly_id
            ).first()

            if not anomaly:
                return None

            old_status = anomaly.status
            anomaly.status = status
            anomaly.updated_at = datetime.utcnow()

            if resolution_note:
                if not anomaly.prediction_data:
                    anomaly.prediction_data = {}
                anomaly.prediction_data["resolution_note"] = resolution_note

            session.commit()

            return anomaly

    @staticmethod
    def get_ai_dashboard_summary(
        start_date: date = None,
        end_date: date = None
    ) -> Dict[str, Any]:
        """获取AI监控仪表板汇总"""
        with get_db_session() as session:
            # 异常检测统计
            anomaly_stats = session.query(
                AIAnomalyDetection.severity,
                func.count(AIAnomalyDetection.id).label('count')
            ).filter(
                and_(
                    *([AIAnomalyDetection.anomaly_date >= start_date] if start_date else []),
                    *([AIAnomalyDetection.anomaly_date <= end_date] if end_date else [])
                )
            ).group_by(AIAnomalyDetection.severity).all()

            # 账户预测统计
            prediction_stats = session.query(
                func.count(AccountLifecyclePrediction.id).label('total_predictions'),
                func.avg(AccountLifecyclePrediction.predicted_remaining_days).label('avg_remaining_days'),
                func.avg(AccountLifecyclePrediction.confidence_score).label('avg_confidence')
            ).filter(
                AccountLifecyclePrediction.status == PredictionStatus.ACTIVE
            ).first()

            # 监控规则统计
            rule_stats = session.query(
                MonitoringRule.is_active,
                func.count(MonitoringRule.id).label('count')
            ).group_by(MonitoringRule.is_active).all()

            return {
                "anomaly_summary": [
                    {
                        "severity": stat.severity.value,
                        "count": stat.count
                    }
                    for stat in anomaly_stats
                ],
                "prediction_summary": {
                    "total_predictions": prediction_stats.total_predictions if prediction_stats else 0,
                    "average_remaining_days": float(prediction_stats.avg_remaining_days) if prediction_stats and prediction_stats.avg_remaining_days else 0,
                    "average_confidence": float(prediction_stats.avg_confidence) if prediction_stats and prediction_stats.avg_confidence else 0
                },
                "rule_summary": [
                    {
                        "is_active": stat.is_active,
                        "count": stat.count
                    }
                    for stat in rule_stats
                ],
                "period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                }
            }

    @staticmethod
    def simulate_anomaly_detection(
        account_id: UUID,
        metrics: Dict[str, Any],
        rules: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """模拟异常检测（用于演示）"""
        detected_anomalies = []

        # 模拟几种常见的异常检测规则
        if metrics.get('spend_sudden_increase', 0) > 200:  # 突然增加200%以上
            detected_anomalies.append({
                "type": AnomalyType.SPEND_SPIKE.value,
                "severity": AnomalySeverity.HIGH.value,
                "confidence": 0.85,
                "description": f"广告消耗突然增加 {metrics.get('spend_sudden_increase', 0)}%"
            })

        if metrics.get('conversion_rate_drop', 0) > 50:  # 转化率下降50%以上
            detected_anomalies.append({
                "type": AnomalyType.PERFORMANCE_DECLINE.value,
                "severity": AnomalySeverity.CRITICAL.value,
                "confidence": 0.92,
                "description": f"转化率下降 {metrics.get('conversion_rate_drop', 0)}%"
            })

        if metrics.get('account_risk_score', 0) > 80:  # 账户风险评分过高
            detected_anomalies.append({
                "type": AnomalyType.ACCOUNT_RISK.value,
                "severity": AnomalySeverity.HIGH.value,
                "confidence": 0.78,
                "description": f"账户风险评分 {metrics.get('account_risk_score', 0)}，存在封号风险"
            })

        if metrics.get('budget_overspend', 0) > 0:  # 预算超支
            detected_anomalies.append({
                "type": AnomalyType.BUDGET_ANOMALY.value,
                "severity": AnomalySeverity.MEDIUM.value,
                "confidence": 0.95,
                "description": f"预算超支 ${metrics.get('budget_overspend', 0)}"
            })

        return detected_anomalies

    @staticmethod
    def _anomaly_to_dict(anomaly: AIAnomalyDetection) -> Dict[str, Any]:
        """转换异常检测为字典"""
        return {
            "id": str(anomaly.id),
            "account_id": str(anomaly.account_id),
            "anomaly_type": anomaly.anomaly_type.value,
            "severity": anomaly.severity.value,
            "description": anomaly.description,
            "metrics_data": anomaly.metrics_data,
            "prediction_data": anomaly.prediction_data,
            "confidence_score": anomaly.confidence_score,
            "status": anomaly.status,
            "anomaly_date": anomaly.anomaly_date.isoformat(),
            "created_at": anomaly.created_at.isoformat(),
            "updated_at": anomaly.updated_at.isoformat() if anomaly.updated_at else None
        }

    @staticmethod
    def _prediction_to_dict(prediction: AccountLifecyclePrediction) -> Dict[str, Any]:
        """转换账户寿命预测为字典"""
        return {
            "id": str(prediction.id),
            "account_id": str(prediction.account_id),
            "predicted_remaining_days": prediction.predicted_remaining_days,
            "prediction_model": prediction.prediction_model,
            "confidence_score": prediction.confidence_score,
            "feature_importance": prediction.feature_importance,
            "recommendation": prediction.recommendation,
            "status": prediction.status.value,
            "created_at": prediction.created_at.isoformat(),
            "updated_at": prediction.updated_at.isoformat() if prediction.updated_at else None
        }

    @staticmethod
    def _rule_to_dict(rule: MonitoringRule) -> Dict[str, Any]:
        """转换监控规则为字典"""
        return {
            "id": str(rule.id),
            "name": rule.name,
            "rule_type": rule.rule_type,
            "conditions": rule.conditions,
            "actions": rule.actions,
            "severity": rule.severity.value,
            "is_active": rule.is_active,
            "status": rule.status.value,
            "description": rule.description,
            "created_by": rule.created_by,
            "created_at": rule.created_at.isoformat(),
            "updated_at": rule.updated_at.isoformat() if rule.updated_at else None
        }


def get_ai_monitoring_service() -> AIMonitoringService:
    """获取AI监控服务实例"""
    return AIMonitoringService()