"""
对账管理服务
Version: 2.0 (SoT Aligned - STATE_MACHINE.md v2.6)
Author: Claude协作开发

对账批次状态机（5状态）：
draft → pending_review → approved/needs_adjustment → completed
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, select

from backend.models import (
    ReconciliationBatch, ReconciliationDetail, ReconciliationAdjustment
)
# ReconciliationReport 可能尚未完全实现
try:
    from backend.models.reconciliation import ReconciliationReport
except (ImportError, AttributeError):
    ReconciliationReport = None
from backend.models import AdAccount
from backend.models import Project
from backend.models import Channel
from backend.models import User
from backend.models.base import ReconciliationBatchStatus, ReconciliationDetailStatus, UserRole
from backend.schemas.reconciliation import (
    ReconciliationBatchCreateRequest,
    ReconciliationDetailReviewRequest,
    ReconciliationAdjustmentCreateRequest,
    ReconciliationReportGenerateRequest,
    ReconciliationStatisticsResponse
)
from backend.utils.id_generator import generate_request_no
# Note: Response helpers moved to routers layer
from backend.exceptions.custom_exceptions import (
    ValidationError,
    ResourceNotFoundError,
    PermissionDeniedError,
    BusinessLogicError
)


def _safe_decimal(value, default: Decimal = Decimal('0.00')) -> Decimal:
    """
    安全地将值转换为 Decimal，防止 MagicMock 静默通过

    Args:
        value: 需要转换的值（None, str, int, float, Decimal）
        default: 默认值

    Returns:
        Decimal: 转换后的 Decimal 值

    Raises:
        TypeError: 如果 value 是 MagicMock 或其他不支持的类型
    """
    if value is None:
        return default

    # 检测 MagicMock（来自 unittest.mock）
    # MagicMock 会有 _mock_name 属性
    if hasattr(value, '_mock_name') or hasattr(value, '_mock_children'):
        raise TypeError(
            f"_safe_decimal 不接受 MagicMock 对象: {type(value).__name__}. "
            "请确保测试正确 mock 了数据库查询结果。"
        )

    if isinstance(value, Decimal):
        return value

    if isinstance(value, (int, float)):
        return Decimal(str(value))

    if isinstance(value, str):
        try:
            return Decimal(value)
        except Exception:
            return default

    # 其他不支持的类型
    raise TypeError(f"_safe_decimal 不支持的类型: {type(value).__name__}")


class ReconciliationService:
    """对账管理服务类"""

    def __init__(self, db: Session):
        self.db = db

    async def create_batch(
        self,
        request: ReconciliationBatchCreateRequest,
        current_user_id: int
    ) -> ReconciliationBatch:
        """创建对账批次"""
        # 检查是否已存在相同日期的对账
        # 使用 period_end 进行查询（reconciliation_date 是 period_end 的属性别名）
        existing = self.db.query(ReconciliationBatch).filter(
            ReconciliationBatch.period_end == request.reconciliation_date
        ).first()

        if existing:
            raise BusinessLogicError(
                message="该日期已存在对账批次",
                error_code="BIZ_302"
            )

        # 生成批次号
        batch_code = generate_request_no("REC")

        # 创建对账批次 - 使用 ReconciliationBatchStatus 枚举 (STATE_MACHINE.md v2.6)
        # 注意：使用 batch_code 和 period_start/period_end 作为模型字段名
        batch = ReconciliationBatch(
            batch_code=batch_code,
            period_start=request.reconciliation_date,
            period_end=request.reconciliation_date,
            status=ReconciliationBatchStatus.DRAFT.value,  # 初始状态为 draft
            created_by=current_user_id,
            # 注意：auto_match 和 notes 字段在模型中不存在
            # 如果需要存储 auto_match 逻辑，应在业务逻辑中处理而非持久化
        )

        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)

        return batch

    async def get_batches(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        current_user_id: int = None,
        user_role: str = None
    ) -> Tuple[List[ReconciliationBatch], int]:
        """获取对账批次列表"""
        query = self.db.query(ReconciliationBatch)

        # 根据角色过滤数据
        if user_role in ["account_manager", "media_buyer"]:
            # 只能看到自己项目的对账数据
            query = query.join(ReconciliationDetail).join(AdAccount)
            if user_role == "account_manager":
                query = query.join(Project).filter(
                    Project.account_manager_id == current_user_id
                )
            else:  # media_buyer
                query = query.filter(
                    AdAccount.assigned_user_id == current_user_id
                )

        # 应用过滤条件
        if status:
            query = query.filter(ReconciliationBatch.status == status)
        if date_from:
            # 使用 period_end 进行过滤（reconciliation_date 是其属性别名）
            query = query.filter(ReconciliationBatch.period_end >= date_from)
        if date_to:
            query = query.filter(ReconciliationBatch.period_end <= date_to)

        # 计算总数
        total = query.count()

        # 分页
        batches = query.order_by(
            ReconciliationBatch.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return batches, total

    async def get_batch_by_id(
        self,
        batch_id: int,
        current_user_id: int = None,
        user_role: str = None
    ) -> ReconciliationBatch:
        """获取对账批次详情"""
        batch = self.db.query(ReconciliationBatch).filter(
            ReconciliationBatch.id == batch_id
        ).first()

        if not batch:
            raise ResourceNotFoundError(
                message="对账批次不存在",
                error_code="SYS_004"
            )

        # 权限检查
        if user_role in ["account_manager", "media_buyer"]:
            has_permission = self.db.query(ReconciliationDetail).filter(
                ReconciliationDetail.batch_id == batch_id
            ).join(AdAccount)

            if user_role == "account_manager":
                has_permission = has_permission.join(Project).filter(
                    Project.account_manager_id == current_user_id
                )
            else:
                has_permission = has_permission.filter(
                    AdAccount.assigned_user_id == current_user_id
                )

            if not has_permission.first():
                raise PermissionDeniedError(
                    message="无权限访问此对账批次",
                    error_code="BIZ_303"
                )

        return batch

    async def run_reconciliation(
        self,
        batch_id: int,
        current_user_id: int
    ) -> ReconciliationBatch:
        """执行对账"""
        batch = await self.get_batch_by_id(batch_id, current_user_id, "admin")

        # 检查状态 - 只能从 draft 或 pending_review 状态执行对账
        if batch.status not in [ReconciliationBatchStatus.DRAFT.value, ReconciliationBatchStatus.PENDING_REVIEW.value]:
            raise BusinessLogicError(
                message="只能对草稿或待审核的批次执行对账",
                error_code="BIZ_306"
            )

        # 更新批次状态为 pending_review
        batch.status = ReconciliationBatchStatus.PENDING_REVIEW.value
        self.db.commit()

        try:
            # 获取所有活跃的广告账户
            ad_accounts = self.db.query(AdAccount).filter(
                AdAccount.status == "active"
            ).all()

            platform_total = Decimal('0.00')
            internal_total = Decimal('0.00')
            difference_total = Decimal('0.00')

            # 为每个账户创建对账详情
            for account in ad_accounts:
                # TODO: 从平台API获取消耗数据
                platform_spend = Decimal('0.00')  # 临时值

                # TODO: 从内部记录获取消耗数据
                internal_spend = Decimal('0.00')  # 临时值

                # 计算差异
                spend_difference = platform_spend - internal_spend
                is_matched = abs(spend_difference) < Decimal('0.01')

                # 创建对账详情
                # 注意：ReconciliationDetail 模型字段：system_spend, actual_spend, discrepancy, status
                detail = ReconciliationDetail(
                    batch_id=batch_id,
                    ad_account_id=account.id,
                    system_spend=platform_spend,
                    actual_spend=internal_spend,
                    discrepancy=spend_difference,
                    status=ReconciliationDetailStatus.CONFIRMED.value if is_matched else ReconciliationDetailStatus.PENDING.value,
                    notes=f"自动匹配" if is_matched else f"需要人工审核，差异: {spend_difference}"
                )

                self.db.add(detail)

                # 累计统计（用于更新 batch 汇总字段）
                platform_total += platform_spend
                internal_total += internal_spend
                difference_total += spend_difference

            # 更新批次汇总金额字段（这些字段在模型中存在）
            batch.total_system_spend = platform_total
            batch.total_actual_spend = internal_total
            batch.discrepancy = difference_total
            # 对账完成后状态为 approved（需人工审核后才 completed）
            batch.status = ReconciliationBatchStatus.APPROVED.value

            self.db.commit()

        except Exception as e:
            batch.status = ReconciliationBatchStatus.NEEDS_ADJUSTMENT.value  # 异常时需要调整
            self.db.commit()
            raise e

        return batch

    async def get_batch_details(
        self,
        batch_id: int,
        page: int = 1,
        page_size: int = 20,
        match_status: Optional[str] = None,
        current_user_id: int = None,
        user_role: str = None
    ) -> Tuple[List[ReconciliationDetail], int]:
        """获取对账详情列表"""
        # 权限检查
        await self.get_batch_by_id(batch_id, current_user_id, user_role)

        query = self.db.query(ReconciliationDetail).filter(
            ReconciliationDetail.batch_id == batch_id
        )

        # 应用过滤条件
        # 注意：ReconciliationDetail 使用 status 字段，不是 match_status
        if match_status:
            query = query.filter(ReconciliationDetail.status == match_status)

        # 计算总数
        total = query.count()

        # 分页查询
        details = query.order_by(
            ReconciliationDetail.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return details, total

    async def review_detail(
        self,
        detail_id: int,
        request: ReconciliationDetailReviewRequest,
        current_user_id: int
    ) -> ReconciliationDetail:
        """审核对账差异"""
        detail = self.db.query(ReconciliationDetail).filter(
            ReconciliationDetail.id == detail_id
        ).first()

        if not detail:
            raise ResourceNotFoundError(
                message="对账详情不存在",
                error_code="SYS_004"
            )

        # 对账详情状态检查 - pending, confirmed, adjusted 可审核
        # 注意：使用 status 字段，而不是 match_status
        if detail.status not in [ReconciliationDetailStatus.PENDING.value, ReconciliationDetailStatus.CONFIRMED.value, ReconciliationDetailStatus.ADJUSTED.value]:
            raise BusinessLogicError(
                message="只能审核待处理或异常的对账详情",
                error_code="BIZ_306"
            )

        # 更新审核信息
        # 注意：ReconciliationDetail 模型只有 notes 字段，没有 reviewed_by, reviewed_at, review_notes 等字段
        # 将审核信息存储在 notes 字段中
        review_info = f"审核人: {current_user_id}, 时间: {datetime.utcnow().isoformat()}"
        if request.review_notes:
            review_info += f", 备注: {request.review_notes}"
        detail.notes = review_info

        # 更新匹配状态
        # 注意：ReconciliationDetail 模型没有 is_matched, match_status, auto_confidence, difference_type, difference_reason 字段
        # 使用 status 字段来表示匹配状态：confirmed = 匹配，adjusted = 不匹配，pending = 待审核
        if request.action == "approve" and request.is_matched:
            detail.status = ReconciliationDetailStatus.CONFIRMED.value
        elif request.action == "reject":
            detail.status = ReconciliationDetailStatus.ADJUSTED.value
        elif request.action == "investigate":
            # 保持 pending 状态，等待人工审核
            detail.status = ReconciliationDetailStatus.PENDING.value

        # 如果指定了最终状态，映射到 status 字段
        if request.match_status:
            # 将 match_status 映射到 status 枚举值
            status_map = {
                "matched": ReconciliationDetailStatus.CONFIRMED.value,
                "exception": ReconciliationDetailStatus.ADJUSTED.value,
                "manual_review": ReconciliationDetailStatus.PENDING.value,
            }
            detail.status = status_map.get(request.match_status, detail.status)

        self.db.commit()
        self.db.refresh(detail)

        # 更新批次统计
        await self._update_batch_statistics(detail.batch_id)

        return detail

    async def create_adjustment(
        self,
        detail_id: int,
        request: ReconciliationAdjustmentCreateRequest,
        current_user_id: int
    ) -> ReconciliationAdjustment:
        """创建调整记录"""
        detail = self.db.query(ReconciliationDetail).filter(
            ReconciliationDetail.id == detail_id
        ).first()

        if not detail:
            raise ResourceNotFoundError(
                message="对账详情不存在",
                error_code="SYS_004"
            )

        # 创建调整记录 - 使用 SoT DATA_SCHEMA.md v5.2 定义的字段
        # 字段：detail_id, adjustment_type, amount, reason, created_by
        adjustment = ReconciliationAdjustment(
            detail_id=detail_id,
            adjustment_type=request.adjustment_type,
            amount=request.adjustment_amount,
            reason=request.detailed_reason or request.adjustment_reason,
            created_by=current_user_id
        )

        self.db.add(adjustment)
        self.db.commit()
        self.db.refresh(adjustment)

        # 更新对账详情状态为已调整
        detail.status = ReconciliationDetailStatus.ADJUSTED.value
        detail.notes = f"调整金额: {request.adjustment_amount}, 原因: {request.adjustment_reason}"

        self.db.commit()

        # 更新批次统计
        await self._update_batch_statistics(detail.batch_id)

        return adjustment

    async def get_statistics(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        current_user_id: int = None,
        user_role: str = None
    ) -> ReconciliationStatisticsResponse:
        """获取对账统计信息"""
        query = self.db.query(ReconciliationBatch)

        # 根据角色过滤数据
        if user_role in ["account_manager", "media_buyer"]:
            query = query.join(ReconciliationDetail).join(AdAccount)
            if user_role == "account_manager":
                query = query.join(Project).filter(
                    Project.account_manager_id == current_user_id
                )
            else:  # media_buyer
                query = query.filter(
                    AdAccount.assigned_user_id == current_user_id
                )

        # 应用日期过滤（使用 period_end，reconciliation_date 是其属性别名）
        if date_from:
            query = query.filter(ReconciliationBatch.period_end >= date_from)
        if date_to:
            query = query.filter(ReconciliationBatch.period_end <= date_to)

        # 总体统计 - 使用 ReconciliationBatchStatus 枚举 (STATE_MACHINE.md v2.6)
        total_batches = query.count()
        completed_batches = query.filter(
            ReconciliationBatch.status == ReconciliationBatchStatus.COMPLETED.value
        ).count()
        exception_batches = query.filter(
            ReconciliationBatch.status == ReconciliationBatchStatus.NEEDS_ADJUSTMENT.value
        ).count()
        resolved_batches = query.filter(
            ReconciliationBatch.status == ReconciliationBatchStatus.APPROVED.value
        ).count()

        # 账户统计
        details_query = self.db.query(ReconciliationDetail).join(ReconciliationBatch)
        if user_role in ["account_manager", "media_buyer"]:
            details_query = details_query.join(AdAccount)
            if user_role == "account_manager":
                details_query = details_query.join(Project).filter(
                    Project.account_manager_id == current_user_id
                )
            else:
                details_query = details_query.filter(
                    AdAccount.assigned_user_id == current_user_id
                )

        total_accounts = details_query.count()
        # 注意：ReconciliationDetail 模型没有 is_matched 字段
        # 使用 discrepancy 接近 0 来判断是否匹配（容忍 0.01 的误差）
        matched_accounts = details_query.filter(
            func.abs(ReconciliationDetail.discrepancy) < Decimal('0.01')
        ).count()
        mismatched_accounts = total_accounts - matched_accounts

        # 金额统计
        from sqlalchemy import cast, Numeric
        batch_stats = query.with_entities(
            func.sum(cast(ReconciliationBatch.total_system_spend, Numeric(15, 2))).label('platform_total'),
            func.sum(cast(ReconciliationBatch.total_actual_spend, Numeric(15, 2))).label('internal_total'),
            func.sum(cast(ReconciliationBatch.discrepancy, Numeric(15, 2))).label('difference_total')
        ).first()

        # 安全处理空值和类型转换，防止 MagicMock 静默通过
        if batch_stats is None:
            total_platform_spend = Decimal('0.00')
            total_internal_spend = Decimal('0.00')
            total_difference = Decimal('0.00')
        else:
            total_platform_spend = _safe_decimal(
                getattr(batch_stats, 'platform_total', None),
                Decimal('0.00')
            )
            total_internal_spend = _safe_decimal(
                getattr(batch_stats, 'internal_total', None),
                Decimal('0.00')
            )
            total_difference = _safe_decimal(
                getattr(batch_stats, 'difference_total', None),
                Decimal('0.00')
            )

        # 调整金额统计
        # 注意：如果 ReconciliationAdjustment 不存在，返回 0
        if ReconciliationAdjustment is None:
            total_adjustments = Decimal('0.00')
        else:
            adjustments_query = self.db.query(ReconciliationAdjustment)
            if user_role in ["account_manager", "media_buyer"]:
                adjustments_query = adjustments_query.join(ReconciliationDetail).join(ReconciliationBatch)
                if user_role == "account_manager":
                    adjustments_query = adjustments_query.join(AdAccount).join(Project).filter(
                        Project.account_manager_id == current_user_id
                    )
                else:
                    adjustments_query = adjustments_query.join(AdAccount).filter(
                        AdAccount.assigned_user_id == current_user_id
                    )

            adjustments_scalar = adjustments_query.with_entities(
                func.sum(cast(ReconciliationAdjustment.amount, Numeric(15, 2)))
            ).scalar()
            total_adjustments = _safe_decimal(adjustments_scalar, Decimal('0.00'))

        # 效率统计
        if total_accounts > 0:
            auto_match_rate = (matched_accounts / total_accounts) * 100
            manual_review_rate = (mismatched_accounts / total_accounts) * 100
            difference_rate = (total_difference / total_platform_spend * 100) if total_platform_spend > 0 else 0
        else:
            auto_match_rate = 0
            manual_review_rate = 0
            difference_rate = 0

        resolution_rate = (resolved_batches / total_batches * 100) if total_batches > 0 else 0

        # 平均处理时间（小时）
        # 注意：ReconciliationBatch 使用 created_at 和 closed_at，而不是 started_at 和 completed_at
        avg_processing_time = self.db.query(
            func.avg(
                func.extract(
                    'epoch',
                    ReconciliationBatch.closed_at - ReconciliationBatch.created_at
                ) / 3600
            )
        ).filter(
            ReconciliationBatch.created_at.isnot(None),
            ReconciliationBatch.closed_at.isnot(None)
        ).scalar() or 0

        # 净差异（调整后）
        net_difference = total_difference - total_adjustments

        # 趋势数据（简化版）
        monthly_trends = []
        daily_trends = []
        top_difference_reasons = []
        channel_performance = []
        top_mismatched_accounts = []

        return ReconciliationStatisticsResponse(
            total_batches=total_batches,
            completed_batches=completed_batches,
            exception_batches=exception_batches,
            resolved_batches=resolved_batches,
            total_accounts=total_accounts,
            matched_accounts=matched_accounts,
            mismatched_accounts=mismatched_accounts,
            total_platform_spend=total_platform_spend,
            total_internal_spend=total_internal_spend,
            total_difference=total_difference,
            total_adjustments=total_adjustments,
            net_difference=net_difference,
            auto_match_rate=round(auto_match_rate, 2),
            manual_review_rate=round(manual_review_rate, 2),
            resolution_rate=round(resolution_rate, 2),
            avg_processing_time_hours=round(float(avg_processing_time), 2),
            difference_rate=round(float(difference_rate), 2),
            monthly_trends=monthly_trends,
            daily_trends=daily_trends,
            top_difference_reasons=top_difference_reasons,
            channel_performance=channel_performance,
            top_mismatched_accounts=top_mismatched_accounts
        )

    async def export_reconciliation_data(
        self,
        batch_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        format_type: str = "excel",
        current_user_id: int = None,
        user_role: str = None
    ) -> List[Dict[str, Any]]:
        """导出对账数据"""
        query = self.db.query(ReconciliationDetail).join(ReconciliationBatch)

        # 根据角色过滤
        if user_role in ["account_manager", "media_buyer"]:
            query = query.join(AdAccount)
            if user_role == "account_manager":
                query = query.join(Project).filter(
                    Project.account_manager_id == current_user_id
                )
            else:
                query = query.filter(
                    AdAccount.assigned_user_id == current_user_id
                )

        # 应用过滤条件
        if batch_id:
            query = query.filter(ReconciliationDetail.batch_id == batch_id)
        if date_from:
            # 使用 period_end（reconciliation_date 是其属性别名）
            query = query.filter(ReconciliationBatch.period_end >= date_from)
        if date_to:
            query = query.filter(ReconciliationBatch.period_end <= date_to)

        # 获取数据
        details = query.all()

        # 转换为导出格式
        export_data = []
        for detail in details:
            # 通过 ad_account 关系访问 project 和 channel
            export_data.append({
                "batch_no": detail.batch.batch_no,
                "reconciliation_date": detail.batch.reconciliation_date.isoformat(),
                "ad_account_name": detail.ad_account.account_name,
                "project_name": detail.ad_account.project.name if detail.ad_account.project else None,
                "channel_name": detail.ad_account.channel.name if detail.ad_account.channel else None,
                "platform_spend": float(detail.system_spend),
                "internal_spend": float(detail.actual_spend),
                "spend_difference": float(detail.discrepancy),
                "is_matched": abs(detail.discrepancy) < Decimal('0.01'),  # 基于 discrepancy 计算
                "match_status": detail.status,  # 使用 status 字段
                "difference_type": None,  # 模型中没有此字段
                "difference_reason": detail.notes,  # 使用 notes 字段
                "created_at": detail.created_at.isoformat()
            })

        return export_data

    async def _update_batch_statistics(self, batch_id: int):
        """更新批次统计信息

        注意：根据 SoT spec，统计字段如 total_accounts, matched_accounts 等
        应从 ReconciliationDetail 记录按需计算，不存储在数据库中。
        仅更新批次的汇总金额字段：total_system_spend, total_actual_spend, discrepancy
        """
        batch = self.db.query(ReconciliationBatch).filter(
            ReconciliationBatch.id == batch_id
        ).first()

        if not batch:
            return

        # 重新计算汇总金额
        details = self.db.query(ReconciliationDetail).filter(
            ReconciliationDetail.batch_id == batch_id
        ).all()

        # 仅更新模型中存在的汇总金额字段
        batch.total_system_spend = sum(d.system_spend for d in details) if details else Decimal('0.00')
        batch.total_actual_spend = sum(d.actual_spend for d in details) if details else Decimal('0.00')
        batch.discrepancy = sum(d.discrepancy for d in details) if details else Decimal('0.00')

        self.db.commit()