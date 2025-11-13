"""
对账管理服务
Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, select

from models.reconciliation import (
    ReconciliationBatch, ReconciliationDetail,
    ReconciliationAdjustment, ReconciliationReport
)
from models.ad_account import AdAccount
from models.project import Project
from models.channel import Channel
from models.user import User
from schemas.reconciliation import (
    ReconciliationBatchCreateRequest,
    ReconciliationDetailReviewRequest,
    ReconciliationAdjustmentCreateRequest,
    ReconciliationReportGenerateRequest,
    ReconciliationStatisticsResponse
)
from utils.id_generator import generate_request_no
from utils.response import success_response, error_response
from exceptions import ValidationError, NotFoundError, PermissionError


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
        existing = self.db.query(ReconciliationBatch).filter(
            ReconciliationBatch.reconciliation_date == request.reconciliation_date
        ).first()

        if existing:
            raise ValidationError(
                "BIZ_302",
                "该日期已存在对账批次"
            )

        # 生成批次号
        batch_no = generate_request_no("REC")

        # 创建对账批次
        batch = ReconciliationBatch(
            batch_no=batch_no,
            reconciliation_date=request.reconciliation_date,
            status="pending",
            auto_match=request.auto_match,
            created_by=current_user_id,
            notes=request.notes
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
            query = query.filter(ReconciliationBatch.reconciliation_date >= date_from)
        if date_to:
            query = query.filter(ReconciliationBatch.reconciliation_date <= date_to)

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
            raise NotFoundError("SYS_004", "对账批次不存在")

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
                raise PermissionError("BIZ_303", "无权限访问此对账批次")

        return batch

    async def run_reconciliation(
        self,
        batch_id: int,
        current_user_id: int
    ) -> ReconciliationBatch:
        """执行对账"""
        batch = await self.get_batch_by_id(batch_id, current_user_id, "admin")

        if batch.status != "pending":
            raise ValidationError("BIZ_306", "只能对待处理的批次执行对账")

        # 更新批次状态
        batch.status = "processing"
        batch.started_at = datetime.utcnow()
        self.db.commit()

        try:
            # 获取所有活跃的广告账户
            ad_accounts = self.db.query(AdAccount).filter(
                AdAccount.status == "active"
            ).all()

            total_accounts = len(ad_accounts)
            matched_count = 0
            mismatched_count = 0
            auto_matched_count = 0

            platform_total = Decimal('0.00')
            internal_total = Decimal('0.00')
            difference_total = Decimal('0.00')

            # 为每个账户创建对账详情
            for account in ad_accounts:
                # TODO: 从平台API获取消耗数据
                platform_spend = Decimal('0.00')  # 临时值
                platform_data_date = date.today()

                # TODO: 从内部记录获取消耗数据
                internal_spend = Decimal('0.00')  # 临时值
                internal_data_date = date.today()

                # 计算差异
                spend_difference = platform_spend - internal_spend
                is_matched = abs(spend_difference) < Decimal('0.01')

                # 判断匹配状态
                if is_matched:
                    match_status = "auto_matched" if batch.auto_match else "matched"
                    if batch.auto_match:
                        auto_matched_count += 1
                    matched_count += 1
                else:
                    match_status = "manual_review"
                    mismatched_count += 1

                # 创建对账详情
                detail = ReconciliationDetail(
                    batch_id=batch_id,
                    ad_account_id=account.id,
                    project_id=account.project_id,
                    channel_id=account.channel_id,
                    platform_spend=platform_spend,
                    platform_data_date=platform_data_date,
                    internal_spend=internal_spend,
                    internal_data_date=internal_data_date,
                    spend_difference=spend_difference,
                    is_matched=is_matched,
                    match_status=match_status,
                    auto_confidence=Decimal('1.00') if is_matched else Decimal('0.00')
                )

                self.db.add(detail)

                # 累计统计
                platform_total += platform_spend
                internal_total += internal_spend
                difference_total += spend_difference

            # 更新批次统计信息
            batch.total_accounts = total_accounts
            batch.matched_accounts = matched_count
            batch.mismatched_accounts = mismatched_count
            batch.auto_matched = auto_matched_count
            batch.manual_reviewed = mismatched_count
            batch.total_platform_spend = platform_total
            batch.total_internal_spend = internal_total
            batch.total_difference = difference_total
            batch.status = "completed"
            batch.completed_at = datetime.utcnow()

            self.db.commit()

        except Exception as e:
            batch.status = "exception"
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
        if match_status:
            query = query.filter(ReconciliationDetail.match_status == match_status)

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
            raise NotFoundError("SYS_004", "对账详情不存在")

        if detail.match_status not in ["pending", "manual_review", "exception"]:
            raise ValidationError("BIZ_306", "只能审核待处理或异常的对账详情")

        # 更新审核信息
        detail.reviewed_by = current_user_id
        detail.reviewed_at = datetime.utcnow()
        detail.review_notes = request.review_notes
        detail.auto_confidence = request.auto_confidence or detail.auto_confidence
        detail.difference_type = request.difference_type
        detail.difference_reason = request.difference_reason

        # 更新匹配状态
        if request.action == "approve" and request.is_matched:
            detail.match_status = "matched"
            detail.is_matched = True
        elif request.action == "reject":
            detail.match_status = "exception"
            detail.is_matched = False
        elif request.action == "investigate":
            detail.match_status = "manual_review"

        # 如果指定了最终状态
        if request.match_status:
            detail.match_status = request.match_status

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
            raise NotFoundError("SYS_004", "对账详情不存在")

        # 计算调整后金额
        adjusted_amount = request.original_amount + request.adjustment_amount

        # 创建调整记录
        adjustment = ReconciliationAdjustment(
            detail_id=detail_id,
            batch_id=detail.batch_id,
            adjustment_type=request.adjustment_type,
            original_amount=request.original_amount,
            adjustment_amount=request.adjustment_amount,
            adjusted_amount=adjusted_amount,
            adjustment_reason=request.adjustment_reason,
            detailed_reason=request.detailed_reason,
            evidence_url=request.evidence_url,
            approved_by=current_user_id,
            approved_at=datetime.utcnow()
        )

        self.db.add(adjustment)
        self.db.commit()
        self.db.refresh(adjustment)

        # 更新对账详情状态
        detail.resolved_by = current_user_id
        detail.resolved_at = datetime.utcnow()
        detail.resolution_method = "adjust"
        detail.resolution_notes = f"调整金额: {request.adjustment_amount}"
        detail.match_status = "resolved"

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

        # 应用日期过滤
        if date_from:
            query = query.filter(ReconciliationBatch.reconciliation_date >= date_from)
        if date_to:
            query = query.filter(ReconciliationBatch.reconciliation_date <= date_to)

        # 总体统计
        total_batches = query.count()
        completed_batches = query.filter(
            ReconciliationBatch.status == "completed"
        ).count()
        exception_batches = query.filter(
            ReconciliationBatch.status == "exception"
        ).count()
        resolved_batches = query.filter(
            ReconciliationBatch.status == "resolved"
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
        matched_accounts = details_query.filter(
            ReconciliationDetail.is_matched == True
        ).count()
        mismatched_accounts = total_accounts - matched_accounts

        # 金额统计
        from sqlalchemy import cast, Numeric
        batch_stats = query.with_entities(
            func.sum(cast(ReconciliationBatch.total_platform_spend, Numeric(15, 2))).label('platform_total'),
            func.sum(cast(ReconciliationBatch.total_internal_spend, Numeric(15, 2))).label('internal_total'),
            func.sum(cast(ReconciliationBatch.total_difference, Numeric(15, 2))).label('difference_total')
        ).first()

        total_platform_spend = batch_stats.platform_total or Decimal('0.00')
        total_internal_spend = batch_stats.internal_total or Decimal('0.00')
        total_difference = batch_stats.difference_total or Decimal('0.00')

        # 调整金额统计
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

        total_adjustments = adjustments_query.with_entities(
            func.sum(cast(ReconciliationAdjustment.adjustment_amount, Numeric(15, 2)))
        ).scalar() or Decimal('0.00')

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
        avg_processing_time = self.db.query(
            func.avg(
                func.extract(
                    'epoch',
                    ReconciliationBatch.completed_at - ReconciliationBatch.started_at
                ) / 3600
            )
        ).filter(
            ReconciliationBatch.started_at.isnot(None),
            ReconciliationBatch.completed_at.isnot(None)
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
            query = query.filter(ReconciliationBatch.reconciliation_date >= date_from)
        if date_to:
            query = query.filter(ReconciliationBatch.reconciliation_date <= date_to)

        # 获取数据
        details = query.all()

        # 转换为导出格式
        export_data = []
        for detail in details:
            export_data.append({
                "batch_no": detail.batch.batch_no,
                "reconciliation_date": detail.batch.reconciliation_date.isoformat(),
                "ad_account_name": detail.ad_account.account_name,
                "project_name": detail.project.name,
                "channel_name": detail.channel.name,
                "platform_spend": float(detail.platform_spend),
                "internal_spend": float(detail.internal_spend),
                "spend_difference": float(detail.spend_difference),
                "is_matched": detail.is_matched,
                "match_status": detail.match_status,
                "difference_type": detail.difference_type,
                "difference_reason": detail.difference_reason,
                "created_at": detail.created_at.isoformat()
            })

        return export_data

    async def _update_batch_statistics(self, batch_id: int):
        """更新批次统计信息"""
        batch = self.db.query(ReconciliationBatch).filter(
            ReconciliationBatch.id == batch_id
        ).first()

        if not batch:
            return

        # 重新计算统计信息
        details = self.db.query(ReconciliationDetail).filter(
            ReconciliationDetail.batch_id == batch_id
        ).all()

        batch.total_accounts = len(details)
        batch.matched_accounts = sum(1 for d in details if d.is_matched)
        batch.mismatched_accounts = batch.total_accounts - batch.matched_accounts
        batch.total_platform_spend = sum(d.platform_spend for d in details)
        batch.total_internal_spend = sum(d.internal_spend for d in details)
        batch.total_difference = sum(d.spend_difference for d in details)
        batch.auto_matched = sum(1 for d in details if d.match_status == "auto_matched")
        batch.manual_reviewed = sum(1 for d in details if d.match_status == "manual_review")

        self.db.commit()