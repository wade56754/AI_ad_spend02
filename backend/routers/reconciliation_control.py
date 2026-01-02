"""
对账中控 API 路由

OpenSpec Change: add-reconciliation-control-center
SoT References:
- API_SOT.md v9.3 (新增 §7 Reconciliation Control API)
- DATA_SCHEMA.md v5.4 §3.5.5, §3.5.6, §3.5.7
- STATE_MACHINE.md v2.6 §11.4
- AUTH_SPEC.md v2.0 (权限验证)

Phase 1 约束 (MASTER.md v4.4 §5):
- 提示 + 高亮 + 记录
- 不自动阻断

Version: 1.0
Author: Claude Code (OpenSpec apply)
"""

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.orm import Session

from backend.core.dependencies import get_db, get_current_user
from backend.core.response import success_response
from backend.models import User
from backend.models.reconciliation import RuleType, IssueType, IssueStatus
from backend.services.reconciliation_control_service import (
    SettlementRuleService,
    BalanceSnapshotService,
    ReconciliationIssueService,
    CommissionRuleService,
)
from backend.schemas.reconciliation import (
    SettlementRuleCreate,
    SettlementRuleUpdate,
    SettlementRuleResponse,
    SettlementRuleListResponse,
    BalanceSnapshotCreate,
    BalanceSnapshotBatchCreate,
    BalanceSnapshotResponse,
    BalanceSnapshotListResponse,
    ReconciliationIssueCreate,
    ReconciliationIssueAssign,
    ReconciliationIssueResolve,
    ReconciliationIssueResponse,
    ReconciliationIssueListResponse,
    ReconciliationIssueSummary,
    SettlementRuleType,
    BalanceSnapshotSource,
    ReconciliationIssueType,
    ReconciliationIssueStatus,
    CommissionRuleCreate,
    CommissionRuleUpdate,
    CommissionRuleResponse,
    CommissionCalculation,
)

router = APIRouter(
    prefix="/reconciliation-control",
    tags=["Reconciliation Control (对账中控)"],
)


# ==================== Settlement Rules ====================


@router.post(
    "/settlement-rules",
    response_model=dict,
    summary="创建结算规则",
    description="创建新的结算规则 (tiered/markup)",
)
async def create_settlement_rule(
    data: SettlementRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建结算规则"""
    service = SettlementRuleService(db)
    rule = service.create(data, current_user.id)
    return success_response(
        data=SettlementRuleResponse.model_validate(rule).model_dump(),
        message="结算规则创建成功",
    )


@router.get(
    "/settlement-rules", response_model=dict, summary="列出结算规则", description="查询结算规则列表"
)
async def list_settlement_rules(
    rule_type: Optional[SettlementRuleType] = Query(None, description="规则类型"),
    effective_date: Optional[date] = Query(None, description="生效日期"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出结算规则"""
    service = SettlementRuleService(db)
    rt = RuleType(rule_type.value) if rule_type else None
    rules, total = service.list_rules(rt, effective_date, skip, limit)
    return success_response(
        data={
            "items": [
                SettlementRuleResponse.model_validate(r).model_dump() for r in rules
            ],
            "meta": {"total": total, "skip": skip, "limit": limit},
        }
    )


@router.get(
    "/settlement-rules/{rule_id}",
    response_model=dict,
    summary="获取结算规则",
    description="根据ID获取结算规则详情",
)
async def get_settlement_rule(
    rule_id: int = Path(..., description="规则ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取结算规则"""
    service = SettlementRuleService(db)
    rule = service.get_by_id(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="结算规则不存在")
    return success_response(
        data=SettlementRuleResponse.model_validate(rule).model_dump()
    )


@router.patch(
    "/settlement-rules/{rule_id}",
    response_model=dict,
    summary="更新结算规则",
    description="更新结算规则配置",
)
async def update_settlement_rule(
    rule_id: int = Path(..., description="规则ID"),
    data: SettlementRuleUpdate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新结算规则"""
    service = SettlementRuleService(db)
    rule = service.update(rule_id, data)
    return success_response(
        data=SettlementRuleResponse.model_validate(rule).model_dump(),
        message="结算规则更新成功",
    )


@router.delete(
    "/settlement-rules/{rule_id}",
    response_model=dict,
    summary="删除结算规则",
    description="软删除结算规则（设置结束日期）",
)
async def delete_settlement_rule(
    rule_id: int = Path(..., description="规则ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除结算规则"""
    service = SettlementRuleService(db)
    service.delete(rule_id)
    return success_response(message="结算规则已删除")


# ==================== Balance Snapshots ====================


@router.post(
    "/balance-snapshots",
    response_model=dict,
    summary="创建余额快照",
    description="为广告账户创建余额/押款快照",
)
async def create_balance_snapshot(
    data: BalanceSnapshotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建余额快照"""
    service = BalanceSnapshotService(db)
    snapshot = service.create(data, current_user.id)
    return success_response(
        data=BalanceSnapshotResponse.model_validate(snapshot).model_dump(),
        message="余额快照创建成功",
    )


@router.post(
    "/balance-snapshots/batch",
    response_model=dict,
    summary="批量创建余额快照",
    description="批量导入余额快照",
)
async def batch_create_balance_snapshots(
    data: BalanceSnapshotBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量创建余额快照"""
    service = BalanceSnapshotService(db)
    snapshots = service.batch_create(data, current_user.id)
    return success_response(
        data={
            "created": len(snapshots),
            "items": [
                BalanceSnapshotResponse.model_validate(s).model_dump()
                for s in snapshots
            ],
        },
        message=f"成功创建 {len(snapshots)} 条快照",
    )


@router.get(
    "/balance-snapshots", response_model=dict, summary="列出余额快照", description="查询余额快照列表"
)
async def list_balance_snapshots(
    ad_account_id: Optional[int] = Query(None, description="广告账户ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出余额快照"""
    service = BalanceSnapshotService(db)
    snapshots, total = service.list_snapshots(
        ad_account_id, start_date, end_date, skip, limit
    )
    return success_response(
        data={
            "items": [
                BalanceSnapshotResponse.model_validate(s).model_dump()
                for s in snapshots
            ],
            "meta": {"total": total, "skip": skip, "limit": limit},
        }
    )


@router.get(
    "/balance-snapshots/{snapshot_id}",
    response_model=dict,
    summary="获取余额快照",
    description="根据ID获取余额快照详情",
)
async def get_balance_snapshot(
    snapshot_id: int = Path(..., description="快照ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取余额快照"""
    service = BalanceSnapshotService(db)
    snapshot = service.get_by_id(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="余额快照不存在")
    return success_response(
        data=BalanceSnapshotResponse.model_validate(snapshot).model_dump()
    )


@router.post(
    "/balance-snapshots/verify-conservation",
    response_model=dict,
    summary="验证守恒公式",
    description="验证对账守恒公式: Σ(充值) - Σ(消耗) = Δ(余额) + Δ(押款)",
)
async def verify_conservation(
    ad_account_id: int = Query(..., description="广告账户ID"),
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    topup_total: float = Query(..., description="期间充值总额"),
    spend_total: float = Query(..., description="期间消耗总额"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """验证守恒公式"""
    from decimal import Decimal

    service = BalanceSnapshotService(db)
    is_valid, details = service.verify_conservation(
        ad_account_id,
        start_date,
        end_date,
        Decimal(str(topup_total)),
        Decimal(str(spend_total)),
    )
    return success_response(
        data={"is_valid": is_valid, "details": details},
        message="守恒验证通过" if is_valid else "守恒验证失败",
    )


# ==================== Reconciliation Issues ====================


@router.post("/issues", response_model=dict, summary="创建差异单", description="创建对账差异单")
async def create_issue(
    data: ReconciliationIssueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建差异单"""
    service = ReconciliationIssueService(db)
    issue = service.create(data, current_user.id)
    return success_response(
        data=ReconciliationIssueResponse.model_validate(issue).model_dump(),
        message="差异单创建成功",
    )


@router.get("/issues", response_model=dict, summary="列出差异单", description="查询差异单列表")
async def list_issues(
    status: Optional[ReconciliationIssueStatus] = Query(None, description="状态"),
    issue_type: Optional[ReconciliationIssueType] = Query(None, description="差异类型"),
    ad_account_id: Optional[int] = Query(None, description="广告账户ID"),
    assigned_to: Optional[str] = Query(None, description="分配给 (UUID)"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    sla_breached: Optional[bool] = Query(None, description="是否SLA超时"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出差异单"""
    service = ReconciliationIssueService(db)
    st = IssueStatus(status.value) if status else None
    it = IssueType(issue_type.value) if issue_type else None
    at = UUID(assigned_to) if assigned_to else None

    issues, total = service.list_issues(
        st, it, ad_account_id, at, start_date, end_date, sla_breached, skip, limit
    )
    return success_response(
        data={
            "items": [
                ReconciliationIssueResponse.model_validate(i).model_dump()
                for i in issues
            ],
            "meta": {"total": total, "skip": skip, "limit": limit},
        }
    )


@router.get(
    "/issues/summary", response_model=dict, summary="差异单统计", description="获取差异单统计摘要"
)
async def get_issues_summary(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """获取差异单统计摘要"""
    service = ReconciliationIssueService(db)
    summary = service.get_summary()
    return success_response(data=summary)


@router.get(
    "/issues/{issue_id}",
    response_model=dict,
    summary="获取差异单",
    description="根据ID获取差异单详情",
)
async def get_issue(
    issue_id: int = Path(..., description="差异单ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取差异单"""
    service = ReconciliationIssueService(db)
    issue = service.get_by_id(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="差异单不存在")
    return success_response(
        data=ReconciliationIssueResponse.model_validate(issue).model_dump()
    )


@router.post(
    "/issues/{issue_id}/assign",
    response_model=dict,
    summary="分配差异单",
    description="将差异单分配给处理人",
)
async def assign_issue(
    issue_id: int = Path(..., description="差异单ID"),
    data: ReconciliationIssueAssign = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """分配差异单"""
    service = ReconciliationIssueService(db)
    issue = service.assign(issue_id, data, current_user.id)
    return success_response(
        data=ReconciliationIssueResponse.model_validate(issue).model_dump(),
        message="差异单已分配",
    )


@router.post(
    "/issues/{issue_id}/investigate",
    response_model=dict,
    summary="开始调查",
    description="开始调查差异单",
)
async def start_investigation(
    issue_id: int = Path(..., description="差异单ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """开始调查"""
    service = ReconciliationIssueService(db)
    issue = service.start_investigation(issue_id, current_user.id)
    return success_response(
        data=ReconciliationIssueResponse.model_validate(issue).model_dump(),
        message="开始调查差异单",
    )


@router.post(
    "/issues/{issue_id}/resolve",
    response_model=dict,
    summary="处理差异单",
    description="处理并记录差异单解决方案",
)
async def resolve_issue(
    issue_id: int = Path(..., description="差异单ID"),
    data: ReconciliationIssueResolve = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理差异单"""
    service = ReconciliationIssueService(db)
    issue = service.resolve(issue_id, data, current_user.id)
    return success_response(
        data=ReconciliationIssueResponse.model_validate(issue).model_dump(),
        message="差异单已处理",
    )


@router.post(
    "/issues/{issue_id}/close",
    response_model=dict,
    summary="关闭差异单",
    description="关闭已处理的差异单（终态）",
)
async def close_issue(
    issue_id: int = Path(..., description="差异单ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """关闭差异单"""
    service = ReconciliationIssueService(db)
    issue = service.close(issue_id, current_user.id)
    return success_response(
        data=ReconciliationIssueResponse.model_validate(issue).model_dump(),
        message="差异单已关闭",
    )


@router.post(
    "/issues/{issue_id}/reopen",
    response_model=dict,
    summary="重新打开差异单",
    description="重新打开已处理的差异单",
)
async def reopen_issue(
    issue_id: int = Path(..., description="差异单ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """重新打开差异单"""
    service = ReconciliationIssueService(db)
    issue = service.reopen(issue_id, current_user.id)
    return success_response(
        data=ReconciliationIssueResponse.model_validate(issue).model_dump(),
        message="差异单已重新打开",
    )


@router.post(
    "/issues/check-sla",
    response_model=dict,
    summary="检查SLA超时",
    description="检查并标记SLA超时的差异单（Phase 1: 仅标记）",
)
async def check_sla_breach(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """检查SLA超时"""
    service = ReconciliationIssueService(db)
    count = service.check_sla_breach()
    return success_response(
        data={"breached_count": count}, message=f"已标记 {count} 个SLA超时差异单"
    )


# ==================== Commission Rules (TASK-PRJ-003) ====================


@router.post(
    "/commission-rules",
    response_model=dict,
    summary="创建提成规则",
    description="创建新的提成规则 (阶梯提成)",
)
async def create_commission_rule(
    data: CommissionRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建提成规则

    TASK-PRJ-003: 提成配置
    - 阶梯提成: 按 conversions_final 计算
    - 累加计算: Σ(tier.count × tier.rate)
    """
    service = CommissionRuleService(db)
    rule = service.create(data, current_user.id)
    return success_response(
        data=CommissionRuleResponse.model_validate(rule).model_dump(),
        message="提成规则创建成功",
    )


@router.get(
    "/commission-rules",
    response_model=dict,
    summary="列出提成规则",
    description="查询提成规则列表",
)
async def list_commission_rules(
    effective_date: Optional[date] = Query(None, description="生效日期"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出提成规则"""
    service = CommissionRuleService(db)
    rules, total = service.list_rules(effective_date, skip, limit)
    return success_response(
        data={
            "items": [
                CommissionRuleResponse.model_validate(r).model_dump() for r in rules
            ],
            "meta": {"total": total, "skip": skip, "limit": limit},
        }
    )


@router.get(
    "/commission-rules/default",
    response_model=dict,
    summary="获取默认提成规则",
    description="获取当前默认的提成规则",
)
async def get_default_commission_rule(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取默认提成规则"""
    service = CommissionRuleService(db)
    rule = service.get_default_rule()
    if not rule:
        raise HTTPException(status_code=404, detail="未设置默认提成规则")
    return success_response(
        data=CommissionRuleResponse.model_validate(rule).model_dump()
    )


@router.get(
    "/commission-rules/{rule_id}",
    response_model=dict,
    summary="获取提成规则",
    description="根据ID获取提成规则详情",
)
async def get_commission_rule(
    rule_id: int = Path(..., description="规则ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取提成规则"""
    service = CommissionRuleService(db)
    rule = service.get_by_id(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="提成规则不存在")
    return success_response(
        data=CommissionRuleResponse.model_validate(rule).model_dump()
    )


@router.patch(
    "/commission-rules/{rule_id}",
    response_model=dict,
    summary="更新提成规则",
    description="更新提成规则配置",
)
async def update_commission_rule(
    rule_id: int = Path(..., description="规则ID"),
    data: CommissionRuleUpdate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新提成规则"""
    service = CommissionRuleService(db)
    rule = service.update(rule_id, data)
    return success_response(
        data=CommissionRuleResponse.model_validate(rule).model_dump(),
        message="提成规则更新成功",
    )


@router.delete(
    "/commission-rules/{rule_id}",
    response_model=dict,
    summary="删除提成规则",
    description="软删除提成规则（设置结束日期）",
)
async def delete_commission_rule(
    rule_id: int = Path(..., description="规则ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除提成规则"""
    service = CommissionRuleService(db)
    service.delete(rule_id)
    return success_response(message="提成规则已删除")


@router.post(
    "/commission-rules/{rule_id}/calculate",
    response_model=dict,
    summary="计算提成",
    description="根据进粉数计算提成金额",
)
async def calculate_commission(
    rule_id: int = Path(..., description="规则ID"),
    conversions: int = Query(..., ge=0, description="进粉数 (conversions_final)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    计算提成金额

    Example:
        tiers: [1-50: $1, 51-100: $1.5, 101+: $2]
        conversions: 120
        result: 50×1 + 50×1.5 + 20×2 = $165
    """
    service = CommissionRuleService(db)
    result = service.calculate_commission(rule_id, conversions)
    return success_response(
        data=CommissionCalculation.model_validate(result).model_dump(),
        message=f"提成计算完成: {result['total_commission']} CNY",
    )


@router.get(
    "/projects/{project_id}/effective-commission-rule",
    response_model=dict,
    summary="获取项目生效提成规则",
    description="获取项目当前生效的提成规则（优先项目配置，否则使用默认规则）",
)
async def get_project_effective_commission_rule(
    project_id: int = Path(..., description="项目ID"),
    target_date: Optional[date] = Query(None, description="目标日期（默认今天）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取项目生效的提成规则"""
    service = CommissionRuleService(db)
    rule = service.get_effective_rule_for_project(project_id, target_date)
    if not rule:
        raise HTTPException(status_code=404, detail="项目未配置有效的提成规则")
    return success_response(
        data=CommissionRuleResponse.model_validate(rule).model_dump()
    )
