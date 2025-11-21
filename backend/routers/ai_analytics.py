"""
AI分析和异常检测API路由
Version: 1.0
Author: Claude协作开发
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from pathlib import Path

from fastapi import APIRouter, Depends, Query, HTTPException, status

from backend.core.db import get_db
from backend.core.dependencies import get_current_user, require_role
from backend.core.response import success_response, error_response, StandardResponse
from backend.core.error_codes import ValidationErrorCodes, SystemErrorCodes
from backend.exceptions.custom_exceptions import (
    ResourceNotFoundError,
    PermissionDeniedError
)
from backend.models import User
from backend.services.ai_anomaly_detection_service import AIAnomalyDetectionService

router = APIRouter(prefix="/ai/analytics", tags=["ai-analytics"])


class AnomalyDetectionRequest(BaseModel):
    """异常检测请求"""
    account_ids: Optional[List[int]] = None
    project_ids: Optional[List[int]] = None
    days: int = 30
    threshold: float = 2.0


class BatchAnomalyDetectionRequest(BaseModel):
    """批量异常检测请求"""
    account_ids: Optional[List[int]] = None
    project_ids: Optional[List[int]] = None
    days: int = 30
    threshold: float = 2.0


def get_ai_service(db: Session = Depends(get_db)) -> AIAnomalyDetectionService:
    """获取AI服务实例"""
    return AIAnomalyDetectionService(db)


@router.post(
    "/detect-anomalies/{account_id}",
    response_model=StandardResponse[dict],
    summary="检测单账户异常"
)
@require_role(["admin", "finance", "data_operator", "account_manager", "media_buyer"])
async def detect_account_anomalies(
    account_id: int,
    days: int = Query(30, ge=7, le=90, description="分析天数"),
    threshold: float = Query(2.0, ge=1.0, le=5.0, description="异常阈值"),
    service: AIAnomalyDetectionService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user)
):
    """检测单个广告账户的异常"""
    try:
        anomalies = await service.detect_account_performance_anomalies(
            account_id=account_id,
            days=days,
            threshold=threshold
        )

        # 获取账户寿命风险评估
        lifetime_risk = await service.detect_account_lifetime_risk(
            account_id=account_id,
            days=days
        )

        return success_response(
            data={
                "account_id": account_id,
                "performance_anomalies": anomalies,
                "lifetime_risk": lifetime_risk,
                "analysis_config": {
                    "days": days,
                    "threshold": threshold
                }
            },
            message="异常检测完成"
        )

    except ValueError as e:
        return error_response(
            code=ValidationErrorCodes.VALIDATION_ERROR.code,
            message=str(e),
            status_code=ValidationErrorCodes.VALIDATION_ERROR.status_code
        )
    except Exception as e:
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="异常检测失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code
        )


@router.post(
    "/batch-detect-anomalies",
    response_model=StandardResponse[List[dict]],
    summary="批量检测异常"
)
@require_role(["admin", "finance", "data_operator", "account_manager"])
async def batch_detect_anomalies(
    request: BatchAnomalyDetectionRequest,
    service: AIAnomalyDetectionService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user)
):
    """批量检测多个账户的异常"""
    try:
        results = await service.batch_detect_anomalies(
            account_ids=request.account_ids,
            project_ids=request.project_ids,
            days=request.days,
            threshold=request.threshold
        )

        return success_response(
            data=results,
            message="批量异常检测完成"
        )

    except Exception as e:
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="批量异常检测失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code
        )


@router.get(
    "/anomaly-summary",
    response_model=StandardResponse[dict],
    summary="获取异常检测摘要"
)
@require_role(["admin", "finance", "data_operator", "account_manager"])
async def get_anomaly_summary(
    days: int = Query(30, ge=7, le=90, description="统计天数"),
    service: AIAnomalyDetectionService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user)
):
    """获取异常检测的摘要统计"""
    try:
        summary = await service.get_anomaly_summary(days=days)

        return success_response(
            data=summary,
            message="获取异常摘要成功"
        )

    except Exception as e:
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="获取异常摘要失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code
        )


@router.get(
    "/account-risk/{account_id}",
    response_model=StandardResponse[dict],
    summary="评估账户风险"
)
@require_role(["admin", "finance", "data_operator", "account_manager", "media_buyer"])
async def assess_account_risk(
    account_id: int,
    days: int = Query(30, ge=7, le=90, description="分析天数"),
    service: AIAnomalyDetectionService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user)
):
    """评估账户的寿命风险"""
    try:
        risk_assessment = await service.detect_account_lifetime_risk(
            account_id=account_id,
            days=days
        )

        return success_response(
            data=risk_assessment,
            message="风险评估完成"
        )

    except ValueError as e:
        return error_response(
            code=ValidationErrorCodes.VALIDATION_ERROR.code,
            message=str(e),
            status_code=ValidationErrorCodes.VALIDATION_ERROR.status_code
        )
    except Exception as e:
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="风险评估失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code
        )


@router.get(
    "/project-risk/{project_id}",
    response_model=StandardResponse[dict],
    summary="评估项目整体风险"
)
@require_role(["admin", "finance", "data_operator", "account_manager"])
async def assess_project_risk(
    project_id: int,
    days: int = Query(30, ge=7, le=90, description="分析天数"),
    service: AIAnomalyDetectionService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user)
):
    """评估项目所有账户的整体风险"""
    try:
        # 获取项目下的所有账户风险
        results = await service.batch_detect_anomalies(
            project_ids=[project_id],
            days=days
        )

        # 统计项目级风险
        total_accounts = len(results)
        high_risk_accounts = len([
            r for r in results
            if r.get("lifetime_risk", {}).get("risk_level") == "high"
        ])
        medium_risk_accounts = len([
            r for r in results
            if r.get("lifetime_risk", {}).get("risk_level") == "medium"
        ])
        total_anomalies = sum(r.get("anomaly_count", 0) for r in results)

        # 计算项目风险等级
        if high_risk_accounts > 0:
            project_risk_level = "high"
        elif medium_risk_accounts > total_accounts * 0.3:
            project_risk_level = "medium"
        else:
            project_risk_level = "low"

        project_risk_score = (
            (high_risk_accounts * 3 + medium_risk_accounts * 2) / total_accounts * 100
        ) if total_accounts > 0 else 0

        return success_response(
            data={
                "project_id": project_id,
                "risk_level": project_risk_level,
                "risk_score": min(project_risk_score, 100),
                "account_summary": {
                    "total_accounts": total_accounts,
                    "high_risk_accounts": high_risk_accounts,
                    "medium_risk_accounts": medium_risk_accounts,
                    "low_risk_accounts": total_accounts - high_risk_accounts - medium_risk_accounts
                },
                "anomaly_summary": {
                    "total_anomalies": total_anomalies,
                    "avg_anomalies_per_account": total_anomalies / total_accounts if total_accounts > 0 else 0
                },
                "account_details": results,
                "analysis_period": f"{days} days"
            },
            message="项目风险评估完成"
        )

    except Exception as e:
        return error_response(
            code="SYS_500",
            message="项目风险评估失败",
            status_code=500
        )


@router.get(
    "/recommendations/{account_id}",
    response_model=StandardResponse[dict],
    summary="获取AI优化建议"
)
@require_role(["admin", "finance", "data_operator", "account_manager", "media_buyer"])
async def get_ai_recommendations(
    account_id: int,
    days: int = Query(30, ge=7, le=90, description="分析天数"),
    service: AIAnomalyDetectionService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user)
):
    """基于AI分析获取优化建议"""
    try:
        # 获取异常检测结果
        anomalies = await service.detect_account_performance_anomalies(
            account_id=account_id,
            days=days,
            threshold=1.5  # 使用较低的阈值以获取更多建议
        )

        # 获取风险评估
        risk_assessment = await service.detect_account_lifetime_risk(
            account_id=account_id,
            days=days
        )

        # 生成优化建议
        recommendations = []

        # 基于异常类型生成建议
        anomaly_types = set(a["type"] for a in anomalies)

        if "spend_drop" in anomaly_types:
            recommendations.append({
                "category": "预算优化",
                "priority": "high",
                "title": "消耗骤降优化建议",
                "description": "检测到消耗显著下降，建议检查广告投放状态和出价策略",
                "actions": [
                    "检查广告系列是否处于活跃状态",
                    "验证出价是否过低导致展示受限",
                    "考虑增加预算或调整出价策略",
                    "检查目标受众是否过于狭窄"
                ]
            })

        if "spend_spike" in anomaly_types:
            recommendations.append({
                "category": "成本控制",
                "priority": "high",
                "title": "消耗激增控制建议",
                "description": "检测到消耗异常增加，需要控制成本避免超支",
                "actions": [
                    "设置日预算上限",
                    "检查CPA是否在可接受范围内",
                    "暂停低效广告组",
                    "优化出价避免过度竞价"
                ]
            })

        if "ctr_drop" in anomaly_types:
            recommendations.append({
                "category": "创意优化",
                "priority": "medium",
                "title": "点击率下降优化建议",
                "description": "点击率下降可能表示广告创意需要更新",
                "actions": [
                    "A/B测试新的广告创意",
                    "优化广告标题和描述",
                    "更新图片或视频素材",
                    "检查目标受众相关性"
                ]
            })

        if "cvr_drop" in anomaly_types:
            recommendations.append({
                "category": "转化优化",
                "priority": "high",
                "title": "转化率下降优化建议",
                "description": "转化率下降直接影响ROI，需要立即优化",
                "actions": [
                    "优化落地页体验",
                    "检查转化追踪是否正常",
                    "调整目标受众定位",
                    "改进行动号召(CTA)"
                ]
            })

        if "cpa_spike" in anomaly_types:
            recommendations.append({
                "category": "成本优化",
                "priority": "high",
                "title": "CPA过高优化建议",
                "description": "获客成本过高，需要优化投放策略",
                "actions": [
                    "暂停高CPA的广告组",
                    "优化定位以提高转化质量",
                    "改进广告素材相关性",
                    "调整出价策略"
                ]
            })

        # 基于风险等级生成建议
        if risk_assessment["risk_level"] in ["high", "medium"]:
            recommendations.append({
                "category": "风险管理",
                "priority": "high",
                "title": "账户风险管理建议",
                "description": f"当前风险等级为{risk_assessment['risk_level']}，需要采取措施",
                "actions": risk_assessment.get("recommendations", [])
            })

        # 如果没有异常，提供预防性建议
        if not recommendations:
            recommendations.append({
                "category": "持续优化",
                "priority": "low",
                "title": "预防性优化建议",
                "description": "当前表现良好，建议进行持续优化",
                "actions": [
                    "定期测试新广告创意",
                    "监控竞品动态",
                    "探索新的受众群体",
                    "保持ROI稳定增长"
                ]
            })

        return success_response(
            data={
                "account_id": account_id,
                "analysis_summary": {
                    "anomaly_count": len(anomalies),
                    "risk_level": risk_assessment["risk_level"],
                    "risk_score": risk_assessment["risk_score"]
                },
                "recommendations": recommendations,
                "generated_at": risk_assessment["analysis_date"]
            },
            message="AI优化建议生成成功"
        )

    except Exception as e:
        return error_response(
            code="SYS_500",
            message="生成AI建议失败",
            status_code=500
        )