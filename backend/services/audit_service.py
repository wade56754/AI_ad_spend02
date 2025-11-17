"""
审计服务
提供业务操作审计和安全日志功能
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

from fastapi import Request, Depends
from sqlalchemy.orm import Session

from core.audit import audit_logger, security_logger, AuditAction, AuditLevel
from core.security import AuthenticatedUser, get_current_active_user
from core.db import get_db_session


class BusinessAction(str, Enum):
    """业务操作类型"""
    # 项目管理
    PROJECT_CREATE = "project_create"
    PROJECT_UPDATE = "project_update"
    PROJECT_DELETE = "project_delete"
    PROJECT_MEMBER_ADD = "project_member_add"
    PROJECT_MEMBER_REMOVE = "project_member_remove"

    # 日报管理
    DAILY_REPORT_SUBMIT = "daily_report_submit"
    DAILY_REPORT_APPROVE = "daily_report_approve"
    DAILY_REPORT_REJECT = "daily_report_reject"

    # 充值管理
    TOPUP_SUBMIT = "topup_submit"
    TOPUP_APPROVE_DATA = "topup_approve_data"
    TOPUP_APPROVE_FINANCE = "topup_approve_finance"
    TOPUP_REJECT = "topup_reject"
    TOPUP_PAYMENT_CONFIRM = "topup_payment_confirm"

    # 财务对账
    RECONCILIATION_CREATE = "reconciliation_create"
    RECONCILIATION_PROCESS = "reconciliation_process"
    RECONCILIATION_RESOLVE = "reconciliation_resolve"

    # AI监控
    AI_ANOMALY_DETECTED = "ai_anomaly_detected"
    AI_PREDICTION_GENERATED = "ai_prediction_generated"
    AI_RULE_TRIGGERED = "ai_rule_triggered"


class AuditService:
    """审计服务类"""

    @staticmethod
    def log_business_action(
        action: BusinessAction,
        user_id: str,
        resource_type: str,
        resource_id: str,
        old_data: Dict[str, Any] = None,
        new_data: Dict[str, Any] = None,
        ip_address: str = None,
        user_agent: str = None,
        description: str = None,
        level: AuditLevel = AuditLevel.MEDIUM
    ):
        """记录业务操作"""
        audit_logger.log_action(
            action=AuditAction.UPDATE,  # 使用通用的UPDATE操作
            user_id=user_id,
            table_name=resource_type,
            record_id=resource_id,
            old_values=old_data,
            new_values=new_data,
            ip_address=ip_address,
            user_agent=user_agent,
            level=level,
            description=description or f"{action.value} - {resource_type}:{resource_id}"
        )

    @staticmethod
    def log_project_created(
        project_id: str,
        project_data: Dict[str, Any],
        user_id: str,
        request: Request = None
    ):
        """记录项目创建"""
        AuditService.log_business_action(
            action=BusinessAction.PROJECT_CREATE,
            user_id=user_id,
            resource_type="projects",
            resource_id=project_id,
            new_data=project_data,
            ip_address=getattr(request, 'client', {}).get('host') if request else None,
            user_agent=request.headers.get('user-agent') if request else None,
            description=f"创建项目: {project_data.get('name', 'unknown')}"
        )

    @staticmethod
    def log_daily_report_action(
        action: BusinessAction,
        report_id: str,
        user_id: str,
        report_data: Dict[str, Any] = None,
        approved_amount: float = None,
        rejection_reason: str = None,
        request: Request = None
    ):
        """记录日报操作"""
        new_data = report_data.copy() if report_data else {}

        if action == BusinessAction.DAILY_REPORT_APPROVE:
            if approved_amount is not None:
                new_data['approved_amount'] = approved_amount
            description = f"审核通过日报: {report_id}"
            level = AuditLevel.MEDIUM
        elif action == BusinessAction.DAILY_REPORT_REJECT:
            new_data['rejection_reason'] = rejection_reason
            description = f"驳回日报: {report_id} - {rejection_reason}"
            level = AuditLevel.HIGH
        else:
            description = f"提交日报: {report_id}"
            level = AuditLevel.LOW

        AuditService.log_business_action(
            action=action,
            user_id=user_id,
            resource_type="daily_reports",
            resource_id=report_id,
            new_data=new_data,
            ip_address=getattr(request, 'client', {}).get('host') if request else None,
            user_agent=request.headers.get('user-agent') if request else None,
            description=description,
            level=level
        )

    @staticmethod
    def log_topup_action(
        action: BusinessAction,
        topup_id: str,
        user_id: str,
        topup_data: Dict[str, Any] = None,
        approval_note: str = None,
        rejection_reason: str = None,
        payment_amount: float = None,
        request: Request = None
    ):
        """记录充值操作"""
        new_data = topup_data.copy() if topup_data else {}

        if action == BusinessAction.TOPUP_APPROVE_DATA:
            new_data['data_approval_note'] = approval_note
            description = f"初审通过充值申请: {topup_id}"
            level = AuditLevel.MEDIUM
        elif action == BusinessAction.TOPUP_APPROVE_FINANCE:
            new_data['finance_approval_note'] = approval_note
            description = f"财务终审通过充值申请: {topup_id}"
            level = AuditLevel.HIGH
        elif action == BusinessAction.TOPUP_REJECT:
            new_data['rejection_reason'] = rejection_reason
            description = f"驳回充值申请: {topup_id} - {rejection_reason}"
            level = AuditLevel.HIGH
        elif action == BusinessAction.TOPUP_PAYMENT_CONFIRM:
            new_data['payment_amount'] = payment_amount
            description = f"确认充值打款: {topup_id} - 金额: {payment_amount}"
            level = AuditLevel.CRITICAL
        else:
            description = f"提交充值申请: {topup_id}"
            level = AuditLevel.MEDIUM

        AuditService.log_business_action(
            action=action,
            user_id=user_id,
            resource_type="topups",
            resource_id=topup_id,
            new_data=new_data,
            ip_address=getattr(request, 'client', {}).get('host') if request else None,
            user_agent=request.headers.get('user-agent') if request else None,
            description=description,
            level=level
        )

    @staticmethod
    def log_reconciliation_action(
        action: BusinessAction,
        reconciliation_id: str,
        user_id: str,
        reconciliation_data: Dict[str, Any] = None,
        difference_amount: float = None,
        resolution_note: str = None,
        request: Request = None
    ):
        """记录对账操作"""
        new_data = reconciliation_data.copy() if reconciliation_data else {}

        if action == BusinessAction.RECONCILIATION_PROCESS:
            if difference_amount is not None:
                new_data['difference_amount'] = difference_amount
            description = f"执行对账: {reconciliation_id} - 差异: {difference_amount}"
            level = AuditLevel.MEDIUM
        elif action == BusinessAction.RECONCILIATION_RESOLVE:
            new_data['resolution_note'] = resolution_note
            description = f"解决对账差异: {reconciliation_id} - {resolution_note}"
            level = AuditLevel.HIGH
        else:
            description = f"创建对账任务: {reconciliation_id}"
            level = AuditLevel.LOW

        AuditService.log_business_action(
            action=action,
            user_id=user_id,
            resource_type="reconciliations",
            resource_id=reconciliation_id,
            new_data=new_data,
            ip_address=getattr(request, 'client', {}).get('host') if request else None,
            user_agent=request.headers.get('user-agent') if request else None,
            description=description,
            level=level
        )

    @staticmethod
    def log_ai_action(
        action: BusinessAction,
        resource_id: str,
        user_id: str = None,
        ai_data: Dict[str, Any] = None,
        anomaly_type: str = None,
        prediction_result: Dict[str, Any] = None,
        rule_name: str = None,
        request: Request = None
    ):
        """记录AI操作"""
        new_data = ai_data.copy() if ai_data else {}

        if action == BusinessAction.AI_ANOMALY_DETECTED:
            new_data['anomaly_type'] = anomaly_type
            description = f"检测到异常: {anomaly_type} - {resource_id}"
            level = AuditLevel.HIGH
        elif action == BusinessAction.AI_PREDICTION_GENERATED:
            new_data['prediction_result'] = prediction_result
            description = f"生成AI预测: {resource_id}"
            level = AuditLevel.MEDIUM
        elif action == BusinessAction.AI_RULE_TRIGGERED:
            new_data['rule_name'] = rule_name
            description = f"触发AI规则: {rule_name} - {resource_id}"
            level = AuditLevel.MEDIUM
        else:
            description = f"AI操作: {action.value} - {resource_id}"
            level = AuditLevel.LOW

        audit_logger.log_action(
            action=AuditAction.UPDATE,
            user_id=user_id or "system",  # AI操作可能没有具体用户
            table_name="ai_monitoring",
            record_id=resource_id,
            new_data=new_data,
            ip_address=getattr(request, 'client', {}).get('host') if request else None,
            user_agent=request.headers.get('user-agent') if request else None,
            description=description,
            level=level
        )

    @staticmethod
    def log_security_event(
        event_type: str,
        user_id: str,
        severity: str = "medium",
        details: Dict[str, Any] = None,
        request: Request = None,
        description: str = None
    ):
        """记录安全事件"""
        security_logger.log_security_event(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            ip_address=getattr(request, 'client', {}).get('host') if request else None,
            user_agent=request.headers.get('user-agent') if request else None,
            details=details,
            description=description
        )

    @staticmethod
    def log_permission_denied(
        user_id: str,
        resource: str,
        action: str,
        request: Request = None
    ):
        """记录权限拒绝事件"""
        AuditService.log_security_event(
            event_type="permission_denied",
            user_id=user_id,
            severity="high",
            details={
                "resource": resource,
                "action": action,
                "user_role": None  # 可以从用户数据获取
            },
            request=request,
            description=f"权限不足: {user_id} 尝试 {action} {resource}"
        )

    @staticmethod
    def log_data_export(
        user_id: str,
        table_name: str,
        record_count: int,
        filters: Dict[str, Any] = None,
        request: Request = None
    ):
        """记录数据导出"""
        audit_logger.log_export(
            table_name=table_name,
            record_count=record_count,
            user_id=user_id,
            ip_address=getattr(request, 'client', {}).get('host') if request else None,
            user_agent=request.headers.get('user-agent') if request else None,
            description=f"导出 {table_name} - 条件: {json.dumps(filters or {}, ensure_ascii=False)}"
        )

    @staticmethod
    def log_bulk_operation(
        operation: str,
        table_name: str,
        record_count: int,
        user_id: str,
        success_count: int = None,
        error_count: int = None,
        errors: List[str] = None,
        request: Request = None
    ):
        """记录批量操作"""
        details = {
            "operation": operation,
            "record_count": record_count,
            "success_count": success_count or record_count,
            "error_count": error_count or 0
        }

        if errors:
            details["errors"] = errors[:5]  # 只记录前5个错误

        level = AuditLevel.CRITICAL if error_count and error_count > 0 else AuditLevel.HIGH

        audit_logger.log_action(
            action=AuditAction.UPDATE,
            user_id=user_id,
            table_name=table_name,
            new_values=details,
            ip_address=getattr(request, 'client', {}).get('host') if request else None,
            user_agent=request.headers.get('user-agent') if request else None,
            description=f"批量{operation}: {table_name} - 总计: {record_count}, 成功: {success_count or record_count}, 失败: {error_count or 0}",
            level=level
        )


def get_audit_service() -> AuditService:
    """获取审计服务实例"""
    return AuditService()


# FastAPI依赖注入函数
def audit_dependency(
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    request: Request = None
) -> tuple[AuthenticatedUser, AuditService]:
    """审计依赖，返回当前用户和审计服务"""
    return current_user, get_audit_service()