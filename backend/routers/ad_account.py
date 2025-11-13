"""
广告账户管理路由
Version: 1.0
Author: Claude协作开发
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import get_current_user
from models.user import User
from models.ad_account import AdAccount, AccountAlert, AccountNote
from schemas.ad_account import (
    AdAccountCreateRequest,
    AdAccountUpdateRequest,
    AdAccountResponse,
    AdAccountListResponse,
    AdAccountMini,
    AdAccountStatusUpdateRequest,
    AdAccountBudgetUpdateRequest,
    AccountAlertCreateRequest,
    AccountAlertUpdateRequest,
    AccountAlertResponse,
    AccountNoteCreateRequest,
    AccountNoteResponse,
    AdAccountStatisticsResponse
)
from services.ad_account_service import AdAccountService
from services.audit_log_service import AuditLogService
from utils.decorators import require_role
from utils.response import success_response, paginated_response
from utils.export import export_to_excel, export_to_pdf
from exceptions import ValidationError, NotFoundError, PermissionError


router = APIRouter(prefix="/ad-accounts", tags=["广告账户管理"])


def get_ad_account_service(db: Session = Depends(get_db)) -> AdAccountService:
    """获取广告账户服务实例"""
    return AdAccountService(db)


def get_audit_service(db: Session = Depends(get_db)) -> AuditLogService:
    """获取审计日志服务实例"""
    return AuditLogService(db)


@router.get("", response_model=dict)
@require_role(["admin", "finance", "data_operator", "account_manager", "media_buyer"])
async def get_ad_accounts(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="账户状态"),
    platform: Optional[str] = Query(None, description="广告平台"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    channel_id: Optional[int] = Query(None, description="渠道ID"),
    assigned_user_id: Optional[int] = Query(None, description="负责投手ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AdAccountService = Depends(get_ad_account_service)
):
    """获取广告账户列表"""
    try:
        accounts, total = await service.get_accounts(
            page=page,
            page_size=page_size,
            status=status,
            platform=platform,
            project_id=project_id,
            channel_id=channel_id,
            assigned_user_id=assigned_user_id,
            current_user_id=current_user.id,
            user_role=current_user.role
        )

        # 转换为响应格式
        account_responses = []
        for account in accounts:
            account_data = AdAccountResponse.model_validate(account)

            # 获取关联名称
            if hasattr(account, 'project') and account.project:
                account_data.project_name = account.project.name
            if hasattr(account, 'channel') and account.channel:
                account_data.channel_name = account.channel.name
            if hasattr(account, 'assigned_user') and account.assigned_user:
                account_data.assigned_user_name = account.assigned_user.name
            if hasattr(account, 'creator') and account.creator:
                account_data.created_by_name = account.creator.name

            # 计算活跃天数
            if account.activated_date:
                days_active = (datetime.utcnow() - account.activated_date).days
                account_data.days_active = days_active

            # 计算预算使用率
            if account.total_budget and account.total_budget > 0:
                account_data.budget_utilization = round(
                    float(account.total_spend / account.total_budget * 100), 2
                )

            # TODO: 获取近7天数据
            # account_data.recent_spend_7d = ...
            # account_data.recent_leads_7d = ...

            account_responses.append(account_data)

        return paginated_response(
            items=account_responses,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
@require_role(["admin", "account_manager"])
async def create_ad_account(
    request: AdAccountCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AdAccountService = Depends(get_ad_account_service),
    audit_service: AuditLogService = Depends(get_audit_service)
):
    """创建广告账户"""
    try:
        account = await service.create_account(request, current_user.id)

        # 记录审计日志
        await audit_service.log_action(
            user_id=current_user.id,
            action="create",
            resource_type="ad_account",
            resource_id=account.id,
            details=f"创建广告账户: {account.name}"
        )

        return success_response(
            data=AdAccountResponse.model_validate(account),
            message="广告账户创建成功",
            status_code=status.HTTP_201_CREATED
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.error_code, "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{account_id}", response_model=dict)
@require_role(["admin", "finance", "data_operator", "account_manager", "media_buyer"])
async def get_ad_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AdAccountService = Depends(get_ad_account_service)
):
    """获取广告账户详情"""
    try:
        account = await service.get_account_by_id(
            account_id,
            current_user.id,
            current_user.role
        )

        account_data = AdAccountResponse.model_validate(account)

        # 获取关联名称
        if hasattr(account, 'project') and account.project:
            account_data.project_name = account.project.name
        if hasattr(account, 'channel') and account.channel:
            account_data.channel_name = account.channel.name
        if hasattr(account, 'assigned_user') and account.assigned_user:
            account_data.assigned_user_name = account.assigned_user.name
        if hasattr(account, 'creator') and account.creator:
            account_data.created_by_name = account.creator.name

        return success_response(data=account_data)

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.error_code, "message": str(e)}
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": e.error_code, "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{account_id}", response_model=dict)
@require_role(["admin", "account_manager"])
async def update_ad_account(
    account_id: int,
    request: AdAccountUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AdAccountService = Depends(get_ad_account_service)
):
    """更新广告账户"""
    try:
        account = await service.update_account(account_id, request, current_user.id)

        return success_response(
            data=AdAccountResponse.model_validate(account),
            message="广告账户更新成功"
        )

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.error_code, "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{account_id}/status", response_model=dict)
@require_role(["admin", "account_manager", "finance"])
async def update_ad_account_status(
    account_id: int,
    request: AdAccountStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AdAccountService = Depends(get_ad_account_service)
):
    """更新账户状态"""
    try:
        account = await service.update_account_status(
            account_id,
            request,
            current_user.id
        )

        return success_response(
            data=AdAccountResponse.model_validate(account),
            message="账户状态更新成功"
        )

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.error_code, "message": str(e)}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.error_code, "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{account_id}/budget", response_model=dict)
@require_role(["admin", "account_manager", "finance"])
async def update_ad_account_budget(
    account_id: int,
    request: AdAccountBudgetUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AdAccountService = Depends(get_ad_account_service)
):
    """更新账户预算"""
    try:
        account = await service.update_account_budget(
            account_id,
            request,
            current_user.id
        )

        return success_response(
            data=AdAccountResponse.model_validate(account),
            message="账户预算更新成功"
        )

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.error_code, "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/statistics/overview", response_model=dict)
@require_role(["admin", "finance", "data_operator", "account_manager"])
async def get_ad_accounts_statistics(
    project_id: Optional[int] = Query(None, description="项目ID"),
    channel_id: Optional[int] = Query(None, description="渠道ID"),
    platform: Optional[str] = Query(None, description="广告平台"),
    date_from: Optional[str] = Query(None, description="开始日期"),
    date_to: Optional[str] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AdAccountService = Depends(get_ad_account_service)
):
    """获取广告账户统计"""
    try:
        from datetime import datetime

        # 转换日期
        start_date = datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else None
        end_date = datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else None

        statistics = await service.get_statistics(
            project_id=project_id,
            channel_id=channel_id,
            platform=platform,
            date_from=start_date,
            date_to=end_date,
            current_user_id=current_user.id,
            user_role=current_user.role
        )

        return success_response(data=statistics)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{account_id}/alerts", response_model=dict)
@require_role(["admin", "finance", "data_operator", "account_manager", "media_buyer"])
async def get_account_alerts(
    account_id: int,
    status: Optional[str] = Query(None, description="预警状态"),
    severity: Optional[str] = Query(None, description="严重程度"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AdAccountService = Depends(get_ad_account_service)
):
    """获取账户预警列表"""
    try:
        alerts = await service.get_account_alerts(
            account_id,
            status=status,
            severity=severity,
            current_user_id=current_user.id,
            user_role=current_user.role
        )

        alert_responses = []
        for alert in alerts:
            alert_data = AccountAlertResponse.model_validate(alert)
            if hasattr(alert, 'account') and alert.account:
                alert_data.account_name = alert.account.name
            alert_responses.append(alert_data)

        return success_response(data=alert_responses)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{account_id}/alerts", response_model=dict)
@require_role(["admin", "account_manager"])
async def create_account_alert(
    account_id: int,
    request: AccountAlertCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AdAccountService = Depends(get_ad_account_service)
):
    """创建账户预警"""
    try:
        alert = await service.create_account_alert(
            account_id,
            request,
            current_user.id
        )

        return success_response(
            data=AccountAlertResponse.model_validate(alert),
            message="预警创建成功"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/alerts/{alert_id}", response_model=dict)
@require_role(["admin", "account_manager"])
async def update_account_alert(
    alert_id: int,
    request: AccountAlertUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AdAccountService = Depends(get_ad_account_service)
):
    """更新账户预警"""
    try:
        alert = await service.update_account_alert(
            alert_id,
            request,
            current_user.id
        )

        return success_response(
            data=AccountAlertResponse.model_validate(alert),
            message="预警更新成功"
        )

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.error_code, "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{account_id}/notes", response_model=dict)
@require_role(["admin", "finance", "data_operator", "account_manager", "media_buyer"])
async def get_account_notes(
    account_id: int,
    note_type: Optional[str] = Query(None, description="备注类型"),
    is_resolved: Optional[bool] = Query(None, description="是否已解决"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AdAccountService = Depends(get_ad_account_service)
):
    """获取账户备注列表"""
    try:
        notes = await service.get_account_notes(
            account_id,
            note_type=note_type,
            is_resolved=is_resolved,
            current_user_id=current_user.id,
            user_role=current_user.role
        )

        note_responses = []
        for note in notes:
            note_data = AccountNoteResponse.model_validate(note)
            if hasattr(note, 'account') and note.account:
                note_data.account_name = note.account.name
            if hasattr(note, 'creator') and note.creator:
                note_data.created_by_name = note.creator.name
            note_responses.append(note_data)

        return success_response(data=note_responses)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{account_id}/notes", response_model=dict)
@require_role(["admin", "account_manager", "media_buyer"])
async def create_account_note(
    account_id: int,
    request: AccountNoteCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AdAccountService = Depends(get_ad_account_service)
):
    """创建账户备注"""
    try:
        note = await service.create_account_note(
            account_id,
            request,
            current_user.id
        )

        return success_response(
            data=AccountNoteResponse.model_validate(note),
            message="备注创建成功"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{account_id}/history/status", response_model=dict)
@require_role(["admin", "finance", "data_operator", "account_manager", "media_buyer"])
async def get_account_status_history(
    account_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AdAccountService = Depends(get_ad_account_service)
):
    """获取账户状态历史"""
    try:
        # 权限检查
        await service.get_account_by_id(account_id, current_user.id, current_user.role)

        # TODO: 实现状态历史查询
        # history = await service.get_status_history(account_id, page, page_size)

        return success_response(
            data=[],
            message="状态历史查询成功"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{account_id}", response_model=dict)
@require_role(["admin"])
async def delete_ad_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AdAccountService = Depends(get_ad_account_service)
):
    """删除广告账户（软删除）"""
    try:
        success = await service.delete_account(account_id, current_user.id)

        return success_response(
            message="广告账户删除成功"
        )

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.error_code, "message": str(e)}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.error_code, "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/export/excel")
@require_role(["admin", "finance", "data_operator", "account_manager"])
async def export_ad_accounts(
    status: Optional[str] = Query(None, description="账户状态"),
    platform: Optional[str] = Query(None, description="广告平台"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AdAccountService = Depends(get_ad_account_service)
):
    """导出广告账户数据"""
    try:
        # 获取数据
        accounts, _ = await service.get_accounts(
            page=1,
            page_size=10000,  # 大批量导出
            status=status,
            platform=platform,
            project_id=project_id,
            current_user_id=current_user.id,
            user_role=current_user.role
        )

        # 转换为导出格式
        export_data = []
        for account in accounts:
            export_data.append({
                "账户ID": account.account_id,
                "账户名称": account.name,
                "平台": account.platform,
                "状态": account.status,
                "项目": account.project.name if account.project else "",
                "渠道": account.channel.name if account.channel else "",
                "负责投手": account.assigned_user.name if account.assigned_user else "",
                "日预算": float(account.daily_budget) if account.daily_budget else 0,
                "总预算": float(account.total_budget) if account.total_budget else 0,
                "总消耗": float(account.total_spend),
                "总潜在客户": account.total_leads,
                "平均CPL": float(account.avg_cpl) if account.avg_cpl else 0,
                "最佳CPL": float(account.best_cpl) if account.best_cpl else 0,
                "货币": account.currency,
                "创建时间": account.created_at.isoformat() if account.created_at else "",
                "激活时间": account.activated_date.isoformat() if account.activated_date else ""
            })

        # 导出Excel
        file_content = export_to_excel(export_data, sheet_name="广告账户列表")
        filename = f"ad_accounts_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"

        return StreamingResponse(
            iter([file_content]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/mini", response_model=dict)
@require_role(["admin", "finance", "data_operator", "account_manager", "media_buyer"])
async def get_ad_accounts_mini(
    project_id: Optional[int] = Query(None, description="项目ID"),
    status: Optional[str] = Query(None, description="状态筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取广告账户迷你信息列表（用于下拉选择）"""
    try:
        query = db.query(AdAccount)

        # 根据角色过滤
        if current_user.role == "media_buyer":
            query = query.filter(AdAccount.assigned_user_id == current_user.id)
        elif current_user.role == "account_manager":
            query = query.join(Project).filter(
                Project.account_manager_id == current_user.id
            )

        # 应用过滤
        if project_id:
            query = query.filter(AdAccount.project_id == project_id)
        if status:
            query = query.filter(AdAccount.status == status)

        # 获取数据
        accounts = query.order_by(AdAccount.name).limit(100).all()

        # 转换格式
        result = []
        for account in accounts:
            mini = AdAccountMini.model_validate(account)
            if account.assigned_user:
                mini.assigned_user_name = account.assigned_user.name
            result.append(mini)

        return success_response(data=result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )