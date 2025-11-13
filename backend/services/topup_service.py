"""
充值管理服务层
Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, func, desc, extract

from models.topup import TopupRequest, TopupTransaction, TopupApprovalLog
from models.user import User
from models.ad_account import AdAccount
from models.project import Project
from schemas.topup import (
    TopupRequestCreate,
    TopupDataReviewRequest,
    TopupFinanceApprovalRequest,
    TopupMarkPaidRequest,
    TopupReceiptUploadRequest,
    TopupRequestResponse,
    TopupTransactionResponse,
    TopupApprovalLogResponse,
    TopupStatisticsResponse,
    TopupDashboardResponse,
    AdAccountBalance
)
from exceptions.custom_exceptions import (
    ResourceNotFoundError,
    PermissionDeniedError,
    BusinessLogicError,
    ResourceConflictError
)
from utils.id_generator import generate_request_no
from utils.audit import create_audit_log


class TopupService:
    """充值管理服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.MAX_SINGLE_AMOUNT = Decimal("100000")  # 单笔充值上限
        self.MAX_ACCOUNT_BALANCE = Decimal("500000")  # 账户余额上限
        self.MAX_DAILY_REQUESTS = 3  # 每日最大申请次数

    def create_request(
        self,
        request_data: TopupRequestCreate,
        current_user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> TopupRequest:
        """创建充值申请"""
        # 1. 验证广告账户权限
        ad_account = self._validate_ad_account_access(
            request_data.ad_account_id,
            current_user
        )

        # 2. 验证申请金额
        if request_data.requested_amount > self.MAX_SINGLE_AMOUNT:
            raise BusinessLogicError(
                f"单笔充值金额不能超过{self.MAX_SINGLE_AMOUNT}",
                error_code="BIZ_201"
            )

        # 3. 检查账户余额上限
        self._check_account_balance_limit(
            request_data.ad_account_id,
            request_data.requested_amount
        )

        # 4. 检查申请频次限制
        self._check_daily_request_limit(
            request_data.ad_account_id,
            current_user.id
        )

        # 5. 创建充值申请
        request_no = generate_request_no("TOP")

        topup_request = TopupRequest(
            request_no=request_no,
            ad_account_id=request_data.ad_account_id,
            project_id=ad_account.project_id,
            requested_amount=request_data.requested_amount,
            currency=request_data.currency,
            urgency_level=request_data.urgency_level.value,
            reason=request_data.reason,
            notes=request_data.notes,
            expected_date=request_data.expected_date,
            requested_by=current_user.id
        )

        self.db.add(topup_request)
        self.db.flush()

        # 6. 记录审批日志
        self._create_approval_log(
            request_id=topup_request.id,
            action="submitted",
            actor=current_user,
            previous_status=None,
            new_status="pending",
            notes="提交充值申请",
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.db.commit()
        return topup_request

    def get_requests(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        urgency: Optional[str] = None,
        ad_account_id: Optional[int] = None,
        project_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        request_no: Optional[str] = None
    ) -> Tuple[List[TopupRequest], int]:
        """获取充值申请列表"""
        query = self.db.query(TopupRequest)

        # 应用权限过滤
        query = self._apply_permission_filter(query, current_user)

        # 应用搜索条件
        if status:
            query = query.filter(TopupRequest.status == status)
        if urgency:
            query = query.filter(TopupRequest.urgency_level == urgency)
        if ad_account_id:
            query = query.filter(TopupRequest.ad_account_id == ad_account_id)
        if project_id:
            query = query.filter(TopupRequest.project_id == project_id)
        if start_date:
            query = query.filter(TopupRequest.created_at >= start_date)
        if end_date:
            query = query.filter(TopupRequest.created_at <= end_date + timedelta(days=1))
        if request_no:
            query = query.filter(TopupRequest.request_no.like(f"%{request_no}%"))

        # 计算总数
        total = query.count()

        # 分页和排序
        requests = (
            query
            .options(
                joinedload(TopupRequest.ad_account),
                joinedload(TopupRequest.project),
                joinedload(TopupRequest.requester),
                joinedload(TopupRequest.data_reviewer),
                joinedload(TopupRequest.finance_approver)
            )
            .order_by(desc(TopupRequest.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return requests, total

    def get_request_by_id(self, request_id: int, current_user: User) -> TopupRequest:
        """获取充值申请详情"""
        request = (
            self.db.query(TopupRequest)
            .options(
                joinedload(TopupRequest.ad_account),
                joinedload(TopupRequest.project),
                joinedload(TopupRequest.requester),
                joinedload(TopupRequest.data_reviewer),
                joinedload(TopupRequest.finance_approver),
                selectinload(TopupRequest.transactions),
                selectinload(TopupRequest.approval_logs).joinedload(TopupApprovalLog.actor)
            )
            .filter(TopupRequest.id == request_id)
            .first()
        )

        if not request:
            raise ResourceNotFoundError("充值申请不存在", error_code="SYS_004")

        # 检查访问权限
        self._check_request_access(request, current_user)

        return request

    def data_review(
        self,
        request_id: int,
        review_data: TopupDataReviewRequest,
        current_user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> TopupRequest:
        """数据员审核"""
        # 获取并验证请求
        request = self._get_request_for_action(request_id, current_user, "data_review")

        # 检查状态流转
        if request.status not in ["pending"]:
            raise BusinessLogicError(
                f"当前状态({request.status})不能进行数据审核",
                error_code="BIZ_203"
            )

        old_status = request.status
        new_status = "data_review" if review_data.action == "approve" else "rejected"

        # 更新审核信息
        request.data_reviewed_by = current_user.id
        request.data_reviewed_at = datetime.utcnow()
        request.data_review_notes = review_data.notes
        request.status = new_status

        # 记录审批日志
        self._create_approval_log(
            request_id=request_id,
            action="data_reviewed",
            actor=current_user,
            previous_status=old_status,
            new_status=new_status,
            notes=review_data.notes,
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.db.commit()
        return request

    def finance_approve(
        self,
        request_id: int,
        approval_data: TopupFinanceApprovalRequest,
        current_user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> TopupRequest:
        """财务审批"""
        # 获取并验证请求
        request = self._get_request_for_action(request_id, current_user, "finance_approve")

        # 检查状态流转
        if request.status not in ["data_review"]:
            raise BusinessLogicError(
                f"当前状态({request.status})不能进行财务审批",
                error_code="BIZ_203"
            )

        old_status = request.status
        new_status = "finance_approve" if approval_data.action == "approve" else "rejected"

        # 更新审批信息
        request.finance_approved_by = current_user.id
        request.finance_approved_at = datetime.utcnow()
        request.finance_approve_notes = approval_data.notes
        request.actual_amount = approval_data.actual_amount
        request.payment_method = approval_data.payment_method.value if approval_data.payment_method else None
        request.status = new_status

        # 记录审批日志
        self._create_approval_log(
            request_id=request_id,
            action="finance_approved",
            actor=current_user,
            previous_status=old_status,
            new_status=new_status,
            notes=approval_data.notes,
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.db.commit()
        return request

    def mark_as_paid(
        self,
        request_id: int,
        paid_data: TopupMarkPaidRequest,
        current_user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> TopupRequest:
        """标记为已打款"""
        # 获取并验证请求
        request = self._get_request_for_action(request_id, current_user, "finance_approve")

        # 检查状态
        if request.status != "finance_approve":
            raise BusinessLogicError(
                f"当前状态({request.status})不能标记为已打款",
                error_code="BIZ_203"
            )

        # 检查是否已打款
        if request.paid_at:
            raise ResourceConflictError("该申请已标记为已打款", error_code="BIZ_207")

        # 更新打款信息
        request.paid_at = datetime.utcnow()
        request.status = "paid"
        if paid_data.transaction_id:
            request.transaction_id = paid_data.transaction_id

        # 记录审批日志
        self._create_approval_log(
            request_id=request_id,
            action="paid",
            actor=current_user,
            previous_status="finance_approve",
            new_status="paid",
            notes=paid_data.notes,
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.db.commit()
        return request

    def upload_receipt(
        self,
        request_id: int,
        receipt_data: TopupReceiptUploadRequest,
        current_user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> TopupRequest:
        """上传打款凭证"""
        # 获取并验证请求
        request = self._get_request_for_action(request_id, current_user, "finance_approve")

        # 更新凭证信息
        request.receipt_url = receipt_data.receipt_url
        if receipt_data.transaction_id:
            request.transaction_id = receipt_data.transaction_id

        # 如果已打款但未完成，更新为完成
        if request.status == "paid" and not request.completed_at:
            request.completed_at = datetime.utcnow()
            request.status = "completed"

            # 创建交易记录
            transaction = TopupTransaction(
                request_id=request_id,
                transaction_no=request.transaction_id or f"TXN_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                amount=request.actual_amount or request.requested_amount,
                currency=request.currency,
                payment_method=request.payment_method or "other",
                transaction_date=request.paid_at,
                receipt_file=receipt_data.receipt_url,
                notes=receipt_data.notes,
                created_by=current_user.id
            )
            self.db.add(transaction)

            # 记录审批日志
            self._create_approval_log(
                request_id=request_id,
                action="completed",
                actor=current_user,
                previous_status="paid",
                new_status="completed",
                notes="上传凭证后自动完成",
                ip_address=ip_address,
                user_agent=user_agent
            )
        else:
            # 仅记录上传日志
            self._create_approval_log(
                request_id=request_id,
                action="receipt_uploaded",
                actor=current_user,
                previous_status=request.status,
                new_status=request.status,
                notes="上传打款凭证",
                ip_address=ip_address,
                user_agent=user_agent
            )

        self.db.commit()
        return request

    def get_approval_logs(self, request_id: int, current_user: User) -> List[TopupApprovalLog]:
        """获取审批日志"""
        # 验证请求存在和权限
        request = self.get_request_by_id(request_id, current_user)

        logs = (
            self.db.query(TopupApprovalLog)
            .options(joinedload(TopupApprovalLog.actor))
            .filter(TopupApprovalLog.request_id == request_id)
            .order_by(TopupApprovalLog.created_at)
            .all()
        )

        return logs

    def get_statistics(
        self,
        current_user: User,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> TopupStatisticsResponse:
        """获取充值统计数据"""
        # 应用权限过滤
        base_query = self.db.query(TopupRequest)
        base_query = self._apply_permission_filter(base_query, current_user)

        # 应用日期过滤
        if start_date:
            base_query = base_query.filter(TopupRequest.created_at >= start_date)
        if end_date:
            base_query = base_query.filter(TopupRequest.created_at <= end_date + timedelta(days=1))

        # 基础统计
        total_requests = base_query.count()
        pending_requests = base_query.filter(TopupRequest.status == "pending").count()
        data_review_requests = base_query.filter(TopupRequest.status == "data_review").count()
        finance_approve_requests = base_query.filter(TopupRequest.status == "finance_approve").count()
        approved_requests = base_query.filter(TopupRequest.status == "finance_approve").count()
        paid_requests = base_query.filter(TopupRequest.status == "paid").count()
        completed_requests = base_query.filter(TopupRequest.status == "completed").count()
        rejected_requests = base_query.filter(TopupRequest.status == "rejected").count()

        # 金额统计
        total_amount_requested = base_query.with_entities(
            func.coalesce(func.sum(TopupRequest.requested_amount), 0)
        ).scalar() or Decimal(0)

        total_amount_approved = base_query.filter(
            TopupRequest.status.in_(["finance_approve", "paid", "completed"])
        ).with_entities(
            func.coalesce(func.sum(TopupRequest.actual_amount), 0)
        ).scalar() or Decimal(0)

        total_amount_paid = base_query.filter(
            TopupRequest.status.in_(["paid", "completed"])
        ).with_entities(
            func.coalesce(func.sum(TopupRequest.actual_amount), 0)
        ).scalar() or Decimal(0)

        # 紧急程度统计
        urgent_requests = base_query.filter(
            TopupRequest.urgency_level == "urgent"
        ).count()

        high_requests = base_query.filter(
            TopupRequest.urgency_level == "high"
        ).count()

        # 逾期统计
        overdue_requests = base_query.filter(
            and_(
                TopupRequest.status.in_(["pending", "data_review", "finance_approve"]),
                TopupRequest.expected_date < date.today()
            )
        ).count()

        # 计算平均处理时间和成功率
        avg_processing_time, success_rate = self._calculate_processing_metrics(base_query)

        # 获取趋势数据
        monthly_stats = self._get_monthly_statistics(base_query)
        top_projects = self._get_top_projects(base_query)
        top_accounts = self._get_top_accounts(base_query)

        return TopupStatisticsResponse(
            total_requests=total_requests,
            pending_requests=pending_requests,
            data_review_requests=data_review_requests,
            finance_approve_requests=finance_approve_requests,
            approved_requests=approved_requests,
            paid_requests=paid_requests,
            completed_requests=completed_requests,
            rejected_requests=rejected_requests,
            total_amount_requested=total_amount_requested,
            total_amount_approved=total_amount_approved,
            total_amount_paid=total_amount_paid,
            avg_processing_time_hours=avg_processing_time,
            avg_data_review_time_hours=0,  # TODO: 计算具体阶段时间
            avg_finance_approval_time_hours=0,
            success_rate=success_rate,
            urgent_requests=urgent_requests,
            high_requests=high_requests,
            overdue_requests=overdue_requests,
            monthly_stats=monthly_stats,
            top_projects=top_projects,
            top_accounts=top_accounts
        )

    def get_dashboard_data(self, current_user: User) -> TopupDashboardResponse:
        """获取仪表板数据"""
        # 应用权限过滤
        base_query = self.db.query(TopupRequest)
        base_query = self._apply_permission_filter(base_query, current_user)

        # 待办事项
        pending_reviews = base_query.filter(TopupRequest.status == "pending").count()
        pending_approvals = base_query.filter(TopupRequest.status == "data_review").count()
        pending_payments = base_query.filter(TopupRequest.status == "finance_approve").count()

        # 逾期项
        overdue_items = base_query.filter(
            and_(
                TopupRequest.status.in_(["pending", "data_review", "finance_approve"]),
                TopupRequest.expected_date < date.today()
            )
        ).count()

        # 今日数据
        today = date.today()
        today_requests = base_query.filter(
            func.date(TopupRequest.created_at) == today
        ).count()

        today_amount = base_query.filter(
            func.date(TopupRequest.created_at) == today
        ).with_entities(
            func.coalesce(func.sum(TopupRequest.requested_amount), 0)
        ).scalar() or Decimal(0)

        today_completed = base_query.filter(
            func.date(TopupRequest.completed_at) == today
        ).count()

        # 本月数据
        month_start = today.replace(day=1)
        month_requests = base_query.filter(
            TopupRequest.created_at >= month_start
        ).count()

        month_amount = base_query.filter(
            TopupRequest.created_at >= month_start
        ).with_entities(
            func.coalesce(func.sum(TopupRequest.requested_amount), 0)
        ).scalar() or Decimal(0)

        month_completed = base_query.filter(
            TopupRequest.completed_at >= month_start
        ).count()

        # 近期申请
        recent_requests = (
            base_query
            .options(
                joinedload(TopupRequest.ad_account),
                joinedload(TopupRequest.project),
                joinedload(TopupRequest.requester)
            )
            .filter(TopupRequest.status != "completed")
            .order_by(desc(TopupRequest.created_at))
            .limit(5)
            .all()
        )

        # 转换为响应格式
        recent_responses = [
            TopupRequestResponse.model_validate(req, from_attributes=True)
            for req in recent_requests
        ]

        # 获取统计摘要
        statistics = self.get_statistics(current_user)

        return TopupDashboardResponse(
            pending_reviews=pending_reviews,
            pending_approvals=pending_approvals,
            pending_payments=pending_payments,
            overdue_items=overdue_items,
            today_requests=today_requests,
            today_amount=today_amount,
            today_completed=today_completed,
            month_requests=month_requests,
            month_amount=month_amount,
            month_completed=month_completed,
            recent_requests=recent_responses,
            statistics=statistics
        )

    def get_account_balance(self, ad_account_id: int, current_user: User) -> AdAccountBalance:
        """获取账户余额信息"""
        # 验证账户权限
        ad_account = self._validate_ad_account_access(ad_account_id, current_user)

        # 计算已充值金额
        paid_amount = (
            self.db.query(func.coalesce(func.sum(TopupTransaction.amount), 0))
            .join(TopupRequest)
            .filter(
                and_(
                    TopupRequest.ad_account_id == ad_account_id,
                    TopupRequest.status == "completed"
                )
            )
            .scalar() or Decimal(0)
        )

        available_topup = self.MAX_ACCOUNT_BALANCE - paid_amount

        return AdAccountBalance(
            ad_account_id=ad_account_id,
            ad_account_name=ad_account.name,
            current_balance=paid_amount,
            currency="USD",
            max_balance=self.MAX_ACCOUNT_BALANCE,
            available_topup=available_topup
        )

    def export_requests(
        self,
        current_user: User,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """导出充值申请数据"""
        query = self.db.query(TopupRequest)

        # 应用权限过滤
        query = self._apply_permission_filter(query, current_user)

        # 应用过滤条件
        if start_date:
            query = query.filter(TopupRequest.created_at >= start_date)
        if end_date:
            query = query.filter(TopupRequest.created_at <= end_date + timedelta(days=1))
        if status:
            query = query.filter(TopupRequest.status == status)

        # 加载关联数据
        requests = (
            query.options(
                joinedload(TopupRequest.project),
                joinedload(TopupRequest.ad_account),
                joinedload(TopupRequest.requester),
                joinedload(TopupRequest.data_reviewer),
                joinedload(TopupRequest.finance_approver)
            )
            .order_by(desc(TopupRequest.created_at))
            .all()
        )

        # 转换为导出格式
        export_data = []
        for req in requests:
            export_data.append({
                "申请单号": req.request_no,
                "项目名称": req.project.name if req.project else "",
                "广告账户": req.ad_account.name if req.ad_account else "",
                "申请金额": float(req.requested_amount),
                "实际金额": float(req.actual_amount) if req.actual_amount else "",
                "货币": req.currency,
                "状态": req.status,
                "紧急程度": req.urgency_level,
                "申请人": req.requester.nickname if req.requester else "",
                "数据审核人": req.data_reviewer.nickname if req.data_reviewer else "",
                "财务审批人": req.finance_approver.nickname if req.finance_approver else "",
                "申请时间": req.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "数据审核时间": req.data_reviewed_at.strftime("%Y-%m-%d %H:%M:%S") if req.data_reviewed_at else "",
                "财务审批时间": req.finance_approved_at.strftime("%Y-%m-%d %H:%M:%S") if req.finance_approved_at else "",
                "打款时间": req.paid_at.strftime("%Y-%m-%d %H:%M:%S") if req.paid_at else "",
                "完成时间": req.completed_at.strftime("%Y-%m-%d %H:%M:%S") if req.completed_at else "",
                "支付方式": req.payment_method or "",
                "交易流水号": req.transaction_id or ""
            })

        return export_data

    # ===== 私有方法 =====

    def _validate_ad_account_access(self, ad_account_id: int, current_user: User) -> AdAccount:
        """验证广告账户访问权限"""
        ad_account = self.db.query(AdAccount).filter(AdAccount.id == ad_account_id).first()

        if not ad_account:
            raise ResourceNotFoundError("广告账户不存在", error_code="SYS_004")

        # 管理员和财务可以访问所有账户
        if current_user.role in ["admin", "finance", "data_operator"]:
            return ad_account

        # 账户管理员可以访问自己项目的账户
        if current_user.role == "account_manager":
            if ad_account.project and ad_account.project.account_manager_id == current_user.id:
                return ad_account

        # 媒体买家可以访问分配给自己的账户
        if current_user.role == "media_buyer":
            if ad_account.assigned_user_id == current_user.id:
                return ad_account

        raise PermissionDeniedError("无权限访问该广告账户", error_code="BIZ_206")

    def _check_account_balance_limit(self, ad_account_id: int, requested_amount: Decimal):
        """检查账户余额上限"""
        # 计算当前已充值金额
        current_balance = (
            self.db.query(func.coalesce(func.sum(TopupTransaction.amount), 0))
            .join(TopupRequest)
            .filter(
                and_(
                    TopupRequest.ad_account_id == ad_account_id,
                    TopupRequest.status == "completed"
                )
            )
            .scalar() or Decimal(0)
        )

        if current_balance + requested_amount > self.MAX_ACCOUNT_BALANCE:
            raise BusinessLogicError(
                f"充值后账户余额将超出上限({self.MAX_ACCOUNT_BALANCE})",
                error_code="BIZ_202"
            )

    def _check_daily_request_limit(self, ad_account_id: int, user_id: int):
        """检查每日申请次数限制"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        request_count = (
            self.db.query(TopupRequest)
            .filter(
                and_(
                    TopupRequest.ad_account_id == ad_account_id,
                    TopupRequest.requested_by == user_id,
                    TopupRequest.created_at >= today_start
                )
            )
            .count()
        )

        if request_count >= self.MAX_DAILY_REQUESTS:
            raise BusinessLogicError(
                f"同一账户24小时内最多只能申请{self.MAX_DAILY_REQUESTS}次充值",
                error_code="BIZ_204"
            )

    def _apply_permission_filter(self, query, current_user: User):
        """应用权限过滤"""
        # 管理员和财务可以查看所有
        if current_user.role in ["admin", "finance", "data_operator"]:
            return query

        # 账户管理员查看自己项目的申请
        if current_user.role == "account_manager":
            project_ids = (
                self.db.query(Project.id)
                .filter(Project.account_manager_id == current_user.id)
                .subquery()
            )
            return query.filter(TopupRequest.project_id.in_(project_ids))

        # 媒体买家查看自己的申请
        if current_user.role == "media_buyer":
            return query.filter(TopupRequest.requested_by == current_user.id)

        # 默认返回空查询
        return query.filter(False)

    def _check_request_access(self, request: TopupRequest, current_user: User):
        """检查充值申请访问权限"""
        # 管理员和财务可以访问所有
        if current_user.role in ["admin", "finance", "data_operator"]:
            return

        # 账户管理员查看自己项目的申请
        if current_user.role == "account_manager":
            if request.project and request.project.account_manager_id == current_user.id:
                return

        # 媒体买家查看自己的申请
        if current_user.role == "media_buyer":
            if request.requested_by == current_user.id:
                return

        raise PermissionDeniedError("无权限查看该充值申请", error_code="BIZ_206")

    def _get_request_for_action(
        self,
        request_id: int,
        current_user: User,
        action: str
    ) -> TopupRequest:
        """获取可操作的充值申请"""
        request = self.get_request_by_id(request_id, current_user)

        # 验证操作权限
        if action == "data_review" and current_user.role != "data_operator":
            raise PermissionDeniedError("只有数据员可以进行数据审核", error_code="BIZ_206")

        if action == "finance_approve" and current_user.role != "finance":
            raise PermissionDeniedError("只有财务可以进行财务审批", error_code="BIZ_206")

        return request

    def _create_approval_log(
        self,
        request_id: int,
        action: str,
        actor: User,
        previous_status: Optional[str],
        new_status: Optional[str],
        notes: Optional[str],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """创建审批日志"""
        log = TopupApprovalLog(
            request_id=request_id,
            action=action,
            actor_id=actor.id,
            actor_role=actor.role,
            notes=notes,
            previous_status=previous_status,
            new_status=new_status,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(log)

    def _calculate_processing_metrics(self, query) -> Tuple[float, float]:
        """计算处理时间指标"""
        # 计算平均处理时间
        completed_requests = query.filter(
            and_(
                TopupRequest.status == "completed",
                TopupRequest.completed_at.isnot(None)
            )
        ).all()

        if not completed_requests:
            return 0.0, 0.0

        total_hours = 0
        for req in completed_requests:
            if req.created_at and req.completed_at:
                delta = req.completed_at - req.created_at
                total_hours += delta.total_seconds() / 3600

        avg_processing_time = total_hours / len(completed_requests)

        # 计算成功率
        total_count = query.count()
        success_count = query.filter(
            TopupRequest.status == "completed"
        ).count()

        success_rate = (success_count / total_count * 100) if total_count > 0 else 0.0

        return round(avg_processing_time, 2), round(success_rate, 2)

    def _get_monthly_statistics(self, query) -> List[dict]:
        """获取月度统计"""
        monthly_data = (
            query
            .with_entities(
                extract('year', TopupRequest.created_at).label('year'),
                extract('month', TopupRequest.created_at).label('month'),
                func.count(TopupRequest.id).label('count'),
                func.sum(TopupRequest.requested_amount).label('amount')
            )
            .group_by(
                extract('year', TopupRequest.created_at),
                extract('month', TopupRequest.created_at)
            )
            .order_by(
                extract('year', TopupRequest.created_at),
                extract('month', TopupRequest.created_at)
            )
            .limit(12)
            .all()
        )

        return [
            {
                "month": f"{int(row.year)}-{int(row.month):02d}",
                "count": row.count,
                "amount": float(row.amount) if row.amount else 0
            }
            for row in monthly_data
        ]

    def _get_top_projects(self, query) -> List[dict]:
        """获取充值金额TOP5项目"""
        top_projects = (
            query
            .join(Project)
            .with_entities(
                Project.id,
                Project.name,
                func.sum(TopupRequest.requested_amount).label('total_amount'),
                func.count(TopupRequest.id).label('count')
            )
            .group_by(Project.id, Project.name)
            .order_by(func.sum(TopupRequest.requested_amount).desc())
            .limit(5)
            .all()
        )

        return [
            {
                "project_id": row.id,
                "project_name": row.name,
                "total_amount": float(row.total_amount) if row.total_amount else 0,
                "request_count": row.count
            }
            for row in top_projects
        ]

    def _get_top_accounts(self, query) -> List[dict]:
        """获取充值频次TOP5账户"""
        top_accounts = (
            query
            .join(AdAccount)
            .with_entities(
                AdAccount.id,
                AdAccount.name,
                func.count(TopupRequest.id).label('count')
            )
            .group_by(AdAccount.id, AdAccount.name)
            .order_by(func.count(TopupRequest.id).desc())
            .limit(5)
            .all()
        )

        return [
            {
                "account_id": row.id,
                "account_name": row.name,
                "request_count": row.count
            }
            for row in top_accounts
        ]