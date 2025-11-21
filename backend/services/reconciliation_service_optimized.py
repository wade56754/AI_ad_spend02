"""
对账管理服务 - 性能优化版本
Version: 2.0
Author: Claude协作开发
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple, Iterator
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, select, text
from sqlalchemy.exc import SQLAlchemyError

from backend.models.reconciliation import (
    ReconciliationBatch, ReconciliationDetail,
    ReconciliationAdjustment, ReconciliationReport
)
from backend.models import AdAccount
from backend.models import Project
from backend.models import Channel
from backend.models import User
from backend.models.ad_spend_daily import AdSpendDaily
from backend.schemas.reconciliation import (
    ReconciliationBatchCreateRequest,
    ReconciliationDetailReviewRequest,
    ReconciliationAdjustmentCreateRequest,
    ReconciliationReportGenerateRequest,
    ReconciliationStatisticsResponse
)
from backend.utils.id_generator import generate_request_no
# Note: Response helpers moved to routers layer
from backend.exceptions import ValidationException, ResourceNotFoundException, AuthorizationException
import logging

logger = logging.getLogger(__name__)


class ReconciliationServiceOptimized:
    """对账管理服务类 - 性能优化版本"""

    def __init__(self, db: Session):
        self.db = db
        self.batch_size = 100  # 批处理大小

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
            raise ValidationError("BIZ_301", f"该日期({request.reconciliation_date})的对账已存在")

        # 生成批次号
        batch_no = generate_request_no("REC")

        batch = ReconciliationBatch(
            batch_no=batch_no,
            reconciliation_date=request.reconciliation_date,
            status="pending",
            created_by=current_user_id,
            auto_match=request.auto_match,
            notes=request.notes
        )

        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)

        logger.info(f"创建对账批次成功: batch_id={batch.id}, date={request.reconciliation_date}")
        return batch

    async def get_batch_by_id(
        self,
        batch_id: int,
        current_user_id: int,
        required_role: str = "viewer"
    ) -> ReconciliationBatch:
        """根据ID获取对账批次"""
        batch = self.db.query(ReconciliationBatch).filter(
            ReconciliationBatch.id == batch_id
        ).first()

        if not batch:
            raise ResourceNotFoundException("BIZ_302", f"对账批次({batch_id})不存在")

        return batch

    def get_active_accounts_paginated(
        self,
        offset: int = 0,
        limit: int = 100,
        project_id: Optional[int] = None,
        channel_id: Optional[int] = None
    ) -> Tuple[List[AdAccount], int]:
        """分页获取活跃广告账户"""
        query = self.db.query(AdAccount).filter(AdAccount.status == "active")

        # 添加过滤条件
        if project_id:
            query = query.filter(AdAccount.project_id == project_id)
        if channel_id:
            query = query.filter(AdAccount.channel_id == channel_id)

        # 获取总数
        total = query.count()

        # 分页查询
        accounts = query.offset(offset).limit(limit).all()

        return accounts, total

    def get_pending_spend_data(
        self,
        reconciliation_date: date,
        ad_account_ids: List[int]
    ) -> Dict[int, Dict[str, Any]]:
        """批量获取待对账的消耗数据"""
        if not ad_account_ids:
            return {}

        # 分批查询，避免IN子句过长
        spend_data = {}
        batch_size = 500

        for i in range(0, len(ad_account_ids), batch_size):
            batch_ids = ad_account_ids[i:i + batch_size]

            # 查询内部消耗数据
            spend_records = self.db.query(AdSpendDaily).filter(
                and_(
                    AdSpendDaily.date == reconciliation_date,
                    AdSpendDaily.ad_account_id.in_(batch_ids)
                )
            ).all()

            for record in spend_records:
                spend_data[record.ad_account_id] = {
                    'internal_spend': record.spend,
                    'internal_data_date': record.date,
                    'internal_leads': record.leads,
                    'internal_conversions': record.conversions
                }

        return spend_data

    async def run_reconciliation(
        self,
        batch_id: int,
        current_user_id: int,
        limit: Optional[int] = None,
        batch_size: Optional[int] = None
    ) -> ReconciliationBatch:
        """执行对账 - 优化版本"""
        batch = await self.get_batch_by_id(batch_id, current_user_id, "admin")

        if batch.status != "pending":
            raise ValidationError("BIZ_306", "只能对待处理的批次执行对账")

        # 更新批次状态
        batch.status = "processing"
        batch.started_at = datetime.utcnow()
        self.db.commit()

        # 使用传入的批次大小或默认值
        effective_batch_size = batch_size or self.batch_size

        try:
            # 获取活跃账户总数（用于进度跟踪）
            total_accounts = self.db.query(AdAccount).filter(
                AdAccount.status == "active"
            ).count()

            logger.info(f"开始对账批次 {batch_id}，总账户数: {total_accounts}")

            # 分批处理账户
            matched_count = 0
            mismatched_count = 0
            auto_matched_count = 0

            platform_total = Decimal('0.00')
            internal_total = Decimal('0.00')
            difference_total = Decimal('0.00')

            processed_accounts = 0

            # 分批处理，避免内存溢出
            offset = 0
            effective_limit = limit or total_accounts  # 如果没有limit限制，处理所有账户

            while processed_accounts < effective_limit:
                # 分页获取账户
                accounts, has_more = self._get_accounts_batch(
                    offset,
                    min(effective_batch_size, effective_limit - processed_accounts)
                )

                if not accounts:
                    break

                # 获取这些账户的ID
                account_ids = [account.id for account in accounts]

                # 批量获取消耗数据
                spend_data = await self._get_platform_spend_data_batch(account_ids)

                # 批量创建对账详情
                details = []
                for account in accounts:
                    account_id = account.id

                    # 获取平台数据（模拟）
                    platform_spend = spend_data.get(account_id, {}).get('platform_spend', Decimal('0.00'))
                    platform_data_date = spend_data.get(account_id, {}).get('platform_date', date.today())

                    # 获取内部数据
                    internal_record = await self._get_internal_spend_data(
                        account_id, batch.reconciliation_date
                    )
                    internal_spend = internal_record.spend if internal_record else Decimal('0.00')
                    internal_data_date = internal_record.date if internal_record else date.today()

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

                    # 创建对账详情对象（但不立即插入数据库）
                    detail = ReconciliationDetail(
                        batch_id=batch_id,
                        ad_account_id=account_id,
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
                    details.append(detail)

                    # 累计统计
                    platform_total += platform_spend
                    internal_total += internal_spend
                    difference_total += spend_difference

                # 批量插入数据库
                if details:
                    self.db.bulk_insert_mappings(ReconciliationDetail, [
                        {
                            'batch_id': d.batch_id,
                            'ad_account_id': d.ad_account_id,
                            'project_id': d.project_id,
                            'channel_id': d.channel_id,
                            'platform_spend': d.platform_spend,
                            'platform_data_date': d.platform_data_date,
                            'internal_spend': d.internal_spend,
                            'internal_data_date': d.internal_data_date,
                            'spend_difference': d.spend_difference,
                            'is_matched': d.is_matched,
                            'match_status': d.match_status,
                            'auto_confidence': d.auto_confidence
                        } for d in details
                    ])
                    self.db.commit()

                processed_accounts += len(accounts)
                logger.info(f"已处理账户: {processed_accounts}/{min(effective_limit, total_accounts)}")

                offset += effective_batch_size

                if not has_more:
                    break

            # 更新批次统计信息
            batch.total_accounts = processed_accounts
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

            logger.info(f"对账完成: batch_id={batch_id}, processed={processed_accounts}, matched={matched_count}, mismatched={mismatched_count}")
            return batch

        except Exception as e:
            batch.status = "exception"
            batch.error_message = str(e)
            self.db.commit()
            logger.error(f"对账异常: batch_id={batch_id}, error={e}")
            raise e

    def _get_accounts_batch(self, offset: int, limit: int) -> Tuple[List[AdAccount], bool]:
        """获取一批账户"""
        query = self.db.query(AdAccount).filter(AdAccount.status == "active")

        accounts = query.offset(offset).limit(limit + 1).all()  # 多查一个判断是否还有更多

        has_more = len(accounts) > limit
        if has_more:
            accounts = accounts[:limit]

        return accounts, has_more

    async def _get_platform_spend_data_batch(self, account_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """批量获取平台消耗数据"""
        # 这里应该调用真实的平台API
        # 现在返回模拟数据
        platform_data = {}
        for account_id in account_ids:
            platform_data[account_id] = {
                'platform_spend': Decimal('100.00'),  # 模拟数据
                'platform_date': date.today()
            }
        return platform_data

    async def _get_internal_spend_data(self, account_id: int, reconciliation_date: date) -> Optional[AdSpendDaily]:
        """获取内部消耗数据"""
        return self.db.query(AdSpendDaily).filter(
            and_(
                AdSpendDaily.ad_account_id == account_id,
                AdSpendDaily.date == reconciliation_date
            )
        ).first()

    def create_database_indexes(self):
        """创建必要的数据库索引以提升查询性能"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_ad_spend_daily_account_date ON ad_spend_daily(ad_account_id, date);",
            "CREATE INDEX IF NOT EXISTS idx_ad_spend_daily_date ON ad_spend_daily(date);",
            "CREATE INDEX IF NOT EXISTS idx_reconciliation_detail_batch_id ON reconciliation_details(batch_id);",
            "CREATE INDEX IF NOT EXISTS idx_reconciliation_detail_account_id ON reconciliation_details(ad_account_id);",
            "CREATE INDEX IF NOT EXISTS idx_ad_account_status ON ad_accounts(status);",
            "CREATE INDEX IF NOT EXISTS idx_ad_account_project ON ad_accounts(project_id);",
            "CREATE INDEX IF NOT EXISTS idx_ad_account_channel ON ad_accounts(channel_id);",
            "CREATE INDEX IF NOT EXISTS idx_reconciliation_batch_date ON reconciliation_batches(reconciliation_date);",
            "CREATE INDEX IF NOT EXISTS idx_reconciliation_batch_status ON reconciliation_batches(status);"
        ]

        for index_sql in indexes:
            try:
                self.db.execute(text(index_sql))
                self.db.commit()
                logger.info(f"创建索引成功: {index_sql}")
            except SQLAlchemyError as e:
                if "already exists" not in str(e):
                    logger.warning(f"创建索引失败: {index_sql}, error: {e}")
                    self.db.rollback()

    async def get_reconciliation_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        project_id: Optional[int] = None
    ) -> ReconciliationStatisticsResponse:
        """获取对账统计信息 - 优化版本"""
        query = self.db.query(ReconciliationBatch)

        if start_date:
            query = query.filter(ReconciliationBatch.reconciliation_date >= start_date)
        if end_date:
            query = query.filter(ReconciliationBatch.reconciliation_date <= end_date)
        if project_id:
            # 通过JOIN过滤项目
            query = query.join(ReconciliationDetail).join(AdAccount).filter(
                AdAccount.project_id == project_id
            ).distinct()

        # 使用聚合查询获取统计数据
        stats = query.with_entities(
            func.count(ReconciliationBatch.id).label('total_batches'),
            func.sum(ReconciliationBatch.total_accounts).label('total_accounts'),
            func.sum(ReconciliationBatch.matched_accounts).label('matched_accounts'),
            func.sum(ReconciliationBatch.mismatched_accounts).label('mismatched_accounts'),
            func.sum(ReconciliationBatch.total_platform_spend).label('total_platform_spend'),
            func.sum(ReconciliationBatch.total_internal_spend).label('total_internal_spend'),
            func.sum(ReconciliationBatch.total_difference).label('total_difference')
        ).first()

        return ReconciliationStatisticsResponse(
            total_batches=stats.total_batches or 0,
            total_accounts=int(stats.total_accounts or 0),
            matched_accounts=int(stats.matched_accounts or 0),
            mismatched_accounts=int(stats.mismatched_accounts or 0),
            total_platform_spend=stats.total_platform_spend or Decimal('0.00'),
            total_internal_spend=stats.total_internal_spend or Decimal('0.00'),
            total_difference=stats.total_difference or Decimal('0.00'),
            match_rate=(stats.matched_accounts / stats.total_accounts * 100) if stats.total_accounts else 0.0
        )