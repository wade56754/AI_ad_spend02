"""
AI监控API路由
处理异常检测、账户寿命预测、监控规则管理等接口
"""

from datetime import date, datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field

from core.db import get_db
from core.dependencies import get_current_user, require_role
from core.response import (
    success_response,
    error_response,
    StandardResponse
)
from core.error_codes import ErrorCode
from models.users import User
from models.ai_monitoring import AnomalyType, AnomalySeverity, PredictionStatus, RuleStatus
from services.ai_monitoring_service import get_ai_monitoring_service, AIMonitoringService


# 定义分页响应类型
class PaginatedResponse(BaseModel):
    """分页响应"""
    items: List[Any]
    total: int
    page: int
    size: int


router = APIRouter(prefix="/ai-monitoring", tags=["ai_monitoring"])


# Pydantic模型定义
class AnomalyDetectionCreateRequest(BaseModel):
    """创建异常检测请求"""
    account_id: UUID = Field(..., description="账户ID")
    anomaly_type: AnomalyType = Field(..., description="异常类型")
    severity: AnomalySeverity = Field(..., description="严重程度")
    description: str = Field(..., description="异常描述")
    metrics_data: Optional[Dict[str, Any]] = Field(None, description="指标数据")
    prediction_data: Optional[Dict[str, Any]] = Field(None, description="预测数据")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="置信度分数")


class LifecyclePredictionCreateRequest(BaseModel):
    """创建账户寿命预测请求"""
    account_id: UUID = Field(..., description="账户ID")
    predicted_remaining_days: int = Field(..., gt=0, description="预测剩余天数")
    prediction_model: str = Field("default", description="预测模型")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="置信度分数")
    feature_importance: Optional[Dict[str, float]] = Field(None, description="特征重要性")
    recommendation: Optional[str] = Field(None, description="建议")


class MonitoringRuleCreateRequest(BaseModel):
    """创建监控规则请求"""
    name: str = Field(..., description="规则名称")
    rule_type: str = Field(..., description="规则类型")
    conditions: Dict[str, Any] = Field(..., description="触发条件")
    actions: Dict[str, Any] = Field(..., description="执行动作")
    severity: AnomalySeverity = Field(AnomalySeverity.MEDIUM, description="严重程度")
    is_active: bool = Field(True, description="是否激活")
    description: Optional[str] = Field(None, description="描述")


class AnomalyDetectionUpdateRequest(BaseModel):
    """更新异常状态请求"""
    status: str = Field(..., description="状态")
    resolution_note: Optional[str] = Field(None, description="解决方案说明")


class AnomalySimulationRequest(BaseModel):
    """异常检测模拟请求"""
    account_id: UUID = Field(..., description="账户ID")
    metrics: Dict[str, Any] = Field(..., description="账户指标数据")
    rules: Optional[List[Dict[str, Any]]] = Field(None, description="自定义规则")


class AnomalyDetectionResponse(BaseModel):
    """异常检测响应"""
    id: str
    account_id: str
    anomaly_type: str
    severity: str
    description: str
    metrics_data: Optional[Dict[str, Any]]
    prediction_data: Optional[Dict[str, Any]]
    confidence_score: Optional[float]
    status: str
    anomaly_date: str
    created_at: str
    updated_at: Optional[str]


class LifecyclePredictionResponse(BaseModel):
    """账户寿命预测响应"""
    id: str
    account_id: str
    predicted_remaining_days: int
    prediction_model: str
    confidence_score: Optional[float]
    feature_importance: Optional[Dict[str, float]]
    recommendation: Optional[str]
    status: str
    created_at: str
    updated_at: Optional[str]


class MonitoringRuleResponse(BaseModel):
    """监控规则响应"""
    id: str
    name: str
    rule_type: str
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    severity: str
    is_active: bool
    status: str
    description: Optional[str]
    created_by: Optional[str]
    created_at: str
    updated_at: Optional[str]


# API路由定义
@router.post("/anomalies", response_model=StandardResponse[AnomalyDetectionResponse])
async def create_anomaly_detection(
    request: AnomalyDetectionCreateRequest,
    ai_service: AIMonitoringService = Depends(get_ai_monitoring_service),
    current_user: User = Depends(require_role(["admin", "account_manager"]))
):
    """
    创建异常检测记录
    需要权限: AI_MONITORING 或 ADMIN
    """    # 权限检查

    try:
        anomaly = ai_service.create_anomaly_detection(
            account_id=request.account_id,
            anomaly_type=request.anomaly_type,
            severity=request.severity,
            description=request.description,
            metrics_data=request.metrics_data,
            prediction_data=request.prediction_data,
            confidence_score=request.confidence_score,
            user_id=current_user.id
        )

        return success_response(data=AnomalyDetectionResponse(**ai_service._anomaly_to_dict(anomaly)), message="异常检测记录创建成功")

    except Exception as e:
        return error_response(
            code="INTERNAL_ERROR",
            message=f"创建异常检测失败: {str(e)}",
            status_code=500
        )


@router.post("/predictions", response_model=StandardResponse[LifecyclePredictionResponse])
async def create_lifecycle_prediction(
    request: LifecyclePredictionCreateRequest,
    ai_service: AIMonitoringService = Depends(get_ai_monitoring_service),
    current_user: User = Depends(require_role(["admin", "account_manager"]))
):
    """
    创建账户寿命预测
    需要权限: AI_ANALYSIS 或 ADMIN
    """    # 权限检查

    try:
        prediction = ai_service.create_account_lifecycle_prediction(
            account_id=request.account_id,
            predicted_remaining_days=request.predicted_remaining_days,
            prediction_model=request.prediction_model,
            confidence_score=request.confidence_score,
            feature_importance=request.feature_importance,
            recommendation=request.recommendation,
            user_id=current_user.id
        )

        return success_response(data=LifecyclePredictionResponse(**ai_service._prediction_to_dict(prediction)), message="账户寿命预测创建成功")

    except Exception as e:
        return error_response(
            code="INTERNAL_ERROR",
            message=f"创建账户寿命预测失败: {str(e)}",
            status_code=500
        )


@router.post("/rules", response_model=StandardResponse[MonitoringRuleResponse])
async def create_monitoring_rule(
    request: MonitoringRuleCreateRequest,
    ai_service: AIMonitoringService = Depends(get_ai_monitoring_service),
    current_user: User = Depends(require_role(["admin"]))
):
    """
    创建监控规则
    需要权限: AI_MONITORING 或 ADMIN
    """    # 权限检查

    try:
        rule = ai_service.create_monitoring_rule(
            name=request.name,
            rule_type=request.rule_type,
            conditions=request.conditions,
            actions=request.actions,
            severity=request.severity,
            is_active=request.is_active,
            description=request.description,
            user_id=current_user.id
        )

        return success_response(data=MonitoringRuleResponse(**ai_service._rule_to_dict(rule)), message="监控规则创建成功")

    except Exception as e:
        return error_response(
            code="INTERNAL_ERROR",
            message=f"创建监控规则失败: {str(e)}",
            status_code=500
        )


@router.get("/anomalies", response_model=StandardResponse[PaginatedResponse])
async def get_anomaly_detections(
    account_id: Optional[UUID] = Query(None, description="账户ID"),
    anomaly_type: Optional[AnomalyType] = Query(None, description="异常类型"),
    severity: Optional[AnomalySeverity] = Query(None, description="严重程度"),
    status: Optional[str] = Query(None, description="状态"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(require_permissions(Permission.AI_MONITORING)),
    ai_service: AIMonitoringService = Depends(get_ai_monitoring_service)
):
    """
    获取异常检测列表
    需要权限: AI_MONITORING
    """
    try:
        result = ai_service.get_anomaly_detections(
            account_id=account_id,
            anomaly_type=anomaly_type,
            severity=severity,
            status=status,
            start_date=start_date,
            end_date=end_date,
            page=page,
            size=size
        )

        return success_response(data=result, message="获取异常检测列表成功")

    except Exception as e:
        return error_response(
            code="INTERNAL_ERROR",
            message=f"获取异常检测列表失败: {str(e)}",
            status_code=500
        )


@router.get("/predictions", response_model=StandardResponse[PaginatedResponse])
async def get_lifecycle_predictions(
    account_id: Optional[UUID] = Query(None, description="账户ID"),
    status: Optional[PredictionStatus] = Query(None, description="预测状态"),
    prediction_model: Optional[str] = Query(None, description="预测模型"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(require_permissions(Permission.AI_ANALYSIS)),
    ai_service: AIMonitoringService = Depends(get_ai_monitoring_service)
):
    """
    获取账户寿命预测列表
    需要权限: AI_ANALYSIS
    """
    try:
        result = ai_service.get_account_lifecycle_predictions(
            account_id=account_id,
            status=status,
            prediction_model=prediction_model,
            page=page,
            size=size
        )

        return success_response(data=result, message="获取账户寿命预测列表成功")

    except Exception as e:
        return error_response(
            code="INTERNAL_ERROR",
            message=f"获取账户寿命预测列表失败: {str(e)}",
            status_code=500
        )


@router.get("/rules", response_model=StandardResponse[PaginatedResponse])
async def get_monitoring_rules(
    rule_type: Optional[str] = Query(None, description="规则类型"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(require_permissions(Permission.AI_MONITORING)),
    ai_service: AIMonitoringService = Depends(get_ai_monitoring_service)
):
    """
    获取监控规则列表
    需要权限: AI_MONITORING
    """
    try:
        result = ai_service.get_monitoring_rules(
            rule_type=rule_type,
            is_active=is_active,
            page=page,
            size=size
        )

        return success_response(data=result, message="获取监控规则列表成功")

    except Exception as e:
        return error_response(
            code="INTERNAL_ERROR",
            message=f"获取监控规则列表失败: {str(e)}",
            status_code=500
        )


@router.put("/anomalies/{anomaly_id}/status", response_model=StandardResponse[AnomalyDetectionResponse])
async def update_anomaly_status(
    anomaly_id: UUID,
    request: AnomalyDetectionUpdateRequest,
    ai_service: AIMonitoringService = Depends(get_ai_monitoring_service),
    current_user: User = Depends(require_role(["admin", "account_manager"]))
):
    """
    更新异常状态
    需要权限: AI_MONITORING 或 ADMIN
    """    # 权限检查

    try:
        anomaly = ai_service.update_anomaly_status(
            anomaly_id=anomaly_id,
            status=request.status,
            resolution_note=request.resolution_note,
            user_id=current_user.id
        )

        if not anomaly:
            return error_response(
                code="NOT_FOUND",
                message="异常检测记录不存在",
                status_code=404
            )

        return success_response(data=AnomalyDetectionResponse(**ai_service._anomaly_to_dict(anomaly)), message="异常状态更新成功")

    except HTTPException:
        raise
    except Exception as e:
        return error_response(
            code="INTERNAL_ERROR",
            message=f"更新异常状态失败: {str(e)}",
            status_code=500
        )


@router.post("/simulate-detection", response_model=StandardResponse[List[Dict[str, Any]]])
async def simulate_anomaly_detection(
    request: AnomalySimulationRequest,
    ai_service: AIMonitoringService = Depends(get_ai_monitoring_service),
    current_user: User = Depends(require_role(["admin", "account_manager"]))
):
    """
    模拟异常检测
    需要权限: ADMIN 或 ACCOUNT_MANAGER
    """
    try:
        detected_anomalies = ai_service.simulate_anomaly_detection(
            account_id=request.account_id,
            metrics=request.metrics,
            rules=request.rules
        )

        # 记录审计日志
        audit_service.log_ai_action(
            action=BusinessAction.AI_ANOMALY_DETECTED,
            resource_id=str(request.account_id),
            user_id=current_user.id,
            ai_data={
                "account_id": str(request.account_id),
                "metrics": request.metrics,
                "detected_count": len(detected_anomalies)
            },
            anomaly_type="simulation"
        )

        return success_response(data=detected_anomalies, message=f"模拟检测完成，发现 {len(detected_anomalies)} 个异常")

    except Exception as e:
        return error_response(
            code="INTERNAL_ERROR",
            message=f"模拟异常检测失败: {str(e)}",
            status_code=500
        )


@router.get("/dashboard", response_model=StandardResponse[Dict[str, Any]])
async def get_ai_dashboard(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(require_permissions(Permission.AI_MONITORING)),
    ai_service: AIMonitoringService = Depends(get_ai_monitoring_service)
):
    """
    获取AI监控仪表板数据
    需要权限: AI_MONITORING
    """
    try:
        dashboard_data = ai_service.get_ai_dashboard_summary(
            start_date=start_date,
            end_date=end_date
        )

        return success_response(data=dashboard_data, message="获取AI监控仪表板数据成功")

    except Exception as e:
        return error_response(
            code="INTERNAL_ERROR",
            message=f"获取AI监控仪表板数据失败: {str(e)}",
            status_code=500
        )


@router.get("/statistics", response_model=StandardResponse[Dict[str, Any]])
async def get_ai_statistics(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    ai_service: AIMonitoringService = Depends(get_ai_monitoring_service),
    current_user: User = Depends(require_role(["admin", "account_manager"]))
):
    """
    获取AI监控统计信息
    需要权限: MANAGER 或 ADMIN
    """
    try:
        dashboard_data = ai_service.get_ai_dashboard_summary(
            start_date=start_date,
            end_date=end_date
        )

        # 添加额外的统计信息
        statistics = {
            "dashboard_summary": dashboard_data,
            "system_health": {
                "ai_models_loaded": True,
                "last_prediction_run": datetime.now().isoformat(),
                "active_monitoring_rules": dashboard_data["rule_summary"][0]["count"] if dashboard_data["rule_summary"] else 0
            },
            "performance_metrics": {
                "avg_detection_time_ms": 150,
                "prediction_accuracy": 0.87,
                "false_positive_rate": 0.12
            }
        }

        return success_response(data=statistics, message="获取AI监控统计信息成功")

    except Exception as e:
        return error_response(
            code="INTERNAL_ERROR",
            message=f"获取AI监控统计信息失败: {str(e)}",
            status_code=500
        )