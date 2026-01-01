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
from sqlalchemy import and_, or_, func, select, Integer

from backend.models import (
    ReconciliationBatch,
    ReconciliationDetail,
    ReconciliationAdjustment,
    ReconciliationReport,
)
from backend.models import AdAccount
from backend.models import Project
from backend.models import Channel
from backend.models import User
from backend.models.base import (
    ReconciliationBatchStatus,
    ReconciliationDetailStatus,
    UserRole,
)
from backend.schemas.reconciliation import (
    ReconciliationBatchCreateRequest,
    ReconciliationDetailReviewRequest,
    ReconciliationAdjustmentCreateRequest,
    ReconciliationReportGenerateRequest,
    ReconciliationStatisticsResponse,
)
from backend.utils.id_generator import generate_request_no

# Note: Response helpers moved to routers layer
from backend.exceptions.custom_exceptions import (
    ValidationError,
    ResourceNotFoundError,
    PermissionDeniedError,
    BusinessLogicError,
)
from backend.core.state_machine import (
    RECONCILIATION_BATCH_STATE_MACHINE,
    RECONCILIATION_DETAIL_STATE_MACHINE,
    StateTransitionError,
    ReconciliationBatchStatus as SMBatchStatus,
    ReconciliationDetailStatus as SMDetailStatus,
)


def _safe_decimal(value, default: Decimal = Decimal("0.00")) -> Decimal:
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
    if hasattr(value, "_mock_name") or hasattr(value, "_mock_children"):
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

    def _validate_batch_transition(
        self,
        batch: ReconciliationBatch,
        target_status: str,
        user_role: str,
        action_name: str = "状态转换",
    ) -> None:
        """
        验证对账批次状态转换是否合法

        Args:
            batch: 对账批次实体
            target_status: 目标状态
            user_role: 当前用户角色
            action_name: 操作名称（用于错误消息）

        Raises:
            BusinessLogicError: 如果状态转换不允许
        """
        current_status = batch.status

        # 检查是否可以转换
        if not RECONCILIATION_BATCH_STATE_MACHINE.can_transition(
            current_status, target_status
        ):
            allowed = RECONCILIATION_BATCH_STATE_MACHINE.get_allowed_transitions(
                current_status
            )
            raise BusinessLogicError(
                message=f"{action_name}失败: 不能从 {current_status} 转换到 {target_status}。允许的目标状态: {allowed}",
                error_code="STATE_400",
            )

        # 使用状态机执行转换（包含角色验证）
        try:
            RECONCILIATION_BATCH_STATE_MACHINE.transition(
                batch, current_status, target_status, user_role=user_role
            )
        except StateTransitionError as e:
            raise BusinessLogicError(
                message=f"{action_name}失败: {str(e)}", error_code="STATE_401"
            )

    def _validate_detail_transition(
        self,
        detail: ReconciliationDetail,
        target_status: str,
        user_role: str,
        action_name: str = "状态转换",
    ) -> None:
        """
        验证对账明细状态转换是否合法

        Args:
            detail: 对账明细实体
            target_status: 目标状态
            user_role: 当前用户角色
            action_name: 操作名称（用于错误消息）

        Raises:
            BusinessLogicError: 如果状态转换不允许
        """
        current_status = detail.status

        # 检查是否可以转换
        if not RECONCILIATION_DETAIL_STATE_MACHINE.can_transition(
            current_status, target_status
        ):
            allowed = RECONCILIATION_DETAIL_STATE_MACHINE.get_allowed_transitions(
                current_status
            )
            raise BusinessLogicError(
                message=f"{action_name}失败: 不能从 {current_status} 转换到 {target_status}。允许的目标状态: {allowed}",
                error_code="STATE_400",
            )

        # 使用状态机执行转换（包含角色验证）
        try:
            RECONCILIATION_DETAIL_STATE_MACHINE.transition(
                detail, current_status, target_status, user_role=user_role
            )
        except StateTransitionError as e:
            raise BusinessLogicError(
                message=f"{action_name}失败: {str(e)}", error_code="STATE_401"
            )

    async def create_batch(
        self, request: ReconciliationBatchCreateRequest, current_user_id: int
    ) -> ReconciliationBatch:
        """创建对账批次"""
        # 检查是否已存在相同日期的对账
        # 使用 period_end 进行查询（reconciliation_date 是 period_end 的属性别名）
        existing = (
            self.db.query(ReconciliationBatch)
            .filter(ReconciliationBatch.period_end == request.reconciliation_date)
            .first()
        )

        if existing:
            raise BusinessLogicError(message="该日期已存在对账批次", error_code="BIZ_302")

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
        user_role: str = None,
    ) -> Tuple[List[ReconciliationBatch], int]:
        """获取对账批次列表"""
        query = self.db.query(ReconciliationBatch)

        # 根据角色过滤数据
        if user_role in ["account_manager", "pitcher"]:
            # 只能看到自己项目的对账数据
            query = query.join(ReconciliationDetail).join(AdAccount)
            if user_role == "account_manager":
                query = query.join(Project).filter(
                    Project.account_manager_id == current_user_id
                )
            else:  # pitcher
                query = query.filter(AdAccount.owner_id == current_user_id)

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
        batches = (
            query.order_by(ReconciliationBatch.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return batches, total

    async def get_batch_by_id(
        self, batch_id: int, current_user_id: int = None, user_role: str = None
    ) -> ReconciliationBatch:
        """获取对账批次详情"""
        batch = (
            self.db.query(ReconciliationBatch)
            .filter(ReconciliationBatch.id == batch_id)
            .first()
        )

        if not batch:
            raise ResourceNotFoundError(message="对账批次不存在", error_code="SYS_004")

        # 权限检查
        if user_role in ["account_manager", "pitcher"]:
            has_permission = (
                self.db.query(ReconciliationDetail)
                .filter(ReconciliationDetail.batch_id == batch_id)
                .join(AdAccount)
            )

            if user_role == "account_manager":
                has_permission = has_permission.join(Project).filter(
                    Project.account_manager_id == current_user_id
                )
            else:
                has_permission = has_permission.filter(
                    AdAccount.owner_id == current_user_id
                )

            if not has_permission.first():
                raise PermissionDeniedError(message="无权限访问此对账批次", error_code="BIZ_303")

        return batch

    async def run_reconciliation(
        self,
        batch_id: int,
        current_user_id: int,
        supplier_data: Optional[Dict[int, Decimal]] = None,
    ) -> ReconciliationBatch:
        """
        执行对账 - 计算差异并生成调整建议

        RECONCILIATION_SOT.md v1.0 §4.1:
        1. 汇总系统消耗: our_total_spend = SUM(daily_reports.real_spend)
        2. 对比供应商消耗: supplier_total_spend
        3. 计算差异: difference = our_total_spend - supplier_total_spend
        4. 计算差异率: difference_rate = (difference / supplier_total_spend) × 100%

        Args:
            batch_id: 批次ID
            current_user_id: 当前用户ID
            supplier_data: 供应商提供的消耗数据 {ad_account_id: spend_amount}
                          如果为空，则使用 system_spend 作为基准（差异为0）

        Returns:
            ReconciliationBatch: 更新后的批次对象
        """
        from backend.models import DailyReport

        batch = await self.get_batch_by_id(batch_id, current_user_id, "admin")

        # 检查状态 - 只能从 draft 或 pending_review 状态执行对账
        if batch.status not in [
            ReconciliationBatchStatus.DRAFT.value,
            ReconciliationBatchStatus.PENDING_REVIEW.value,
        ]:
            raise BusinessLogicError(message="只能对草稿或待审核的批次执行对账", error_code="BIZ_306")

        # 更新批次状态为 pending_review
        batch.status = ReconciliationBatchStatus.PENDING_REVIEW.value
        self.db.commit()

        try:
            # ====== Step 1: 汇总系统消耗 (RECONCILIATION_SOT.md §2.2) ======
            # 按广告账户汇总 daily_reports.real_spend
            system_spend_query = (
                self.db.query(
                    DailyReport.ad_account_id,
                    func.sum(DailyReport.real_spend).label("total_spend"),
                )
                .filter(
                    DailyReport.report_date >= batch.period_start,
                    DailyReport.report_date <= batch.period_end,
                    DailyReport.status == "final_locked",  # 仅统计已锁定的日报
                )
                .group_by(DailyReport.ad_account_id)
                .all()
            )

            # 转换为字典 {ad_account_id: total_spend}
            system_spend_map = {
                row.ad_account_id: _safe_decimal(row.total_spend)
                for row in system_spend_query
            }

            # ====== Step 2: 获取所有相关广告账户 ======
            ad_account_ids = set(system_spend_map.keys())
            if supplier_data:
                ad_account_ids.update(supplier_data.keys())

            # 获取广告账户信息
            ad_accounts = (
                self.db.query(AdAccount).filter(AdAccount.id.in_(ad_account_ids)).all()
                if ad_account_ids
                else []
            )

            # ====== Step 3: 计算差异并创建明细 ======
            our_total = Decimal("0.00")
            supplier_total = Decimal("0.00")
            difference_total = Decimal("0.00")

            for account in ad_accounts:
                # 系统记录的消耗 (our_total_spend)
                system_spend = system_spend_map.get(account.id, Decimal("0.00"))

                # 供应商提供的消耗 (supplier_total_spend)
                # 如果没有供应商数据，假设与系统一致（差异为0）
                external_spend = Decimal("0.00")
                if supplier_data and account.id in supplier_data:
                    external_spend = _safe_decimal(supplier_data[account.id])
                else:
                    external_spend = system_spend  # 默认无差异

                # ====== Step 4: 计算差异 (RECONCILIATION_SOT.md §2.2) ======
                # difference = our_total_spend - supplier_total_spend
                # 正差 = 我方多记 | 负差 = 我方少记
                spend_difference = system_spend - external_spend

                # 差异率 = (difference / supplier_total_spend) × 100%
                difference_rate = Decimal("0.0000")
                if external_spend > 0:
                    difference_rate = (spend_difference / external_spend) * 100

                # ====== Step 5: 判断是否匹配（容忍 0.01 的误差）======
                is_matched = abs(spend_difference) < Decimal("0.01")

                # ====== Step 6: 生成调整建议 ======
                adjustment_suggestion = None
                if not is_matched:
                    if spend_difference > Decimal("10.00"):
                        # 我方多记，需减少
                        adjustment_suggestion = f"decrease:{spend_difference}"
                    elif spend_difference < Decimal("-10.00"):
                        # 我方少记，需增加
                        adjustment_suggestion = f"increase:{abs(spend_difference)}"
                    else:
                        # 差异较小，可核销
                        adjustment_suggestion = f"writeoff:{abs(spend_difference)}"

                # ====== Step 7: 创建对账明细 ======
                detail_notes = f"差异率: {difference_rate:.2f}%"
                if adjustment_suggestion:
                    detail_notes += f" | 建议: {adjustment_suggestion}"

                detail = ReconciliationDetail(
                    batch_id=batch_id,
                    ad_account_id=account.id,
                    system_spend=system_spend,
                    actual_spend=external_spend,
                    discrepancy=spend_difference,
                    status=ReconciliationDetailStatus.CONFIRMED.value
                    if is_matched
                    else ReconciliationDetailStatus.PENDING.value,
                    notes=detail_notes,
                )
                self.db.add(detail)

                # 累计统计
                our_total += system_spend
                supplier_total += external_spend
                difference_total += spend_difference

            # ====== Step 8: 更新批次汇总 ======
            batch.total_system_spend = our_total
            batch.total_actual_spend = supplier_total
            batch.discrepancy = difference_total

            # 计算批次差异率
            if supplier_total > 0:
                batch_difference_rate = (difference_total / supplier_total) * 100
            else:
                batch_difference_rate = Decimal("0.0000")

            # 如果所有明细都匹配，状态为 approved；否则需要调整
            pending_count = sum(
                1
                for a in ad_accounts
                if abs(
                    system_spend_map.get(a.id, Decimal("0.00"))
                    - (
                        supplier_data.get(
                            a.id, system_spend_map.get(a.id, Decimal("0.00"))
                        )
                        if supplier_data
                        else system_spend_map.get(a.id, Decimal("0.00"))
                    )
                )
                >= Decimal("0.01")
            )

            if pending_count == 0:
                batch.status = ReconciliationBatchStatus.APPROVED.value
            else:
                batch.status = ReconciliationBatchStatus.PENDING_REVIEW.value

            self.db.commit()

        except Exception as e:
            batch.status = ReconciliationBatchStatus.NEEDS_ADJUSTMENT.value
            self.db.commit()
            raise e

        return batch

    async def calculate_difference(
        self, batch_id: int, ad_account_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        计算对账差异（RECONCILIATION_SOT.md v1.0 §4）

        差异计算公式:
        - difference = our_total_spend - supplier_total_spend
        - difference_rate = (difference / supplier_total_spend) × 100%

        差异类型判定:
        - 正差（我方多记）: difference > 0 → 建议 decrease
        - 负差（我方少记）: difference < 0 → 建议 increase
        - 零差: |difference| < 0.01 → 自动确认

        Args:
            batch_id: 批次ID
            ad_account_id: 可选，指定账户ID（用于单账户差异分析）

        Returns:
            Dict: 差异计算结果
        """
        query = self.db.query(ReconciliationDetail).filter(
            ReconciliationDetail.batch_id == batch_id
        )

        if ad_account_id:
            query = query.filter(ReconciliationDetail.ad_account_id == ad_account_id)

        details = query.all()

        if not details:
            return {
                "batch_id": batch_id,
                "total_system_spend": Decimal("0.00"),
                "total_supplier_spend": Decimal("0.00"),
                "total_difference": Decimal("0.00"),
                "difference_rate": Decimal("0.0000"),
                "matched_count": 0,
                "pending_count": 0,
                "adjustment_suggestions": [],
            }

        # 汇总统计
        total_system = sum(_safe_decimal(d.system_spend) for d in details)
        total_supplier = sum(_safe_decimal(d.actual_spend) for d in details)
        total_diff = sum(_safe_decimal(d.discrepancy) for d in details)

        # 差异率
        diff_rate = Decimal("0.0000")
        if total_supplier > 0:
            diff_rate = (total_diff / total_supplier) * 100

        # 状态统计
        matched_count = sum(
            1 for d in details if d.status == ReconciliationDetailStatus.CONFIRMED.value
        )
        pending_count = sum(
            1 for d in details if d.status == ReconciliationDetailStatus.PENDING.value
        )

        # 生成调整建议
        suggestions = []
        for d in details:
            if d.status != ReconciliationDetailStatus.PENDING.value:
                continue

            diff_amount = _safe_decimal(d.discrepancy)
            if abs(diff_amount) < Decimal("0.01"):
                continue

            suggestion = {
                "detail_id": d.id,
                "ad_account_id": d.ad_account_id,
                "difference": diff_amount,
                "adjustment_type": None,
                "reason": None,
            }

            if diff_amount > Decimal("10.00"):
                suggestion["adjustment_type"] = "decrease"
                suggestion["reason"] = f"系统多记 {diff_amount}，建议红冲减少"
            elif diff_amount < Decimal("-10.00"):
                suggestion["adjustment_type"] = "increase"
                suggestion["reason"] = f"系统少记 {abs(diff_amount)}，建议补录增加"
            else:
                suggestion["adjustment_type"] = "writeoff"
                suggestion["reason"] = f"差异金额较小 ({diff_amount})，建议核销"

            suggestions.append(suggestion)

        return {
            "batch_id": batch_id,
            "total_system_spend": total_system,
            "total_supplier_spend": total_supplier,
            "total_difference": total_diff,
            "difference_rate": round(diff_rate, 4),
            "matched_count": matched_count,
            "pending_count": pending_count,
            "adjustment_suggestions": suggestions,
        }

    async def get_batch_details(
        self,
        batch_id: int,
        page: int = 1,
        page_size: int = 20,
        match_status: Optional[str] = None,
        current_user_id: int = None,
        user_role: str = None,
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
        details = (
            query.order_by(ReconciliationDetail.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return details, total

    async def review_detail(
        self,
        detail_id: int,
        request: ReconciliationDetailReviewRequest,
        current_user_id: int,
    ) -> ReconciliationDetail:
        """审核对账差异"""
        detail = (
            self.db.query(ReconciliationDetail)
            .filter(ReconciliationDetail.id == detail_id)
            .first()
        )

        if not detail:
            raise ResourceNotFoundError(message="对账详情不存在", error_code="SYS_004")

        # 对账详情状态检查 - pending, confirmed, adjusted 可审核
        # 注意：使用 status 字段，而不是 match_status
        if detail.status not in [
            ReconciliationDetailStatus.PENDING.value,
            ReconciliationDetailStatus.CONFIRMED.value,
            ReconciliationDetailStatus.ADJUSTED.value,
        ]:
            raise BusinessLogicError(message="只能审核待处理或异常的对账详情", error_code="BIZ_306")

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
        current_user_id: int,
    ) -> ReconciliationAdjustment:
        """创建调整记录"""
        detail = (
            self.db.query(ReconciliationDetail)
            .filter(ReconciliationDetail.id == detail_id)
            .first()
        )

        if not detail:
            raise ResourceNotFoundError(message="对账详情不存在", error_code="SYS_004")

        # 创建调整记录 - 使用 SoT DATA_SCHEMA.md v5.2 定义的字段
        # 字段：detail_id, adjustment_type, amount, reason, created_by
        adjustment = ReconciliationAdjustment(
            detail_id=detail_id,
            adjustment_type=request.adjustment_type,
            amount=request.adjustment_amount,
            reason=request.detailed_reason or request.adjustment_reason,
            created_by=current_user_id,
        )

        self.db.add(adjustment)
        self.db.commit()
        self.db.refresh(adjustment)

        # 更新对账详情状态为已调整
        detail.status = ReconciliationDetailStatus.ADJUSTED.value
        detail.notes = (
            f"调整金额: {request.adjustment_amount}, 原因: {request.adjustment_reason}"
        )

        self.db.commit()

        # 更新批次统计
        await self._update_batch_statistics(detail.batch_id)

        return adjustment

    async def get_statistics(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        current_user_id: int = None,
        user_role: str = None,
    ) -> ReconciliationStatisticsResponse:
        """获取对账统计信息"""
        query = self.db.query(ReconciliationBatch)

        # 根据角色过滤数据
        if user_role in ["account_manager", "pitcher"]:
            query = query.join(ReconciliationDetail).join(AdAccount)
            if user_role == "account_manager":
                query = query.join(Project).filter(
                    Project.account_manager_id == current_user_id
                )
            else:  # pitcher
                query = query.filter(AdAccount.owner_id == current_user_id)

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
            ReconciliationBatch.status
            == ReconciliationBatchStatus.NEEDS_ADJUSTMENT.value
        ).count()
        resolved_batches = query.filter(
            ReconciliationBatch.status == ReconciliationBatchStatus.APPROVED.value
        ).count()

        # 账户统计
        details_query = self.db.query(ReconciliationDetail).join(ReconciliationBatch)
        if user_role in ["account_manager", "pitcher"]:
            details_query = details_query.join(AdAccount)
            if user_role == "account_manager":
                details_query = details_query.join(Project).filter(
                    Project.account_manager_id == current_user_id
                )
            else:
                details_query = details_query.filter(
                    AdAccount.owner_id == current_user_id
                )

        total_accounts = details_query.count()
        # 注意：ReconciliationDetail 模型没有 is_matched 字段
        # 使用 discrepancy 接近 0 来判断是否匹配（容忍 0.01 的误差）
        matched_accounts = details_query.filter(
            func.abs(ReconciliationDetail.discrepancy) < Decimal("0.01")
        ).count()
        mismatched_accounts = total_accounts - matched_accounts

        # 金额统计
        from sqlalchemy import cast, Numeric

        batch_stats = query.with_entities(
            func.sum(
                cast(ReconciliationBatch.total_system_spend, Numeric(15, 2))
            ).label("platform_total"),
            func.sum(
                cast(ReconciliationBatch.total_actual_spend, Numeric(15, 2))
            ).label("internal_total"),
            func.sum(cast(ReconciliationBatch.discrepancy, Numeric(15, 2))).label(
                "difference_total"
            ),
        ).first()

        # 安全处理空值和类型转换，防止 MagicMock 静默通过
        if batch_stats is None:
            total_platform_spend = Decimal("0.00")
            total_internal_spend = Decimal("0.00")
            total_difference = Decimal("0.00")
        else:
            total_platform_spend = _safe_decimal(
                getattr(batch_stats, "platform_total", None), Decimal("0.00")
            )
            total_internal_spend = _safe_decimal(
                getattr(batch_stats, "internal_total", None), Decimal("0.00")
            )
            total_difference = _safe_decimal(
                getattr(batch_stats, "difference_total", None), Decimal("0.00")
            )

        # 调整金额统计
        # 注意：如果 ReconciliationAdjustment 不存在，返回 0
        if ReconciliationAdjustment is None:
            total_adjustments = Decimal("0.00")
        else:
            adjustments_query = self.db.query(ReconciliationAdjustment)
            if user_role in ["account_manager", "pitcher"]:
                adjustments_query = adjustments_query.join(ReconciliationDetail).join(
                    ReconciliationBatch
                )
                if user_role == "account_manager":
                    adjustments_query = (
                        adjustments_query.join(AdAccount)
                        .join(Project)
                        .filter(Project.account_manager_id == current_user_id)
                    )
                else:
                    adjustments_query = adjustments_query.join(AdAccount).filter(
                        AdAccount.owner_id == current_user_id
                    )

            adjustments_scalar = adjustments_query.with_entities(
                func.sum(cast(ReconciliationAdjustment.amount, Numeric(15, 2)))
            ).scalar()
            total_adjustments = _safe_decimal(adjustments_scalar, Decimal("0.00"))

        # 效率统计
        if total_accounts > 0:
            auto_match_rate = (matched_accounts / total_accounts) * 100
            manual_review_rate = (mismatched_accounts / total_accounts) * 100
            difference_rate = (
                (total_difference / total_platform_spend * 100)
                if total_platform_spend > 0
                else 0
            )
        else:
            auto_match_rate = 0
            manual_review_rate = 0
            difference_rate = 0

        resolution_rate = (
            (resolved_batches / total_batches * 100) if total_batches > 0 else 0
        )

        # 平均处理时间（小时）
        # 注意：ReconciliationBatch 使用 created_at 和 closed_at，而不是 started_at 和 completed_at
        avg_processing_time = (
            self.db.query(
                func.avg(
                    func.extract(
                        "epoch",
                        ReconciliationBatch.closed_at - ReconciliationBatch.created_at,
                    )
                    / 3600
                )
            )
            .filter(
                ReconciliationBatch.created_at.isnot(None),
                ReconciliationBatch.closed_at.isnot(None),
            )
            .scalar()
            or 0
        )

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
            top_mismatched_accounts=top_mismatched_accounts,
        )

    async def export_reconciliation_data(
        self,
        batch_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        format_type: str = "excel",
        current_user_id: int = None,
        user_role: str = None,
    ) -> List[Dict[str, Any]]:
        """导出对账数据"""
        query = self.db.query(ReconciliationDetail).join(ReconciliationBatch)

        # 根据角色过滤
        if user_role in ["account_manager", "pitcher"]:
            query = query.join(AdAccount)
            if user_role == "account_manager":
                query = query.join(Project).filter(
                    Project.account_manager_id == current_user_id
                )
            else:
                query = query.filter(AdAccount.owner_id == current_user_id)

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
            export_data.append(
                {
                    "batch_no": detail.batch.batch_no,
                    "reconciliation_date": detail.batch.reconciliation_date.isoformat(),
                    "ad_account_name": detail.ad_account.account_name,
                    "project_name": detail.ad_account.project.name
                    if detail.ad_account.project
                    else None,
                    "channel_name": detail.ad_account.channel.name
                    if detail.ad_account.channel
                    else None,
                    "platform_spend": float(detail.system_spend),
                    "internal_spend": float(detail.actual_spend),
                    "spend_difference": float(detail.discrepancy),
                    "is_matched": abs(detail.discrepancy)
                    < Decimal("0.01"),  # 基于 discrepancy 计算
                    "match_status": detail.status,  # 使用 status 字段
                    "difference_type": None,  # 模型中没有此字段
                    "difference_reason": detail.notes,  # 使用 notes 字段
                    "created_at": detail.created_at.isoformat(),
                }
            )

        return export_data

    async def _update_batch_statistics(self, batch_id: int):
        """更新批次统计信息

        注意：根据 SoT spec，统计字段如 total_accounts, matched_accounts 等
        应从 ReconciliationDetail 记录按需计算，不存储在数据库中。
        仅更新批次的汇总金额字段：total_system_spend, total_actual_spend, discrepancy
        """
        batch = (
            self.db.query(ReconciliationBatch)
            .filter(ReconciliationBatch.id == batch_id)
            .first()
        )

        if not batch:
            return

        # 重新计算汇总金额
        details = (
            self.db.query(ReconciliationDetail)
            .filter(ReconciliationDetail.batch_id == batch_id)
            .all()
        )

        # 仅更新模型中存在的汇总金额字段
        batch.total_system_spend = (
            sum(d.system_spend for d in details) if details else Decimal("0.00")
        )
        batch.total_actual_spend = (
            sum(d.actual_spend for d in details) if details else Decimal("0.00")
        )
        batch.discrepancy = (
            sum(d.discrepancy for d in details) if details else Decimal("0.00")
        )

        self.db.commit()

    # ========== 批次状态转换方法 (STATE_MACHINE.md v2.6 第11章) ==========

    async def submit_batch(
        self, batch_id: int, current_user_id: int, user_role: str = "finance"
    ) -> ReconciliationBatch:
        """
        提交批次审核
        状态转换: draft → pending_review
        允许角色: finance, project_owner
        """
        batch = await self.get_batch_by_id(batch_id, current_user_id, user_role)

        # 验证批次有明细
        detail_count = (
            self.db.query(ReconciliationDetail)
            .filter(ReconciliationDetail.batch_id == batch_id)
            .count()
        )

        if detail_count == 0:
            raise BusinessLogicError(message="批次没有对账明细，无法提交审核", error_code="RECON_001")

        # 使用统一状态机验证并执行转换
        self._validate_batch_transition(
            batch, ReconciliationBatchStatus.PENDING_REVIEW.value, user_role, "提交审核"
        )
        batch.version += 1
        self.db.commit()
        self.db.refresh(batch)

        return batch

    async def approve_batch(
        self, batch_id: int, current_user_id: int, user_role: str = "finance"
    ) -> ReconciliationBatch:
        """
        批准对账批次
        状态转换: pending_review → approved
        允许角色: finance, admin
        """
        batch = await self.get_batch_by_id(batch_id, current_user_id, user_role)

        # 使用统一状态机验证并执行转换
        self._validate_batch_transition(
            batch, ReconciliationBatchStatus.APPROVED.value, user_role, "批准对账"
        )
        batch.reviewed_by = current_user_id
        batch.version += 1
        self.db.commit()
        self.db.refresh(batch)

        return batch

    async def request_adjustment(
        self,
        batch_id: int,
        current_user_id: int,
        reason: str,
        user_role: str = "finance",
    ) -> ReconciliationBatch:
        """
        请求调整（审核不通过）
        状态转换: pending_review → needs_adjustment
        允许角色: finance, admin
        """
        batch = await self.get_batch_by_id(batch_id, current_user_id, user_role)

        # 使用统一状态机验证并执行转换
        self._validate_batch_transition(
            batch, ReconciliationBatchStatus.NEEDS_ADJUSTMENT.value, user_role, "请求调整"
        )
        batch.reviewed_by = current_user_id
        batch.version += 1
        self.db.commit()
        self.db.refresh(batch)

        return batch

    async def resubmit_batch(
        self, batch_id: int, current_user_id: int, user_role: str = "finance"
    ) -> ReconciliationBatch:
        """
        重新提交批次（调整后）
        状态转换: needs_adjustment → pending_review
        允许角色: finance, project_owner
        """
        batch = await self.get_batch_by_id(batch_id, current_user_id, user_role)

        # 使用统一状态机验证并执行转换
        self._validate_batch_transition(
            batch, ReconciliationBatchStatus.PENDING_REVIEW.value, user_role, "重新提交"
        )
        batch.version += 1
        self.db.commit()
        self.db.refresh(batch)

        return batch

    async def complete_batch(
        self, batch_id: int, current_user_id: int, user_role: str = "finance"
    ) -> ReconciliationBatch:
        """
        完成对账批次（终态）
        状态转换: approved → completed
        允许角色: finance, admin

        完成条件 (STATE_MACHINE.md v2.6 第14.4节):
        1. 所有明细状态均为 confirmed 或 adjusted
        2. 存在对应的 reconciliation_report 记录
        3. adjusted 状态的明细都有对应的 adjustments 记录
        """
        batch = await self.get_batch_by_id(batch_id, current_user_id, user_role)

        # 验证完成条件1: 所有明细已处理
        pending_details = (
            self.db.query(ReconciliationDetail)
            .filter(
                ReconciliationDetail.batch_id == batch_id,
                ReconciliationDetail.status == ReconciliationDetailStatus.PENDING.value,
            )
            .count()
        )

        if pending_details > 0:
            raise BusinessLogicError(
                message=f"还有 {pending_details} 条明细未处理，无法完成", error_code="RECON_001"
            )

        # 验证完成条件2: 报告已生成
        # 尝试导入 ReconciliationReport
        try:
            from backend.models.finance.reconciliation import ReconciliationReport

            report_exists = (
                self.db.query(ReconciliationReport)
                .filter(ReconciliationReport.batch_id == batch_id)
                .first()
            )

            if not report_exists:
                raise BusinessLogicError(message="对账报告未生成，无法完成", error_code="RECON_002")
        except ImportError:
            # ReconciliationReport 不存在，跳过此验证
            pass

        # 验证完成条件3: adjusted 明细有调整记录
        adjusted_details = (
            self.db.query(ReconciliationDetail)
            .filter(
                ReconciliationDetail.batch_id == batch_id,
                ReconciliationDetail.status
                == ReconciliationDetailStatus.ADJUSTED.value,
            )
            .all()
        )

        for detail in adjusted_details:
            adjustment_exists = (
                self.db.query(ReconciliationAdjustment)
                .filter(ReconciliationAdjustment.detail_id == detail.id)
                .first()
            )

            if not adjustment_exists:
                raise BusinessLogicError(
                    message=f"明细 {detail.id} 标记为已调整但没有调整记录", error_code="RECON_003"
                )

        # 使用统一状态机验证并执行转换
        self._validate_batch_transition(
            batch, ReconciliationBatchStatus.COMPLETED.value, user_role, "完成对账"
        )
        batch.reviewed_by = current_user_id
        batch.closed_at = func.now()
        batch.version += 1
        self.db.commit()
        self.db.refresh(batch)

        return batch

    async def force_complete_batch(
        self, batch_id: int, current_user_id: int, reason: str, user_role: str = "admin"
    ) -> ReconciliationBatch:
        """
        强制完成对账批次（管理员专用）
        状态转换: any (非completed) → completed
        允许角色: admin only
        注意: 此方法绕过状态机，仅限管理员使用
        """
        batch = await self.get_batch_by_id(batch_id, current_user_id, user_role)

        if batch.status == ReconciliationBatchStatus.COMPLETED.value:
            raise BusinessLogicError(message="批次已完成，无需强制完成", error_code="STATE_402")

        # 强制完成，跳过状态机验证（管理员特权）
        # 注意: 这是特殊情况，不使用 _validate_batch_transition
        batch.status = ReconciliationBatchStatus.COMPLETED.value
        batch.reviewed_by = current_user_id
        batch.closed_at = func.now()
        batch.version += 1
        self.db.commit()
        self.db.refresh(batch)

        return batch

    # ========== 明细状态转换方法 ==========

    async def confirm_detail(
        self, detail_id: int, current_user_id: int, user_role: str = "finance"
    ) -> ReconciliationDetail:
        """
        确认对账明细
        状态转换: pending → confirmed
        允许角色: finance, project_owner
        """
        detail = (
            self.db.query(ReconciliationDetail)
            .filter(ReconciliationDetail.id == detail_id)
            .first()
        )

        if not detail:
            raise ResourceNotFoundError(message="对账明细不存在", error_code="SYS_004")

        # 使用统一状态机验证并执行转换
        self._validate_detail_transition(
            detail, ReconciliationDetailStatus.CONFIRMED.value, user_role, "确认明细"
        )
        detail.notes = f"确认人: {current_user_id}, 时间: {datetime.utcnow().isoformat()}"
        detail.version += 1
        self.db.commit()
        self.db.refresh(detail)

        # 更新批次统计
        await self._update_batch_statistics(detail.batch_id)

        return detail

    async def adjust_detail(
        self,
        detail_id: int,
        current_user_id: int,
        adjustment_type: str,
        amount: Decimal,
        reason: str,
        user_role: str = "finance",
    ) -> Tuple[ReconciliationDetail, ReconciliationAdjustment]:
        """
        调整对账明细
        状态转换: pending → adjusted
        允许角色: finance, project_owner

        同时创建调整记录和（可选）账本记录
        """
        detail = (
            self.db.query(ReconciliationDetail)
            .filter(ReconciliationDetail.id == detail_id)
            .first()
        )

        if not detail:
            raise ResourceNotFoundError(message="对账明细不存在", error_code="SYS_004")

        # 使用统一状态机验证并执行转换
        self._validate_detail_transition(
            detail, ReconciliationDetailStatus.ADJUSTED.value, user_role, "调整明细"
        )

        # 创建调整记录
        adjustment = ReconciliationAdjustment(
            detail_id=detail_id,
            adjustment_type=adjustment_type,
            amount=amount,
            reason=reason,
            created_by=current_user_id,
        )
        self.db.add(adjustment)

        # 更新明细备注
        detail.notes = f"调整金额: {amount}, 原因: {reason}"
        detail.version += 1

        self.db.commit()
        self.db.refresh(detail)
        self.db.refresh(adjustment)

        # 更新批次统计
        await self._update_batch_statistics(detail.batch_id)

        return detail, adjustment

    # ========== 报告生成方法 ==========

    async def generate_report(
        self, request: ReconciliationReportGenerateRequest, current_user_id: int
    ):
        """
        生成对账报告

        Args:
            request: 报告生成请求
            current_user_id: 当前用户ID

        Returns:
            ReconciliationReport: 生成的报告对象
        """
        import json

        # 尝试导入 ReconciliationReport
        try:
            from backend.models.finance.reconciliation import ReconciliationReport
        except ImportError:
            raise BusinessLogicError(
                message="ReconciliationReport 模型不可用", error_code="SYS_001"
            )

        # 收集数据
        query = self.db.query(ReconciliationBatch)

        if request.batch_id:
            query = query.filter(ReconciliationBatch.id == request.batch_id)
        else:
            query = query.filter(
                ReconciliationBatch.period_end >= request.report_period_start,
                ReconciliationBatch.period_end <= request.report_period_end,
            )

        batches = query.all()

        if not batches:
            raise ResourceNotFoundError(message="没有找到符合条件的对账批次", error_code="SYS_004")

        # 计算报告指标
        total_batches = len(batches)
        completed_batches = sum(
            1 for b in batches if b.status == ReconciliationBatchStatus.COMPLETED.value
        )
        total_system_spend = sum(_safe_decimal(b.total_system_spend) for b in batches)
        total_actual_spend = sum(_safe_decimal(b.total_actual_spend) for b in batches)
        total_discrepancy = sum(_safe_decimal(b.discrepancy) for b in batches)

        # 统计明细
        detail_stats = (
            self.db.query(
                func.count(ReconciliationDetail.id).label("total"),
                func.sum(
                    func.cast(
                        ReconciliationDetail.status
                        == ReconciliationDetailStatus.CONFIRMED.value,
                        Integer,
                    )
                ).label("confirmed"),
                func.sum(
                    func.cast(
                        ReconciliationDetail.status
                        == ReconciliationDetailStatus.ADJUSTED.value,
                        Integer,
                    )
                ).label("adjusted"),
            )
            .filter(ReconciliationDetail.batch_id.in_([b.id for b in batches]))
            .first()
        )

        metrics = {
            "total_batches": total_batches,
            "completed_batches": completed_batches,
            "total_system_spend": str(total_system_spend),
            "total_actual_spend": str(total_actual_spend),
            "total_discrepancy": str(total_discrepancy),
            "total_details": detail_stats.total or 0,
            "confirmed_details": detail_stats.confirmed or 0,
            "adjusted_details": detail_stats.adjusted or 0,
            "match_rate": round(
                (detail_stats.confirmed or 0) / (detail_stats.total or 1) * 100, 2
            ),
            "generated_at": datetime.utcnow().isoformat(),
        }

        # 创建报告记录
        report = ReconciliationReport(
            batch_id=request.batch_id or batches[0].id,
            report_type=request.report_type,
            period_start=request.report_period_start,
            period_end=request.report_period_end,
            metrics=json.dumps(metrics, ensure_ascii=False),
            generated_by=current_user_id,
        )

        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        return report

    # ========== 账本集成方法 (LEDGER_SOT.md v1.1) ==========

    async def create_ledger_entry_for_adjustment(
        self,
        adjustment: ReconciliationAdjustment,
        project_id: int,
        current_user_id: int,
    ):
        """
        为对账调整创建账本记录

        根据 LEDGER_SOT.md v1.1 第11章，对账调整需要生成相应的账本分录

        Args:
            adjustment: 对账调整记录
            project_id: 项目ID
            current_user_id: 当前用户ID

        Returns:
            LedgerEntry: 创建的账本记录
        """
        from backend.models import LedgerEntry, LedgerEntryType

        # 根据调整类型确定账本分录类型
        if adjustment.adjustment_type == "increase":
            entry_type = LedgerEntryType.TOPUP.value
            amount = adjustment.amount
        elif adjustment.adjustment_type == "decrease":
            entry_type = LedgerEntryType.REVERSAL.value
            amount = -adjustment.amount
        else:  # writeoff
            entry_type = LedgerEntryType.REVERSAL.value
            amount = -adjustment.amount

        # 创建账本记录
        ledger_entry = LedgerEntry(
            ledger_type="PROJECT",
            project_id=project_id,
            entry_type=entry_type,
            amount=amount,
            reference_type="reconciliation_adjustment",
            reference_id=adjustment.id,
            notes=f"对账调整: {adjustment.reason}",
            created_by=current_user_id,
        )

        self.db.add(ledger_entry)
        self.db.commit()
        self.db.refresh(ledger_entry)

        return ledger_entry

    # ========== 批次 CRUD 扩展方法 ==========

    async def update_batch(
        self,
        batch_id: int,
        request: ReconciliationBatchCreateRequest,
        current_user_id: int,
        user_role: str,
    ) -> ReconciliationBatch:
        """
        更新对账批次（仅 draft 状态可更新）

        Args:
            batch_id: 批次ID
            request: 更新请求
            current_user_id: 当前用户ID
            user_role: 用户角色

        Returns:
            ReconciliationBatch: 更新后的批次
        """
        batch = await self.get_batch_by_id(batch_id, current_user_id, user_role)

        if batch.status != ReconciliationBatchStatus.DRAFT.value:
            raise BusinessLogicError(
                message=f"只能更新草稿状态的批次，当前状态: {batch.status}", error_code="STATE_400"
            )

        # 检查日期是否冲突（排除当前批次）
        existing = (
            self.db.query(ReconciliationBatch)
            .filter(
                ReconciliationBatch.period_end == request.reconciliation_date,
                ReconciliationBatch.id != batch_id,
            )
            .first()
        )

        if existing:
            raise BusinessLogicError(message="该日期已存在其他对账批次", error_code="BIZ_302")

        # 更新字段
        batch.period_start = request.reconciliation_date
        batch.period_end = request.reconciliation_date
        batch.version += 1

        self.db.commit()
        self.db.refresh(batch)

        return batch

    async def delete_batch(self, batch_id: int, current_user_id: int) -> bool:
        """
        删除对账批次（仅 draft 状态，admin 角色）

        Args:
            batch_id: 批次ID
            current_user_id: 当前用户ID

        Returns:
            bool: 删除是否成功
        """
        batch = await self.get_batch_by_id(batch_id, current_user_id, "admin")

        if batch.status != ReconciliationBatchStatus.DRAFT.value:
            raise BusinessLogicError(
                message=f"只能删除草稿状态的批次，当前状态: {batch.status}", error_code="STATE_400"
            )

        # 删除关联的明细
        self.db.query(ReconciliationDetail).filter(
            ReconciliationDetail.batch_id == batch_id
        ).delete()

        # 删除批次
        self.db.delete(batch)
        self.db.commit()

        return True

    # ========== 明细扩展方法 ==========

    async def get_detail_by_id(
        self, detail_id: int, current_user_id: int = None, user_role: str = None
    ) -> ReconciliationDetail:
        """
        获取单个对账明细

        Args:
            detail_id: 明细ID
            current_user_id: 当前用户ID
            user_role: 用户角色

        Returns:
            ReconciliationDetail: 对账明细
        """
        detail = (
            self.db.query(ReconciliationDetail)
            .filter(ReconciliationDetail.id == detail_id)
            .first()
        )

        if not detail:
            raise ResourceNotFoundError(message="对账明细不存在", error_code="SYS_004")

        # 权限检查（通过批次）
        if user_role in ["account_manager", "pitcher"]:
            await self.get_batch_by_id(detail.batch_id, current_user_id, user_role)

        return detail

    # ========== 调整记录方法 ==========

    async def get_adjustments(
        self,
        page: int = 1,
        page_size: int = 20,
        batch_id: Optional[int] = None,
        detail_id: Optional[int] = None,
        adjustment_type: Optional[str] = None,
    ) -> Tuple[List[ReconciliationAdjustment], int]:
        """
        获取调整记录列表

        Args:
            page: 页码
            page_size: 每页条数
            batch_id: 批次ID过滤
            detail_id: 明细ID过滤
            adjustment_type: 调整类型过滤

        Returns:
            Tuple[List[ReconciliationAdjustment], int]: (调整记录列表, 总数)
        """
        query = self.db.query(ReconciliationAdjustment)

        # 按批次过滤
        if batch_id:
            query = query.join(ReconciliationDetail).filter(
                ReconciliationDetail.batch_id == batch_id
            )

        # 按明细过滤
        if detail_id:
            query = query.filter(ReconciliationAdjustment.detail_id == detail_id)

        # 按类型过滤
        if adjustment_type:
            query = query.filter(
                ReconciliationAdjustment.adjustment_type == adjustment_type
            )

        # 计算总数
        total = query.count()

        # 分页
        adjustments = (
            query.order_by(ReconciliationAdjustment.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return adjustments, total

    async def get_adjustment_by_id(
        self, adjustment_id: int
    ) -> ReconciliationAdjustment:
        """
        获取单个调整记录

        Args:
            adjustment_id: 调整记录ID

        Returns:
            ReconciliationAdjustment: 调整记录
        """
        adjustment = (
            self.db.query(ReconciliationAdjustment)
            .filter(ReconciliationAdjustment.id == adjustment_id)
            .first()
        )

        if not adjustment:
            raise ResourceNotFoundError(message="调整记录不存在", error_code="SYS_004")

        return adjustment

    async def execute_adjustment(
        self, adjustment_id: int, current_user_id: int
    ) -> ReconciliationAdjustment:
        """
        执行调整记录（触发账本分录）

        Args:
            adjustment_id: 调整记录ID
            current_user_id: 当前用户ID

        Returns:
            ReconciliationAdjustment: 更新后的调整记录
        """
        adjustment = await self.get_adjustment_by_id(adjustment_id)

        # 检查是否已执行
        if hasattr(adjustment, "executed") and adjustment.executed:
            raise BusinessLogicError(message="调整记录已执行", error_code="BIZ_003")

        # 获取明细和批次信息
        detail = (
            self.db.query(ReconciliationDetail)
            .filter(ReconciliationDetail.id == adjustment.detail_id)
            .first()
        )

        if not detail:
            raise ResourceNotFoundError(message="关联的对账明细不存在", error_code="SYS_004")

        # 获取广告账户的项目ID
        ad_account = (
            self.db.query(AdAccount)
            .filter(AdAccount.id == detail.ad_account_id)
            .first()
        )

        if not ad_account or not ad_account.project_id:
            raise BusinessLogicError(message="无法确定调整记录关联的项目", error_code="BIZ_003")

        # 创建账本分录
        await self.create_ledger_entry_for_adjustment(
            adjustment=adjustment,
            project_id=ad_account.project_id,
            current_user_id=current_user_id,
        )

        # 标记为已执行（如果模型有此字段）
        if hasattr(adjustment, "executed"):
            adjustment.executed = True
            self.db.commit()
            self.db.refresh(adjustment)

        return adjustment

    # ========== 报告方法 ==========

    async def get_report_by_id(self, report_id: int):
        """
        获取单个对账报告

        Args:
            report_id: 报告ID

        Returns:
            ReconciliationReport: 对账报告
        """
        try:
            from backend.models.finance.reconciliation import ReconciliationReport
        except ImportError:
            raise BusinessLogicError(
                message="ReconciliationReport 模型不可用", error_code="SYS_001"
            )

        report = (
            self.db.query(ReconciliationReport)
            .filter(ReconciliationReport.id == report_id)
            .first()
        )

        if not report:
            raise ResourceNotFoundError(message="对账报告不存在", error_code="SYS_004")

        return report

    async def delete_report(self, report_id: int) -> bool:
        """
        删除对账报告（admin 角色）

        Args:
            report_id: 报告ID

        Returns:
            bool: 删除是否成功
        """
        report = await self.get_report_by_id(report_id)

        self.db.delete(report)
        self.db.commit()

        return True
