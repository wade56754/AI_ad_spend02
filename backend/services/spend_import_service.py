"""
消耗数据导入服务
Version: 1.0 (Financial SoT Phase 2)
Author: Claude Code

SoT 对齐:
- FINANCIAL_SOT_DESIGN.md v1.0: 消耗事件模型与导入流程
- STATE_MACHINE.md v2.6: 事件状态机 (raw → pending → confirmed → posted → reversed)
- LEDGER_SOT.md v1.1: 账本规则 (禁止直接修改 balance)
- ERROR_CODES_SOT.md v2.1: BIZ_500-599 导入相关错误码

导入流程:
1. Excel 文件上传 → 解析行数据
2. 创建 FinancialEvent (event_type=SPEND, status=raw)
3. 验证阶段: raw → pending (数据完整性检查)
4. 确认阶段: pending → confirmed (人工确认)
5. 入账阶段: confirmed → posted (生成 ledger_entries)
6. 可选冲正: posted → reversed (生成反向分录)

业务规则:
- 每个 SPEND 事件有唯一的 idempotency_key = SPEND:{account_id}:{event_date}
- 手续费自动计算: fee_amount = amount × supplier.fee_rate
- 含费金额: gross_amount = amount + fee_amount
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
import io
import re

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.exc import IntegrityError

from backend.models.finance import (
    FinancialEvent,
    EventType,
    EventStatus,
    SourceType,
    Team,
    Buyer,
    generate_spend_idempotency_key,
)
from backend.models import AdAccount, Supplier
from backend.models.finance.ledger import LedgerEntry
from backend.schemas.spend import (
    SpendImportRequest,
    SpendEventCreate,
    SpendImportResultResponse,
    SpendEventValidateResponse,
    SpendEventConfirmResponse,
    SpendEventPostResponse,
    SpendEventReverseResponse,
    SpendEventResponse,
    ImportRowError,
    ImportRowWarning,
    ValidationError,
    ValidationWarning,
)
from backend.exceptions.custom_exceptions import (
    ResourceNotFoundError,
    BusinessLogicError,
    ResourceConflictError,
)


class SpendImportService:
    """
    消耗数据导入服务

    核心职责:
    - 解析和验证 Excel 消耗数据
    - 创建和管理 SPEND 类型的 FinancialEvent
    - 执行事件状态流转 (raw → pending → confirmed → posted)
    - 生成账本分录 (ledger_entries)

    合法调用方:
    - SpendRouter: /spend/* API 端点
    - ReconciliationService: 对账流程

    错误码范围: BIZ_500-599 (导入相关)
    """

    # 默认列名映射
    DEFAULT_COLUMN_MAPPING = {
        "account_id": ["账户ID", "账户id", "account_id", "AccountID", "账户"],
        "account_name": ["账户名称", "账户名", "account_name", "AccountName"],
        "today_max": ["今日最大消耗", "今日消耗", "today_max", "TodayMax", "当日累计"],
        "yesterday_max": ["昨日最大消耗", "昨日消耗", "yesterday_max", "YesterdayMax", "前日累计"],
        "spend": ["消耗", "消耗金额", "spend", "Spend", "花费"],
        "event_date": ["日期", "消耗日期", "event_date", "Date", "报告日期"],
    }

    def __init__(self, db: Session):
        self.db = db

    # ========== 导入方法 ==========

    def import_from_excel(
        self,
        file_content: bytes,
        file_name: str,
        request: SpendImportRequest,
        user_id: UUID,
    ) -> SpendImportResultResponse:
        """
        从 Excel 导入消耗数据

        流程:
        1. 解析 Excel 文件
        2. 映射列名到标准字段
        3. 验证每行数据
        4. 生成 idempotency_key 去重
        5. 创建 FinancialEvent (status=raw)
        6. 返回导入结果

        Args:
            file_content: 文件二进制内容
            file_name: 文件名
            request: 导入请求参数
            user_id: 操作用户ID

        Returns:
            SpendImportResultResponse: 导入结果

        Raises:
            BusinessLogicError: 文件格式错误或数据校验失败
        """
        import pandas as pd

        result = SpendImportResultResponse(
            file_name=file_name,
            team_code=request.team_code.value,
            dry_run=request.dry_run,
        )

        # 1. 获取团队信息
        team = self._get_team_by_code(request.team_code.value)

        # 2. 解析 Excel
        try:
            df = pd.read_excel(io.BytesIO(file_content))
        except Exception as e:
            raise BusinessLogicError(
                f"Excel 文件解析失败: {str(e)}",
                error_code="BIZ-501"
            )

        result.total_rows = len(df)

        if result.total_rows == 0:
            raise BusinessLogicError(
                "Excel 文件为空",
                error_code="BIZ-502"
            )

        # 3. 列名映射
        column_mapping = self._resolve_column_mapping(
            df.columns.tolist(),
            request.column_mapping
        )

        # 4. 推断事件日期 (从文件名或数据)
        event_date = request.event_date or self._infer_event_date(file_name, df, column_mapping)

        # 5. 遍历处理每行
        events_to_create = []

        for idx, row in df.iterrows():
            row_num = idx + 2  # Excel 行号 (1-based + header)

            try:
                event_data = self._parse_row(row, column_mapping, row_num, event_date)

                if event_data is None:
                    result.skipped_rows += 1
                    continue

                # 生成幂等键
                idempotency_key = generate_spend_idempotency_key(
                    str(event_data["ad_account_id"]),
                    event_data["event_date"]
                )

                # 检查重复
                if self._check_duplicate(idempotency_key):
                    result.duplicate_rows += 1
                    if request.skip_duplicates:
                        result.warnings.append(ImportRowWarning(
                            row_number=row_num,
                            warning_code="WARN-501",
                            warning_message=f"重复记录已跳过: {idempotency_key}"
                        ))
                        continue
                    else:
                        result.errors.append(ImportRowError(
                            row_number=row_num,
                            error_code="BIZ-503",
                            error_message=f"重复记录: {idempotency_key}"
                        ))
                        result.invalid_rows += 1
                        continue

                # 获取账户和供应商信息
                ad_account = self._get_ad_account(event_data["ad_account_id"])
                if not ad_account:
                    result.errors.append(ImportRowError(
                        row_number=row_num,
                        column="account_id",
                        value=str(event_data["ad_account_id"]),
                        error_code="BIZ-504",
                        error_message=f"广告账户不存在: {event_data['ad_account_id']}"
                    ))
                    result.invalid_rows += 1
                    continue

                supplier = self._get_supplier(ad_account.supplier_id) if ad_account.supplier_id else None

                # 计算手续费
                fee_rate = Decimal(str(supplier.fee_rate)) if supplier and supplier.fee_rate else Decimal("0")
                fee_amount = event_data["amount"] * fee_rate
                gross_amount = event_data["amount"] + fee_amount

                # 构建事件对象
                event = FinancialEvent(
                    event_type=EventType.SPEND.value,
                    event_status=EventStatus.RAW.value,
                    source_type=SourceType.EXCEL_IMPORT.value,
                    source_ref=file_name,
                    idempotency_key=idempotency_key,
                    amount=event_data["amount"],
                    fee_amount=fee_amount,
                    gross_amount=gross_amount,
                    currency="USD",
                    event_date=event_data["event_date"],
                    team_id=team.id,
                    buyer_id=self._get_buyer_id(ad_account),
                    supplier_id=ad_account.supplier_id,
                    ad_account_id=ad_account.id,
                    project_id=ad_account.project_id,
                    payload={
                        "today_max": float(event_data.get("today_max", 0)),
                        "yesterday_max": float(event_data.get("yesterday_max", 0)),
                        "fee_rate": float(fee_rate),
                        "import_row": row_num,
                    },
                    created_by=user_id,
                )

                events_to_create.append(event)
                result.valid_rows += 1
                result.total_amount += event_data["amount"]
                result.total_fee += fee_amount
                result.total_gross += gross_amount

            except ValueError as e:
                result.errors.append(ImportRowError(
                    row_number=row_num,
                    error_code="BIZ-505",
                    error_message=str(e)
                ))
                result.invalid_rows += 1

        # 6. 批量插入 (非 dry_run)
        if not request.dry_run and events_to_create:
            try:
                self.db.add_all(events_to_create)
                self.db.flush()

                result.event_ids = [e.id for e in events_to_create]
                result.imported_rows = len(events_to_create)

                self.db.commit()
            except IntegrityError as e:
                self.db.rollback()
                raise BusinessLogicError(
                    f"数据库插入失败: {str(e)}",
                    error_code="BIZ-506"
                )
        elif request.dry_run:
            result.imported_rows = 0  # dry_run 不实际导入

        return result

    def create_event(
        self,
        request: SpendEventCreate,
        user_id: UUID,
    ) -> FinancialEvent:
        """
        手动创建单个消耗事件

        Args:
            request: 创建请求
            user_id: 操作用户ID

        Returns:
            FinancialEvent: 创建的事件
        """
        # 验证账户
        ad_account = self._get_ad_account(request.ad_account_id)
        if not ad_account:
            raise ResourceNotFoundError(f"广告账户不存在: {request.ad_account_id}")

        # 获取供应商
        supplier = self._get_supplier(request.supplier_id)
        if not supplier:
            raise ResourceNotFoundError(f"供应商不存在: {request.supplier_id}")

        # 生成幂等键
        idempotency_key = generate_spend_idempotency_key(
            str(request.ad_account_id),
            request.event_date
        )

        # 检查重复
        if self._check_duplicate(idempotency_key):
            raise ResourceConflictError(f"消耗事件已存在: {idempotency_key}")

        # 计算手续费
        fee_rate = Decimal(str(supplier.fee_rate)) if supplier.fee_rate else Decimal("0")
        fee_amount = request.fee_amount if request.fee_amount is not None else (request.amount * fee_rate)
        gross_amount = request.amount + fee_amount

        # 获取团队
        team_id = self._get_team_id_from_account(ad_account)

        # 创建事件
        event = FinancialEvent(
            event_type=EventType.SPEND.value,
            event_status=EventStatus.RAW.value,
            source_type=SourceType.API.value,
            idempotency_key=idempotency_key,
            amount=request.amount,
            fee_amount=fee_amount,
            gross_amount=gross_amount,
            currency=request.currency,
            event_date=request.event_date,
            team_id=team_id,
            buyer_id=self._get_buyer_id(ad_account),
            supplier_id=request.supplier_id,
            ad_account_id=request.ad_account_id,
            project_id=ad_account.project_id,
            payload={
                "today_max": float(request.today_max) if request.today_max else None,
                "yesterday_max": float(request.yesterday_max) if request.yesterday_max else None,
                "fee_rate": float(fee_rate),
                "notes": request.notes,
            },
            created_by=user_id,
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return event

    # ========== 状态流转方法 ==========

    def validate_events(
        self,
        event_ids: List[UUID],
        force: bool = False,
        user_id: UUID = None,
    ) -> SpendEventValidateResponse:
        """
        验证消耗事件 (raw → pending)

        验证内容:
        - 账户存在性
        - 供应商存在性
        - 金额有效性
        - 日期合理性

        Args:
            event_ids: 事件ID列表
            force: 强制验证 (忽略警告)
            user_id: 操作用户ID

        Returns:
            SpendEventValidateResponse: 验证结果
        """
        response = SpendEventValidateResponse(
            total_events=len(event_ids),
            success=True,
            message="验证完成"
        )

        events = self._get_events_by_ids(event_ids)

        for event in events:
            errors = []
            warnings = []

            # 检查状态
            if event.event_status != EventStatus.RAW.value:
                errors.append(ValidationError(
                    event_id=event.id,
                    error_code="STATE-401",
                    error_message=f"事件状态不是 raw: {event.event_status}"
                ))

            # 检查账户
            if event.ad_account_id:
                ad_account = self._get_ad_account(event.ad_account_id)
                if not ad_account:
                    errors.append(ValidationError(
                        event_id=event.id,
                        field="ad_account_id",
                        error_code="BIZ-504",
                        error_message=f"广告账户不存在: {event.ad_account_id}"
                    ))

            # 检查金额
            if event.amount <= 0:
                errors.append(ValidationError(
                    event_id=event.id,
                    field="amount",
                    error_code="VAL-001",
                    error_message="金额必须大于 0"
                ))

            # 检查日期 (不能是未来日期)
            if event.event_date > date.today():
                warnings.append(ValidationWarning(
                    event_id=event.id,
                    warning_code="WARN-502",
                    warning_message="事件日期是未来日期"
                ))

            # 记录结果
            if errors:
                response.errors.extend(errors)
                response.invalid_events += 1
            else:
                response.warnings.extend(warnings)
                response.valid_events += 1

                # 状态转换: raw → pending
                if force or not warnings:
                    event.transition_to(EventStatus.PENDING.value)
                    response.transitioned_events += 1

        if response.invalid_events > 0:
            response.success = False
            response.message = f"验证失败: {response.invalid_events} 个事件无效"
        else:
            self.db.commit()

        return response

    def confirm_events(
        self,
        event_ids: List[UUID],
        user_id: UUID,
        notes: Optional[str] = None,
    ) -> SpendEventConfirmResponse:
        """
        确认消耗事件 (pending → confirmed)

        Args:
            event_ids: 事件ID列表
            user_id: 操作用户ID
            notes: 确认备注

        Returns:
            SpendEventConfirmResponse: 确认结果
        """
        response = SpendEventConfirmResponse(
            total_events=len(event_ids),
            success=True,
            message="确认完成"
        )

        events = self._get_events_by_ids(event_ids)

        for event in events:
            try:
                if event.event_status != EventStatus.PENDING.value:
                    response.failed_events += 1
                    response.failed_details.append({
                        "event_id": str(event.id),
                        "error_code": "STATE-402",
                        "error_message": f"事件状态不是 pending: {event.event_status}"
                    })
                    continue

                # 状态转换: pending → confirmed
                event.transition_to(EventStatus.CONFIRMED.value, user_id)

                # 记录确认备注
                if notes:
                    event.set_payload_field("confirm_notes", notes)

                response.success_events += 1

            except ValueError as e:
                response.failed_events += 1
                response.failed_details.append({
                    "event_id": str(event.id),
                    "error_code": "STATE-403",
                    "error_message": str(e)
                })

        if response.failed_events > 0:
            response.success = False
            response.message = f"部分确认失败: {response.failed_events} 个"
        else:
            self.db.commit()

        return response

    def post_events(
        self,
        event_ids: List[UUID],
        user_id: UUID,
        post_date: Optional[date] = None,
    ) -> SpendEventPostResponse:
        """
        入账消耗事件 (confirmed → posted)

        入账流程:
        1. 检查事件状态为 confirmed
        2. 生成 ledger_entries (DEBIT 到 SUPPLIER 和 ACCOUNT)
        3. 更新相关余额
        4. 状态转换: confirmed → posted

        Args:
            event_ids: 事件ID列表
            user_id: 操作用户ID
            post_date: 入账日期

        Returns:
            SpendEventPostResponse: 入账结果
        """
        response = SpendEventPostResponse(
            total_events=len(event_ids),
            success=True,
            message="入账完成"
        )

        events = self._get_events_by_ids(event_ids)
        actual_post_date = post_date or date.today()

        for event in events:
            try:
                if event.event_status != EventStatus.CONFIRMED.value:
                    response.failed_events += 1
                    response.failed_details.append({
                        "event_id": str(event.id),
                        "error_code": "STATE-404",
                        "error_message": f"事件状态不是 confirmed: {event.event_status}"
                    })
                    continue

                # 生成账本分录
                entries = self._create_ledger_entries(event, actual_post_date)
                response.ledger_entries_created += len(entries)
                response.total_amount += event.gross_amount or event.amount

                # 状态转换: confirmed → posted
                event.transition_to(EventStatus.POSTED.value)

                response.success_events += 1

            except Exception as e:
                response.failed_events += 1
                response.failed_details.append({
                    "event_id": str(event.id),
                    "error_code": "BIZ-507",
                    "error_message": str(e)
                })

        if response.failed_events > 0:
            response.success = False
            response.message = f"部分入账失败: {response.failed_events} 个"
        else:
            self.db.commit()

        return response

    def reverse_event(
        self,
        event_id: UUID,
        reason: str,
        user_id: UUID,
    ) -> SpendEventReverseResponse:
        """
        冲正消耗事件 (posted → reversed)

        冲正流程:
        1. 检查事件状态为 posted
        2. 生成反向 ledger_entries
        3. 状态转换: posted → reversed

        Args:
            event_id: 事件ID
            reason: 冲正原因
            user_id: 操作用户ID

        Returns:
            SpendEventReverseResponse: 冲正结果
        """
        event = self.db.query(FinancialEvent).filter(
            FinancialEvent.id == event_id
        ).first()

        if not event:
            raise ResourceNotFoundError(f"事件不存在: {event_id}")

        if event.event_status != EventStatus.POSTED.value:
            raise BusinessLogicError(
                f"只能冲正已入账的事件，当前状态: {event.event_status}",
                error_code="STATE-405"
            )

        # 生成反向分录
        reversal_entries = self._create_reversal_entries(event, reason)

        # 状态转换: posted → reversed
        event.transition_to(EventStatus.REVERSED.value)
        event.set_payload_field("reversal_reason", reason)
        event.set_payload_field("reversed_by", str(user_id))
        event.set_payload_field("reversed_at", datetime.utcnow().isoformat())

        self.db.commit()

        return SpendEventReverseResponse(
            event_id=event.id,
            original_amount=event.gross_amount or event.amount,
            reversed_at=datetime.utcnow(),
            reversal_ledger_entries=len(reversal_entries),
            reason=reason,
            success=True,
            message="冲正成功"
        )

    # ========== 查询方法 ==========

    def get_events(
        self,
        event_status: Optional[str] = None,
        team_id: Optional[UUID] = None,
        supplier_id: Optional[int] = None,
        ad_account_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        source_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[FinancialEvent], int]:
        """
        查询消耗事件列表

        Args:
            event_status: 事件状态筛选
            team_id: 团队ID筛选
            supplier_id: 供应商ID筛选
            ad_account_id: 账户ID筛选
            start_date: 开始日期
            end_date: 结束日期
            source_type: 来源类型
            page: 页码
            page_size: 每页数量

        Returns:
            Tuple[List[FinancialEvent], int]: (事件列表, 总数)
        """
        query = self.db.query(FinancialEvent).filter(
            FinancialEvent.event_type == EventType.SPEND.value
        )

        if event_status:
            query = query.filter(FinancialEvent.event_status == event_status)
        if team_id:
            query = query.filter(FinancialEvent.team_id == team_id)
        if supplier_id:
            query = query.filter(FinancialEvent.supplier_id == supplier_id)
        if ad_account_id:
            query = query.filter(FinancialEvent.ad_account_id == ad_account_id)
        if start_date:
            query = query.filter(FinancialEvent.event_date >= start_date)
        if end_date:
            query = query.filter(FinancialEvent.event_date <= end_date)
        if source_type:
            query = query.filter(FinancialEvent.source_type == source_type)

        total = query.count()
        events = query.order_by(
            desc(FinancialEvent.event_date),
            desc(FinancialEvent.created_at)
        ).offset((page - 1) * page_size).limit(page_size).all()

        return events, total

    def get_event_by_id(self, event_id: UUID) -> Optional[FinancialEvent]:
        """获取单个消耗事件"""
        return self.db.query(FinancialEvent).filter(
            FinancialEvent.id == event_id,
            FinancialEvent.event_type == EventType.SPEND.value
        ).first()

    def get_statistics(
        self,
        team_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        获取消耗统计

        Args:
            team_id: 团队ID筛选
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            Dict: 统计数据
        """
        base_query = self.db.query(FinancialEvent).filter(
            FinancialEvent.event_type == EventType.SPEND.value
        )

        if team_id:
            base_query = base_query.filter(FinancialEvent.team_id == team_id)
        if start_date:
            base_query = base_query.filter(FinancialEvent.event_date >= start_date)
        if end_date:
            base_query = base_query.filter(FinancialEvent.event_date <= end_date)

        # 状态统计
        status_counts = self.db.query(
            FinancialEvent.event_status,
            func.count(FinancialEvent.id).label("count"),
            func.sum(FinancialEvent.amount).label("amount"),
            func.sum(FinancialEvent.fee_amount).label("fee"),
            func.sum(FinancialEvent.gross_amount).label("gross"),
        ).filter(
            FinancialEvent.event_type == EventType.SPEND.value
        )

        if team_id:
            status_counts = status_counts.filter(FinancialEvent.team_id == team_id)
        if start_date:
            status_counts = status_counts.filter(FinancialEvent.event_date >= start_date)
        if end_date:
            status_counts = status_counts.filter(FinancialEvent.event_date <= end_date)

        status_counts = status_counts.group_by(FinancialEvent.event_status).all()

        # 构建结果
        result = {
            "total_events": 0,
            "raw_events": 0,
            "pending_events": 0,
            "confirmed_events": 0,
            "posted_events": 0,
            "reversed_events": 0,
            "total_amount": Decimal("0"),
            "total_fee": Decimal("0"),
            "total_gross": Decimal("0"),
            "posted_amount": Decimal("0"),
        }

        for row in status_counts:
            status = row.event_status
            count = row.count or 0
            amount = row.amount or Decimal("0")
            fee = row.fee or Decimal("0")
            gross = row.gross or Decimal("0")

            result["total_events"] += count
            result["total_amount"] += amount
            result["total_fee"] += fee
            result["total_gross"] += gross

            if status == EventStatus.RAW.value:
                result["raw_events"] = count
            elif status == EventStatus.PENDING.value:
                result["pending_events"] = count
            elif status == EventStatus.CONFIRMED.value:
                result["confirmed_events"] = count
            elif status == EventStatus.POSTED.value:
                result["posted_events"] = count
                result["posted_amount"] = gross
            elif status == EventStatus.REVERSED.value:
                result["reversed_events"] = count

        return result

    # ========== 私有方法 ==========

    def _get_team_by_code(self, code: str) -> Team:
        """根据代码获取团队"""
        team = self.db.query(Team).filter(Team.code == code).first()
        if not team:
            raise ResourceNotFoundError(f"团队不存在: {code}")
        return team

    def _get_ad_account(self, account_id: int) -> Optional[AdAccount]:
        """获取广告账户"""
        return self.db.query(AdAccount).filter(AdAccount.id == account_id).first()

    def _get_supplier(self, supplier_id: int) -> Optional[Supplier]:
        """获取供应商"""
        return self.db.query(Supplier).filter(Supplier.id == supplier_id).first()

    def _get_buyer_id(self, ad_account: AdAccount) -> Optional[UUID]:
        """获取投手ID"""
        if hasattr(ad_account, 'buyer_id') and ad_account.buyer_id:
            return ad_account.buyer_id
        return None

    def _get_team_id_from_account(self, ad_account: AdAccount) -> Optional[UUID]:
        """从账户获取团队ID"""
        if hasattr(ad_account, 'team_id') and ad_account.team_id:
            return ad_account.team_id
        return None

    def _check_duplicate(self, idempotency_key: str) -> bool:
        """检查是否重复"""
        return self.db.query(FinancialEvent).filter(
            FinancialEvent.idempotency_key == idempotency_key
        ).first() is not None

    def _get_events_by_ids(self, event_ids: List[UUID]) -> List[FinancialEvent]:
        """批量获取事件"""
        return self.db.query(FinancialEvent).filter(
            FinancialEvent.id.in_(event_ids),
            FinancialEvent.event_type == EventType.SPEND.value
        ).all()

    def _resolve_column_mapping(
        self,
        columns: List[str],
        custom_mapping: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        解析列名映射

        Args:
            columns: Excel 列名列表
            custom_mapping: 自定义映射

        Returns:
            Dict[str, str]: {标准字段名: Excel列名}
        """
        result = {}

        for field, aliases in self.DEFAULT_COLUMN_MAPPING.items():
            # 检查自定义映射
            if custom_mapping and field in custom_mapping:
                if custom_mapping[field] in columns:
                    result[field] = custom_mapping[field]
                    continue

            # 检查默认别名
            for alias in aliases:
                if alias in columns:
                    result[field] = alias
                    break

        return result

    def _infer_event_date(
        self,
        file_name: str,
        df,
        column_mapping: Dict[str, str]
    ) -> date:
        """
        推断事件日期

        优先级:
        1. 文件名中的日期 (如 消耗_20251219.xlsx)
        2. 数据中的日期列
        3. 今天
        """
        # 尝试从文件名提取日期
        date_patterns = [
            r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})',  # 2024-12-19 or 20241219
            r'(\d{2})[-_]?(\d{2})[-_]?(\d{4})',  # 12-19-2024
        ]

        for pattern in date_patterns:
            match = re.search(pattern, file_name)
            if match:
                groups = match.groups()
                try:
                    if len(groups[0]) == 4:  # YYYY first
                        return date(int(groups[0]), int(groups[1]), int(groups[2]))
                    else:  # YYYY last
                        return date(int(groups[2]), int(groups[0]), int(groups[1]))
                except ValueError:
                    pass

        # 尝试从数据中获取
        if "event_date" in column_mapping and column_mapping["event_date"] in df.columns:
            first_date = df[column_mapping["event_date"]].iloc[0]
            if hasattr(first_date, 'date'):
                return first_date.date()
            elif isinstance(first_date, str):
                try:
                    return datetime.strptime(first_date, "%Y-%m-%d").date()
                except ValueError:
                    pass

        # 默认今天
        return date.today()

    def _parse_row(
        self,
        row,
        column_mapping: Dict[str, str],
        row_num: int,
        default_date: date
    ) -> Optional[Dict[str, Any]]:
        """
        解析单行数据

        Args:
            row: DataFrame 行
            column_mapping: 列名映射
            row_num: 行号
            default_date: 默认日期

        Returns:
            Dict: 解析后的数据，None 表示跳过
        """
        import pandas as pd

        result = {}

        # 解析账户ID (必须)
        if "account_id" in column_mapping:
            account_id = row[column_mapping["account_id"]]
            if pd.isna(account_id):
                return None  # 跳过空行
            result["ad_account_id"] = int(account_id)
        else:
            raise ValueError(f"行 {row_num}: 缺少账户ID列")

        # 解析消耗金额 (必须)
        if "spend" in column_mapping:
            spend = row[column_mapping["spend"]]
            if pd.isna(spend):
                spend = 0
            result["amount"] = Decimal(str(spend))
        elif "today_max" in column_mapping and "yesterday_max" in column_mapping:
            today = row.get(column_mapping["today_max"], 0)
            yesterday = row.get(column_mapping["yesterday_max"], 0)
            if pd.isna(today):
                today = 0
            if pd.isna(yesterday):
                yesterday = 0
            result["amount"] = Decimal(str(today)) - Decimal(str(yesterday))
            result["today_max"] = Decimal(str(today))
            result["yesterday_max"] = Decimal(str(yesterday))
        else:
            raise ValueError(f"行 {row_num}: 缺少消耗金额")

        # 跳过零消耗
        if result["amount"] <= 0:
            return None

        # 解析日期
        if "event_date" in column_mapping:
            event_date = row[column_mapping["event_date"]]
            if pd.isna(event_date):
                result["event_date"] = default_date
            elif hasattr(event_date, 'date'):
                result["event_date"] = event_date.date()
            else:
                result["event_date"] = datetime.strptime(str(event_date), "%Y-%m-%d").date()
        else:
            result["event_date"] = default_date

        return result

    def _create_ledger_entries(
        self,
        event: FinancialEvent,
        post_date: date
    ) -> List[LedgerEntry]:
        """
        创建账本分录

        SPEND 事件生成:
        1. SUPPLIER 借方: gross_amount (供应商成本)
        2. ACCOUNT 借方: gross_amount (账户消耗)

        Args:
            event: 财务事件
            post_date: 入账日期

        Returns:
            List[LedgerEntry]: 创建的分录列表
        """
        entries = []
        amount = event.gross_amount or event.amount

        # 1. SUPPLIER 借方分录
        if event.supplier_id:
            supplier_entry = LedgerEntry(
                ledger_type="SUPPLIER",
                entry_type="COST",
                direction="DEBIT",
                amount=amount,
                currency=event.currency,
                supplier_id=event.supplier_id,
                entity_type="SUPPLIER",
                entity_id=str(event.supplier_id),
                event_id=event.id,
                idempotency_key=f"{event.idempotency_key}:SUPPLIER",
                description=f"SPEND 消耗入账 - {event.event_date}",
                entry_date=post_date,
            )
            self.db.add(supplier_entry)
            entries.append(supplier_entry)

        # 2. ACCOUNT 借方分录
        if event.ad_account_id:
            account_entry = LedgerEntry(
                ledger_type="ACCOUNT",
                entry_type="COST",
                direction="DEBIT",
                amount=amount,
                currency=event.currency,
                ad_account_id=event.ad_account_id,
                entity_type="ACCOUNT",
                entity_id=str(event.ad_account_id),
                event_id=event.id,
                idempotency_key=f"{event.idempotency_key}:ACCOUNT",
                description=f"SPEND 消耗入账 - {event.event_date}",
                entry_date=post_date,
            )
            self.db.add(account_entry)
            entries.append(account_entry)

        return entries

    def _create_reversal_entries(
        self,
        event: FinancialEvent,
        reason: str
    ) -> List[LedgerEntry]:
        """
        创建冲正分录 (反向)

        Args:
            event: 原财务事件
            reason: 冲正原因

        Returns:
            List[LedgerEntry]: 冲正分录列表
        """
        entries = []
        amount = event.gross_amount or event.amount
        reversal_date = date.today()

        # 1. SUPPLIER 贷方分录 (冲正)
        if event.supplier_id:
            supplier_entry = LedgerEntry(
                ledger_type="SUPPLIER",
                entry_type="REVERSAL",
                direction="CREDIT",
                amount=amount,
                currency=event.currency,
                supplier_id=event.supplier_id,
                entity_type="SUPPLIER",
                entity_id=str(event.supplier_id),
                event_id=event.id,
                idempotency_key=f"{event.idempotency_key}:SUPPLIER:REV",
                description=f"SPEND 冲正 - {reason}",
                entry_date=reversal_date,
            )
            self.db.add(supplier_entry)
            entries.append(supplier_entry)

        # 2. ACCOUNT 贷方分录 (冲正)
        if event.ad_account_id:
            account_entry = LedgerEntry(
                ledger_type="ACCOUNT",
                entry_type="REVERSAL",
                direction="CREDIT",
                amount=amount,
                currency=event.currency,
                ad_account_id=event.ad_account_id,
                entity_type="ACCOUNT",
                entity_id=str(event.ad_account_id),
                event_id=event.id,
                idempotency_key=f"{event.idempotency_key}:ACCOUNT:REV",
                description=f"SPEND 冲正 - {reason}",
                entry_date=reversal_date,
            )
            self.db.add(account_entry)
            entries.append(account_entry)

        return entries
