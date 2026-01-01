"""
AdSpend Service - 外部消耗数据服务层 (重构版)

SoT References:
- MASTER.md v4.4 §2.4 (7角色模型)
- DATA_SCHEMA.md v5.3 (ad_spend_daily 表)
- API_SOT.md v9.3 (消耗数据 API)

依赖代码块:
- pagination: 分页查询
- permission-filter: 权限过滤

权限矩阵 (MASTER.md v4.8 §2.4):
- ceo, finance, admin: 全部数据
- project_owner: 自己项目的消耗
- pitcher: 自己导入的消耗
- account_manager: 管理账户的消耗

Version: 2.0
Author: Claude Code
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Tuple, Dict
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from backend.models.workflow.ad_spend import AdSpendDaily
from backend.models import User
from backend.schemas.ad_spend import (
    AdSpendCreateRequest,
    AdSpendBatchImportRequest,
    AdSpendQueryParams,
    AdSpendStatisticsResponse,
)
from backend.exceptions.custom_exceptions import (
    ResourceNotFoundError,
    BusinessLogicError,
    PermissionDeniedError,
)

logger = logging.getLogger(__name__)


class AdSpendService:
    """
    外部消耗数据服务

    职责:
    - 消耗数据 CRUD
    - 批量导入
    - 统计分析
    - 权限过滤

    权限矩阵 (MASTER.md v4.4 §2.4):
    - ceo, finance, admin: 全部数据
    - pitcher: 自己导入的数据
    - 其他角色: 根据权限过滤
    """

    def __init__(self, db: Session):
        self.db = db

    def _apply_permission_filter(self, query, user: User):
        """
        权限过滤 (MASTER.md v4.4 §2.4)

        - ceo, finance, admin: 无过滤
        - pitcher: 仅自己导入的数据
        - 其他角色: 默认仅自己导入的数据
        """
        if user.role in ["ceo", "finance", "admin"]:
            return query
        # pitcher 和其他角色只能看自己导入的数据
        return query.filter(AdSpendDaily.imported_by == user.id)

    def create_ad_spend(
        self, request: AdSpendCreateRequest, user: User
    ) -> AdSpendDaily:
        """创建或更新消耗记录 (upsert)"""
        existing = self.db.scalar(
            select(AdSpendDaily).where(
                and_(
                    AdSpendDaily.spend_date == request.spend_date,
                    AdSpendDaily.ad_account_code == request.ad_account_code,
                    AdSpendDaily.source_platform == request.source_platform,
                )
            )
        )
        if existing:
            existing.spend_amount = request.spend_amount
            existing.impressions = request.impressions
            existing.clicks = request.clicks
            existing.conversions = request.conversions
            existing.currency = request.currency
            existing.raw_payload = request.raw_payload
            self.db.commit()
            self.db.refresh(existing)
            return existing

        record = AdSpendDaily(
            source_platform=request.source_platform,
            ad_account_code=request.ad_account_code,
            ad_account_id=request.ad_account_id,
            spend_date=request.spend_date,
            spend_amount=request.spend_amount,
            currency=request.currency,
            impressions=request.impressions,
            clicks=request.clicks,
            conversions=request.conversions,
            raw_payload=request.raw_payload,
            imported_by=user.id,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def batch_import(
        self, request: AdSpendBatchImportRequest, user: User
    ) -> Tuple[int, int, List[Dict], List[str]]:
        """批量导入"""
        success, errors_list, imported_ids = 0, [], []
        for idx, rec in enumerate(request.records):
            try:
                r = self.create_ad_spend(rec, user)
                success += 1
                imported_ids.append(str(r.id))
            except Exception as e:
                errors_list.append({"row": idx + 1, "error": str(e)})
                if not request.skip_errors:
                    raise
        return success, len(errors_list), errors_list, imported_ids

    def get_ad_spend(self, spend_id: UUID, user: User) -> AdSpendDaily:
        """获取单条记录"""
        query = self._apply_permission_filter(
            select(AdSpendDaily).where(AdSpendDaily.id == spend_id), user
        )
        record = self.db.scalar(query)
        if not record:
            raise ResourceNotFoundError(f"记录不存在: {spend_id}")
        return record

    def list_ad_spend(
        self, params: AdSpendQueryParams, user: User, page: int = 1, page_size: int = 20
    ) -> Tuple[List[AdSpendDaily], int]:
        """CodeBlock: CB-BE-001 - 分页查询"""
        query = select(AdSpendDaily)
        if params.spend_date_start:
            query = query.where(AdSpendDaily.spend_date >= params.spend_date_start)
        if params.spend_date_end:
            query = query.where(AdSpendDaily.spend_date <= params.spend_date_end)
        if params.source_platform:
            query = query.where(AdSpendDaily.source_platform == params.source_platform)
        if params.ad_account_code:
            query = query.where(
                AdSpendDaily.ad_account_code.ilike(f"%{params.ad_account_code}%")
            )

        query = self._apply_permission_filter(query, user)
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        query = query.order_by(AdSpendDaily.spend_date.desc())
        records = self.db.scalars(
            query.offset((page - 1) * page_size).limit(page_size)
        ).all()
        return list(records), total

    def get_statistics(
        self, params: AdSpendQueryParams, user: User
    ) -> AdSpendStatisticsResponse:
        """获取统计"""
        query = select(
            func.sum(AdSpendDaily.spend_amount).label("total_spend"),
            func.sum(AdSpendDaily.impressions).label("total_impressions"),
            func.sum(AdSpendDaily.clicks).label("total_clicks"),
            func.sum(AdSpendDaily.conversions).label("total_conversions"),
            func.count(AdSpendDaily.id).label("record_count"),
        )
        if params.spend_date_start:
            query = query.where(AdSpendDaily.spend_date >= params.spend_date_start)
        if params.spend_date_end:
            query = query.where(AdSpendDaily.spend_date <= params.spend_date_end)

        r = self.db.execute(query).first()
        spend = r.total_spend or Decimal("0")
        clicks = r.total_clicks or 0
        return AdSpendStatisticsResponse(
            total_spend=spend,
            total_impressions=r.total_impressions or 0,
            total_clicks=clicks,
            total_conversions=r.total_conversions or 0,
            avg_cpc=(spend / clicks).quantize(Decimal("0.01")) if clicks > 0 else None,
            record_count=r.record_count or 0,
        )

    def delete_ad_spend(self, spend_id: UUID, user: User) -> bool:
        """删除 (仅管理员)"""
        if user.role != "admin":
            raise PermissionDeniedError("仅管理员可删除")
        record = self.get_ad_spend(spend_id, user)
        self.db.delete(record)
        self.db.commit()
        return True

    def get_platforms(self) -> List[str]:
        return list(
            self.db.scalars(select(AdSpendDaily.source_platform).distinct()).all()
        )

    def get_currencies(self) -> List[str]:
        return list(self.db.scalars(select(AdSpendDaily.currency).distinct()).all())
