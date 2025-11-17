"""
日报管理业务逻辑层
Version: 1.0
Author: Claude协作开发
"""

import logging
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy import and_, or_, func, desc, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from core.db import get_db
from core.response import error_response
from exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError
)
from models.daily_report import DailyReport, DailyReportAuditLog
from models.ad_account import AdAccount
from models.users import User
from schemas.daily_report import (
    DailyReportCreateRequest,
    DailyReportUpdateRequest,
    DailyReportAuditRequest,
    DailyReportBatchImportRequest,
    DailyReportQueryParams,
    DailyReportImportError
)

# 创建logger实例
logger = logging.getLogger(__name__)


class DailyReportService:
    """日报管理服务类"""

    def __init__(self, db: Session):
        self.db = db

    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        try:
            yield
            self.db.commit()
            logger.debug("Transaction committed successfully")
        except Exception as e:
            logger.error(f"Transaction failed, rolling back: {str(e)}", exc_info=True)
            self.db.rollback()
            raise

    def create_daily_report(
        self,
        request: DailyReportCreateRequest,
        current_user: User
    ) -> DailyReport:
        """
        创建日报

        Args:
            request: 创建日报请求
            current_user: 当前用户

        Returns:
            DailyReport: 创建的日报对象

        Raises:
            ResourceConflictError: 日报已存在
            PermissionDeniedError: 无权限操作该账户
        """
        logger.info(
            f"Creating daily report for account_id={request.ad_account_id}, "
            f"date={request.report_date}, user={current_user.id} ({current_user.role})"
        )

        # 验证用户是否有权限操作该广告账户
        ad_account = self.db.query(AdAccount).filter(
            AdAccount.id == request.ad_account_id
        ).first()

        if not ad_account:
            logger.error(f"Ad account {request.ad_account_id} not found")
            raise ResourceNotFoundError(f"广告账户 {request.ad_account_id} 不存在")

        # 账户权限检查
        if not self._can_user_access_account(current_user, ad_account):
            raise PermissionDeniedError(
                f"无权限操作广告账户 {ad_account.name}（ID: {ad_account.id}）"
            )

        with self.transaction():
            try:
                # 创建日报记录
                daily_report = DailyReport(
                    report_date=request.report_date,
                    ad_account_id=request.ad_account_id,
                    campaign_name=request.campaign_name,
                    ad_group_name=request.ad_group_name,
                    ad_creative_name=request.ad_creative_name,
                    impressions=request.impressions,
                    clicks=request.clicks,
                    spend=request.spend,
                    conversions=request.conversions,
                    new_follows=request.new_follows,
                    cpa=request.cpa,
                    roas=request.roas,
                    notes=request.notes,
                    created_by=current_user.id
                )

                self.db.add(daily_report)
                self.db.flush()  # 获取ID

                # 记录审计日志
                self._create_audit_log(
                    daily_report_id=daily_report.id,
                    action="created",
                    audit_user_id=current_user.id,
                    ip_address=getattr(current_user, 'ip_address', None),
                    user_agent=getattr(current_user, 'user_agent', None)
                )

                logger.info(
                    f"Daily report created successfully: id={daily_report.id}, "
                    f"account_id={request.ad_account_id}, date={request.report_date}"
                )
                return daily_report

            except IntegrityError as e:
                logger.warning(
                    f"IntegrityError creating daily report: {str(e)}, "
                    f"account_id={request.ad_account_id}, date={request.report_date}"
                )
                if "uq_daily_reports_date_account" in str(e):
                    raise ResourceConflictError(
                        f"账户 {request.ad_account_id} 在 {request.report_date} 的日报已存在"
                    )
                raise BusinessLogicError(f"创建日报失败：数据完整性错误 - {str(e)}")

    def get_daily_reports(
        self,
        params: DailyReportQueryParams,
        current_user: User,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[DailyReport], int]:
        """
        获取日报列表

        Args:
            params: 查询参数
            current_user: 当前用户
            page: 页码
            page_size: 每页数量

        Returns:
            Tuple[List[DailyReport], int]: 日报列表和总数
        """
        logger.info(
            f"Querying daily reports: user={current_user.id} ({current_user.role}), "
            f"page={page}, page_size={page_size}"
        )

        query = self.db.query(DailyReport).options(
            joinedload(DailyReport.ad_account),
            joinedload(DailyReport.creator),
            joinedload(DailyReport.auditor)
        )

        # 构建查询条件
        where_conditions = []

        # 日期范围
        if params.report_date_start:
            where_conditions.append(DailyReport.report_date >= params.report_date_start)
        if params.report_date_end:
            where_conditions.append(DailyReport.report_date <= params.report_date_end)

        # 广告账户
        if params.ad_account_id:
            where_conditions.append(DailyReport.ad_account_id == params.ad_account_id)

        # 状态
        if params.status:
            where_conditions.append(DailyReport.status == params.status)

        # 创建者（投手）
        if params.media_buyer_id:
            where_conditions.append(DailyReport.created_by == params.media_buyer_id)

        # 项目筛选
        if params.project_id:
            where_conditions.append(
                DailyReport.ad_account_id.in_(
                    self.db.query(AdAccount.id).filter(
                        AdAccount.project_id == params.project_id
                    )
                )
            )

        # 应用权限过滤
        if current_user.role == "media_buyer":
            # 投手：只能看分配给自己的账户的日报
            logger.debug(f"Applying media_buyer RBAC filter for user {current_user.id}")
            where_conditions.append(
                DailyReport.ad_account_id.in_(
                    self.db.query(AdAccount.id).filter(
                        AdAccount.assigned_user_id == current_user.id
                    )
                )
            )
        elif current_user.role == "account_manager":
            # 户管：只能看所管理项目的日报
            accessible_projects = self._get_manager_accessible_projects(current_user.id)
            logger.debug(
                f"Applying account_manager RBAC filter for user {current_user.id}, "
                f"accessible_projects={accessible_projects}"
            )
            where_conditions.append(
                DailyReport.ad_account_id.in_(
                    self.db.query(AdAccount.id).filter(
                        AdAccount.project_id.in_(accessible_projects)
                    )
                )
            )
        elif current_user.role in ["admin", "finance", "data_operator"]:
            # 管理员、财务、数据员：可以看所有数据
            logger.debug(f"User {current_user.id} ({current_user.role}) has full access to all reports")
        else:
            # 未知角色：拒绝访问
            logger.error(f"Unauthorized role {current_user.role} for user {current_user.id}")
            raise PermissionDeniedError("未授权的角色，无法查看日报")

        # 应用所有条件
        if where_conditions:
            query = query.filter(and_(*where_conditions))

        # 统计总数
        total = query.count()

        # 分页和排序
        reports = query.order_by(desc(DailyReport.report_date)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        logger.info(
            f"Daily reports query completed: user={current_user.id}, "
            f"total={total}, page={page}, returned={len(reports)}"
        )
        return reports, total

    def get_daily_report(
        self,
        report_id: int,
        current_user: User
    ) -> DailyReport:
        """
        获取日报详情

        Args:
            report_id: 日报ID
            current_user: 当前用户

        Returns:
            DailyReport: 日报对象

        Raises:
            ResourceNotFoundError: 日报不存在
            PermissionDeniedError: 无权限查看
        """
        report = self.db.query(DailyReport).options(
            joinedload(DailyReport.ad_account),
            joinedload(DailyReport.creator),
            joinedload(DailyReport.auditor)
        ).filter(DailyReport.id == report_id).first()

        if not report:
            raise ResourceNotFoundError(f"日报 {report_id} 不存在")

        # 权限检查：验证当前用户是否有权限查看该日报
        if not self._can_user_view_report(current_user, report):
            raise PermissionDeniedError(f"无权限查看该日报（ID: {report_id}）")

        return report

    def update_daily_report(
        self,
        report_id: int,
        request: DailyReportUpdateRequest,
        current_user: User
    ) -> DailyReport:
        """
        更新日报

        Args:
            report_id: 日报ID
            request: 更新请求
            current_user: 当前用户

        Returns:
            DailyReport: 更新后的日报对象

        Raises:
            ResourceNotFoundError: 日报不存在
            BusinessLogicError: 状态不允许修改
            PermissionDeniedError: 无权限修改
        """
        logger.info(
            f"Updating daily report: id={report_id}, user={current_user.id} ({current_user.role})"
        )

        report = self.get_daily_report(report_id, current_user)

        # 检查是否可以修改
        if report.status == "approved":
            logger.warning(f"Cannot update approved report: id={report_id}")
            raise BusinessLogicError("已审核的日报不能修改")

        # 权限检查：验证当前用户是否有权限编辑该日报
        if not self._can_user_edit_report(current_user, report):
            raise PermissionDeniedError(f"无权限修改该日报（ID: {report_id}）")

        with self.transaction():
            # 更新字段
            update_data = request.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(report, field):
                    setattr(report, field, value)

            # 更新时间
            report.updated_at = datetime.utcnow()

            # 记录审计日志
            self._create_audit_log(
                daily_report_id=report_id,
                action="updated",
                audit_user_id=current_user.id,
                old_status=report.status,
                new_status=report.status,
                ip_address=getattr(current_user, 'ip_address', None),
                user_agent=getattr(current_user, 'user_agent', None)
            )

            logger.info(
                f"Daily report updated successfully: id={report_id}, "
                f"updated_fields={list(update_data.keys())}"
            )
            return report

    def delete_daily_report(
        self,
        report_id: int,
        current_user: User
    ) -> bool:
        """
        删除日报

        Args:
            report_id: 日报ID
            current_user: 当前用户

        Returns:
            bool: 是否删除成功

        Raises:
            ResourceNotFoundError: 日报不存在
            PermissionDeniedError: 无权限删除
        """
        logger.info(
            f"Deleting daily report: id={report_id}, user={current_user.id} ({current_user.role})"
        )

        report = self.get_daily_report(report_id, current_user)

        # 只有管理员可以删除
        if current_user.role != "admin":
            logger.warning(
                f"Non-admin user {current_user.id} ({current_user.role}) attempted to delete report {report_id}"
            )
            raise PermissionDeniedError("只有管理员可以删除日报")

        with self.transaction():
            # 删除审计日志
            self.db.query(DailyReportAuditLog).filter(
                DailyReportAuditLog.daily_report_id == report_id
            ).delete()

            # 删除日报
            self.db.delete(report)

            logger.info(f"Daily report deleted successfully: id={report_id}")
            return True

    def approve_daily_report(
        self,
        report_id: int,
        request: DailyReportAuditRequest,
        current_user: User
    ) -> DailyReport:
        """
        审核通过日报

        Args:
            report_id: 日报ID
            request: 审核请求
            current_user: 当前用户

        Returns:
            DailyReport: 更新后的日报对象
        """
        return self._audit_daily_report(
            report_id=report_id,
            new_status="approved",
            audit_request=request,
            current_user=current_user
        )

    def reject_daily_report(
        self,
        report_id: int,
        request: DailyReportAuditRequest,
        current_user: User
    ) -> DailyReport:
        """
        驳回报日

        Args:
            report_id: 日报ID
            request: 审核请求
            current_user: 当前用户

        Returns:
            DailyReport: 更新后的日报对象
        """
        return self._audit_daily_report(
            report_id=report_id,
            new_status="rejected",
            audit_request=request,
            current_user=current_user
        )

    def batch_import_daily_reports(
        self,
        request: DailyReportBatchImportRequest,
        current_user: User
    ) -> Tuple[int, int, List[DailyReportImportError], List[int]]:
        """
        批量导入日报

        Args:
            request: 批量导入请求
            current_user: 当前用户

        Returns:
            Tuple[int, int, List[DailyReportImportError], List[int]]:
            成功数量、失败数量、错误列表、成功导入的ID列表
        """
        success_count = 0
        error_count = 0
        errors: List[DailyReportImportError] = []
        imported_ids: List[int] = []

        for index, report_request in enumerate(request.reports, start=1):
            try:
                report = self.create_daily_report(report_request, current_user)
                imported_ids.append(report.id)
                success_count += 1
            except Exception as e:
                error_count += 1
                error_info = DailyReportImportError(
                    row_number=index,
                    error_code="IMPORT_ERROR",
                    error_message=str(e),
                    invalid_data=report_request.model_dump()
                )
                errors.append(error_info)

                # 如果不跳过错误，直接返回
                if not request.skip_errors:
                    break

        return success_count, error_count, errors, imported_ids

    def get_daily_report_statistics(
        self,
        params: DailyReportQueryParams,
        current_user: User
    ) -> Dict[str, Any]:
        """
        获取日报统计数据

        Args:
            params: 查询参数
            current_user: 当前用户

        Returns:
            Dict[str, Any]: 统计数据
        """
        query = self.db.query(DailyReport)

        # 应用相同的查询条件
        where_conditions = []
        if params.report_date_start:
            where_conditions.append(DailyReport.report_date >= params.report_date_start)
        if params.report_date_end:
            where_conditions.append(DailyReport.report_date <= params.report_date_end)
        if params.ad_account_id:
            where_conditions.append(DailyReport.ad_account_id == params.ad_account_id)
        if params.status:
            where_conditions.append(DailyReport.status == params.status)
        if params.media_buyer_id:
            where_conditions.append(DailyReport.created_by == params.media_buyer_id)

        if where_conditions:
            query = query.filter(and_(*where_conditions))

        # 执行统计查询
        stats = query.with_entities(
            func.count(DailyReport.id).label('total_reports'),
            func.sum(DailyReport.spend).label('total_spend'),
            func.sum(DailyReport.impressions).label('total_impressions'),
            func.sum(DailyReport.clicks).label('total_clicks'),
            func.sum(DailyReport.conversions).label('total_conversions'),
            func.sum(DailyReport.new_follows).label('total_new_follows'),
            func.avg(DailyReport.cpa).label('avg_cpa'),
            func.avg(DailyReport.roas).label('avg_roas')
        ).first()

        # 按状态统计
        status_stats = query.with_entities(
            DailyReport.status,
            func.count(DailyReport.id).label('count')
        ).group_by(DailyReport.status).all()

        status_counts = {status: count for status, count in status_stats}

        # 构建返回数据
        result = {
            'total_reports': stats.total_reports or 0,
            'approved_reports': status_counts.get('approved', 0),
            'rejected_reports': status_counts.get('rejected', 0),
            'pending_reports': status_counts.get('pending', 0),
            'total_spend': stats.total_spend or Decimal('0'),
            'total_impressions': stats.total_impressions or 0,
            'total_clicks': stats.total_clicks or 0,
            'total_conversions': stats.total_conversions or 0,
            'total_new_follows': stats.total_new_follows or 0,
            'avg_cpa': stats.avg_cpa,
            'avg_roas': stats.avg_roas,
            'date_range': {
                'start_date': params.report_date_start,
                'end_date': params.report_date_end
            }
        }

        return result

    def get_daily_report_audit_logs(
        self,
        report_id: int,
        current_user: User
    ) -> List[DailyReportAuditLog]:
        """
        获取日报审核日志

        Args:
            report_id: 日报ID
            current_user: 当前用户

        Returns:
            List[DailyReportAuditLog]: 审核日志列表
        """
        # 先验证日报存在和权限
        self.get_daily_report(report_id, current_user)

        return self.db.query(DailyReportAuditLog).options(
            joinedload(DailyReportAuditLog.audit_user)
        ).filter(
            DailyReportAuditLog.daily_report_id == report_id
        ).order_by(desc(DailyReportAuditLog.audit_time)).all()

    def _audit_daily_report(
        self,
        report_id: int,
        new_status: str,
        audit_request: DailyReportAuditRequest,
        current_user: User
    ) -> DailyReport:
        """
        审核日报内部方法

        Args:
            report_id: 日报ID
            new_status: 新状态
            audit_request: 审核请求
            current_user: 当前用户

        Returns:
            DailyReport: 更新后的日报对象
        """
        # 验证权限
        if current_user.role not in ["admin", "data_operator"]:
            raise PermissionDeniedError("无权限审核日报")

        report = self.get_daily_report(report_id, current_user)

        # 检查状态
        if report.status == new_status:
            raise BusinessLogicError(f"日报已经是{new_status}状态")

        with self.transaction():
            old_status = report.status
            report.status = new_status
            report.audit_notes = audit_request.audit_notes
            report.audit_user_id = current_user.id
            report.audit_time = datetime.utcnow()
            report.updated_at = datetime.utcnow()

            # 记录审计日志
            self._create_audit_log(
                daily_report_id=report_id,
                action=new_status,
                audit_user_id=current_user.id,
                old_status=old_status,
                new_status=new_status,
                audit_notes=audit_request.audit_notes,
                ip_address=getattr(current_user, 'ip_address', None),
                user_agent=getattr(current_user, 'user_agent', None)
            )

            return report

    def _create_audit_log(
        self,
        daily_report_id: int,
        action: str,
        audit_user_id: int,
        old_status: Optional[str] = None,
        new_status: Optional[str] = None,
        audit_notes: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> DailyReportAuditLog:
        """
        创建审计日志

        Args:
            daily_report_id: 日报ID
            action: 操作类型
            audit_user_id: 审核人ID
            old_status: 旧状态
            new_status: 新状态
            audit_notes: 审核说明
            ip_address: IP地址
            user_agent: 用户代理

        Returns:
            DailyReportAuditLog: 审计日志对象
        """
        audit_log = DailyReportAuditLog(
            daily_report_id=daily_report_id,
            action=action,
            old_status=old_status,
            new_status=new_status,
            audit_user_id=audit_user_id,
            audit_notes=audit_notes,
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.db.add(audit_log)
        return audit_log

    # ============== RBAC 权限检查辅助方法 ==============

    def _get_manager_accessible_projects(self, user_id: int) -> List[int]:
        """
        获取用户有权限访问的项目ID列表（用于account_manager角色）

        Args:
            user_id: 用户ID

        Returns:
            List[int]: 项目ID列表

        Note:
            account_manager可以访问：
            1. 自己作为account_manager的项目 (Project.account_manager_id)
            2. 自己作为成员的项目 (ProjectMember)
        """
        from models.projects import Project, ProjectMember

        # 1. 作为account_manager的项目
        managed_projects = self.db.query(Project.id).filter(
            Project.account_manager_id == user_id
        ).all()

        # 2. 作为成员的项目
        member_projects = self.db.query(ProjectMember.project_id).filter(
            ProjectMember.user_id == user_id
        ).all()

        # 合并去重
        project_ids = set(
            [p.id for p in managed_projects] +
            [p.project_id for p in member_projects]
        )

        # TODO: 考虑缓存该结果以提升性能，避免每次查询都join
        return list(project_ids)

    def _can_user_access_account(self, user: User, account: AdAccount) -> bool:
        """
        检查用户是否有权限操作广告账户

        Args:
            user: 用户对象
            account: 广告账户对象

        Returns:
            bool: 是否有权限

        Permission Rules:
            - admin: 全部权限
            - data_operator: 全部权限（用于审核）
            - media_buyer: 只能操作 assigned_user_id 为自己的账户
            - account_manager: 只能操作自己管理的项目下的账户
            - 其他角色: 无权限
        """
        import logging
        logger = logging.getLogger(__name__)

        # admin 全部权限
        if user.role == "admin":
            logger.debug(f"User {user.id} (admin) has access to account {account.id}")
            return True

        # 数据员可以操作所有账户（用于审核）
        if user.role == "data_operator":
            logger.debug(f"User {user.id} (data_operator) has access to account {account.id}")
            return True

        # 投手：只能操作 assigned_user_id 是自己的账户
        if user.role == "media_buyer":
            has_access = account.assigned_user_id == user.id
            logger.debug(
                f"User {user.id} (media_buyer) {'has' if has_access else 'NO'} access to account {account.id}"
            )
            return has_access

        # 项目经理：只能操作自己管理的项目下的账户
        if user.role == "account_manager":
            accessible_projects = self._get_manager_accessible_projects(user.id)
            has_access = account.project_id in accessible_projects
            logger.debug(
                f"User {user.id} (account_manager) {'has' if has_access else 'NO'} access to account {account.id}"
            )
            return has_access

        # 其他角色：无权限
        logger.warning(f"User {user.id} with role {user.role} has NO access to account {account.id}")
        return False

    def _can_user_view_report(self, user: User, report: DailyReport) -> bool:
        """
        检查用户是否有权限查看日报

        Args:
            user: 用户对象
            report: 日报对象

        Returns:
            bool: 是否有权限

        Permission Rules:
            - admin/finance/data_operator: 可以查看所有日报
            - media_buyer: 只能查看 assigned_user_id 为自己的账户的日报
            - account_manager: 只能查看自己管理的项目的日报
        """
        import logging
        logger = logging.getLogger(__name__)

        # admin/finance/data_operator 可以看所有
        if user.role in ["admin", "finance", "data_operator"]:
            logger.debug(f"User {user.id} ({user.role}) can view report {report.id}")
            return True

        # 投手：只能看 assigned_user_id 是自己的账户
        if user.role == "media_buyer":
            account = report.ad_account
            if not account:
                logger.warning(f"Report {report.id} has no associated account")
                return False
            has_access = account.assigned_user_id == user.id
            logger.debug(
                f"User {user.id} (media_buyer) {'can' if has_access else 'CANNOT'} view report {report.id}"
            )
            return has_access

        # 项目经理：检查是否有项目权限
        if user.role == "account_manager":
            if not report.ad_account or not report.ad_account.project_id:
                logger.warning(f"Report {report.id} has no associated account or project")
                return False
            accessible_projects = self._get_manager_accessible_projects(user.id)
            has_access = report.ad_account.project_id in accessible_projects
            logger.debug(
                f"User {user.id} (account_manager) {'can' if has_access else 'CANNOT'} view report {report.id}"
            )
            return has_access

        logger.warning(f"User {user.id} with role {user.role} CANNOT view report {report.id}")
        return False

    def _can_user_edit_report(self, user: User, report: DailyReport) -> bool:
        """
        检查用户是否可以编辑日报

        权限规则：
        - admin/data_operator: 可以编辑所有日报（用于数据管理和审核）
        - media_buyer: 只能编辑自己创建的日报
        - 其他角色: 不能编辑日报

        Args:
            user: 当前用户
            report: 日报对象

        Returns:
            bool: 是否有编辑权限
        """
        # 管理员和数据员可以编辑所有日报
        if user.role in ["admin", "data_operator"]:
            logger.debug(f"User {user.id} ({user.role}) can edit all reports")
            return True

        # 投手只能编辑自己创建的日报
        if user.role == "media_buyer":
            has_access = report.created_by == user.id
            logger.debug(
                f"User {user.id} (media_buyer) {'can' if has_access else 'CANNOT'} edit report {report.id} "
                f"(created_by={report.created_by})"
            )
            return has_access

        # 其他角色（财务、户管）不能直接编辑日报
        logger.warning(f"User {user.id} with role {user.role} CANNOT edit report {report.id}")
        return False