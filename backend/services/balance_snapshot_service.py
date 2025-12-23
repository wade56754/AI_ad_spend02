"""
余额快照服务 (BalanceSnapshotService)
Version: 1.0
Author: Claude Code

Phase 4 Financial SoT - 余额快照功能

SoT 基准:
- LEDGER_SOT.md v1.1 §2.4 (余额唯一真相源原则)
- DATA_SCHEMA.md v5.3 (balance_snapshots 表)

核心功能:
1. create_daily_snapshot: 为指定实体创建每日快照
2. create_all_snapshots: 批量创建所有实体的快照
3. get_balance_at_date: 获取历史余额
4. calculate_balance_from_ledger: 从账本聚合计算余额
5. validate_balance_consistency: 验证余额一致性

业务规则:
- 每个实体每天只能有一条快照记录 (唯一约束)
- 余额 = 累计贷方 - 累计借方
- 快照用于历史余额查询和对账，不用于实时余额判断
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case

from backend.models.finance.balance_snapshot import BalanceSnapshot, EntityType
from backend.models.finance.ledger import LedgerEntry
from backend.core.error_codes import BusinessErrorCodes
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    ValidationError
)

logger = logging.getLogger(__name__)


class BalanceSnapshotService:
    """
    余额快照服务

    提供实体余额快照的创建、查询和验证功能。
    快照基于 ledger_entries 聚合计算，用于历史余额追溯和对账。

    SoT Reference:
    - LEDGER_SOT.md v1.1 §2.4: 余额唯一真相源原则
    - 实时余额使用 entity.balance 字段
    - 历史余额使用 balance_snapshots 或 ledger_entries 聚合

    Usage:
        # 创建单个实体的快照
        snapshot = BalanceSnapshotService.create_daily_snapshot(
            entity_type="SUPPLIER",
            entity_id="supplier-123",
            snapshot_date=date.today(),
            db=session
        )

        # 批量创建所有实体的快照
        result = BalanceSnapshotService.create_all_snapshots(
            snapshot_date=date.today(),
            db=session
        )

        # 获取历史余额
        balance = BalanceSnapshotService.get_balance_at_date(
            entity_type="SUPPLIER",
            entity_id="supplier-123",
            as_of_date=date(2025, 1, 15),
            db=session
        )
    """

    # ========== 核心功能 ==========

    @classmethod
    def create_daily_snapshot(
        cls,
        entity_type: str,
        entity_id: str,
        snapshot_date: date,
        db: Session,
        currency: str = "USD"
    ) -> BalanceSnapshot:
        """
        为指定实体创建每日余额快照

        Args:
            entity_type: 实体类型 (SUPPLIER/PROJECT/ACCOUNT/TEAM)
            entity_id: 实体ID
            snapshot_date: 快照日期
            db: 数据库会话
            currency: 币种 (默认 USD)

        Returns:
            BalanceSnapshot: 创建或更新的快照对象

        Raises:
            ValidationError: 实体类型无效
            BusinessLogicError: 快照创建失败

        SoT Reference:
        - LEDGER_SOT.md v1.1 §2.4: 历史余额追溯使用 ledger_entries 聚合
        """
        # 验证实体类型
        cls._validate_entity_type(entity_type)

        # 验证日期不是未来
        if snapshot_date > date.today():
            raise ValidationError(
                error_code=BusinessErrorCodes.DATE_IN_FUTURE.code,
                message=f"快照日期不能是未来: {snapshot_date}"
            )

        try:
            # 从 ledger_entries 聚合计算余额
            balance_data = cls.calculate_balance_from_ledger(
                entity_type=entity_type,
                entity_id=entity_id,
                as_of_date=snapshot_date,
                db=db
            )

            # 使用 upsert 创建或更新快照
            snapshot = BalanceSnapshot.upsert_snapshot(
                session=db,
                entity_type=entity_type,
                entity_id=entity_id,
                snapshot_date=snapshot_date,
                balance=balance_data["balance"],
                total_debit=balance_data["total_debit"],
                total_credit=balance_data["total_credit"],
                currency=currency
            )

            logger.info(
                f"Created/updated snapshot for {entity_type}:{entity_id} "
                f"on {snapshot_date}, balance={balance_data['balance']}"
            )

            return snapshot

        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}", exc_info=True)
            raise BusinessLogicError(
                error_code=BusinessErrorCodes.LEDGER_CREATE_ERROR.code,
                message=f"快照创建失败: {str(e)}"
            )

    @classmethod
    def create_all_snapshots(
        cls,
        snapshot_date: date,
        db: Session,
        entity_types: Optional[List[str]] = None,
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """
        批量创建所有实体的每日快照

        Args:
            snapshot_date: 快照日期
            db: 数据库会话
            entity_types: 要处理的实体类型列表 (默认全部)
            currency: 币种

        Returns:
            Dict: {
                "date": snapshot_date,
                "success": int,
                "failed": int,
                "details": [...]
            }

        Usage:
            # 创建所有实体的快照
            result = BalanceSnapshotService.create_all_snapshots(
                snapshot_date=date.today(),
                db=session
            )

            # 只创建供应商快照
            result = BalanceSnapshotService.create_all_snapshots(
                snapshot_date=date.today(),
                entity_types=["SUPPLIER"],
                db=session
            )
        """
        if entity_types is None:
            entity_types = [et.value for et in EntityType]

        # 验证所有实体类型
        for et in entity_types:
            cls._validate_entity_type(et)

        # 获取所有有 ledger 记录的实体
        entities = cls._get_entities_with_ledger(db, entity_types, snapshot_date)

        results = {
            "date": snapshot_date.isoformat(),
            "success": 0,
            "failed": 0,
            "details": []
        }

        for entity_type, entity_id in entities:
            try:
                snapshot = cls.create_daily_snapshot(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    snapshot_date=snapshot_date,
                    db=db,
                    currency=currency
                )
                results["success"] += 1
                results["details"].append({
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "status": "success",
                    "balance": float(snapshot.balance)
                })
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "status": "failed",
                    "error": str(e)
                })
                logger.warning(f"Failed to create snapshot for {entity_type}:{entity_id}: {e}")

        # 提交所有成功的快照
        if results["success"] > 0:
            db.commit()

        logger.info(
            f"Batch snapshot creation completed: "
            f"{results['success']} success, {results['failed']} failed"
        )

        return results

    @classmethod
    def calculate_balance_from_ledger(
        cls,
        entity_type: str,
        entity_id: str,
        as_of_date: date,
        db: Session
    ) -> Dict[str, Decimal]:
        """
        从 ledger_entries 聚合计算余额

        Args:
            entity_type: 实体类型
            entity_id: 实体ID
            as_of_date: 截止日期 (包含当天)
            db: 数据库会话

        Returns:
            Dict: {
                "balance": Decimal,
                "total_debit": Decimal,
                "total_credit": Decimal
            }

        SoT Reference:
        - LEDGER_SOT.md v1.1 §2.4: 历史余额追溯使用 ledger_entries 聚合
        - 余额 = 累计贷方(CREDIT) - 累计借方(DEBIT)
        """
        # 查询截止日期前的所有分录
        # 使用 entry_date 作为时间基准
        end_of_day = datetime.combine(as_of_date, datetime.max.time())

        # 聚合计算借方和贷方总额
        # DEBIT: 负数金额 (消耗/支出)
        # CREDIT: 正数金额 (收入/充值)
        result = db.query(
            func.coalesce(
                func.sum(
                    case(
                        (LedgerEntry.direction == 'DEBIT', func.abs(LedgerEntry.amount)),
                        else_=Decimal('0')
                    )
                ),
                Decimal('0')
            ).label('total_debit'),
            func.coalesce(
                func.sum(
                    case(
                        (LedgerEntry.direction == 'CREDIT', LedgerEntry.amount),
                        else_=Decimal('0')
                    )
                ),
                Decimal('0')
            ).label('total_credit')
        ).filter(
            and_(
                LedgerEntry.entity_type == entity_type,
                LedgerEntry.entity_id == entity_id,
                LedgerEntry.entry_date <= end_of_day
            )
        ).first()

        total_debit = result.total_debit if result and result.total_debit else Decimal('0')
        total_credit = result.total_credit if result and result.total_credit else Decimal('0')

        # 余额 = 贷方 - 借方
        balance = total_credit - total_debit

        return {
            "balance": balance,
            "total_debit": total_debit,
            "total_credit": total_credit
        }

    @classmethod
    def get_balance_at_date(
        cls,
        entity_type: str,
        entity_id: str,
        as_of_date: date,
        db: Session,
        use_snapshot: bool = True
    ) -> Optional[Decimal]:
        """
        获取实体在指定日期的余额

        Args:
            entity_type: 实体类型
            entity_id: 实体ID
            as_of_date: 截止日期
            db: 数据库会话
            use_snapshot: 是否优先使用快照 (默认 True)

        Returns:
            Decimal: 余额，如果没有记录则返回 None

        SoT Reference:
        - LEDGER_SOT.md v1.1 §2.4: 历史余额追溯
        - 优先使用快照，无快照时从 ledger 聚合计算
        """
        cls._validate_entity_type(entity_type)

        if use_snapshot:
            # 尝试从快照获取
            snapshot = BalanceSnapshot.get_snapshot(
                session=db,
                entity_type=entity_type,
                entity_id=entity_id,
                snapshot_date=as_of_date
            )
            if snapshot:
                return snapshot.balance

            # 尝试获取最近的快照
            latest_snapshot = BalanceSnapshot.get_latest_snapshot(
                session=db,
                entity_type=entity_type,
                entity_id=entity_id,
                as_of_date=as_of_date
            )
            if latest_snapshot:
                # 从最近快照日期到目标日期的增量计算
                return cls._calculate_balance_from_snapshot(
                    base_snapshot=latest_snapshot,
                    target_date=as_of_date,
                    db=db
                )

        # 直接从 ledger 聚合计算
        balance_data = cls.calculate_balance_from_ledger(
            entity_type=entity_type,
            entity_id=entity_id,
            as_of_date=as_of_date,
            db=db
        )

        return balance_data["balance"]

    @classmethod
    def get_entity_balance_history(
        cls,
        entity_type: str,
        entity_id: str,
        start_date: date,
        end_date: date,
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        获取实体的余额历史

        Args:
            entity_type: 实体类型
            entity_id: 实体ID
            start_date: 开始日期
            end_date: 结束日期
            db: 数据库会话

        Returns:
            List[Dict]: 余额历史列表，每项包含 date, balance, total_debit, total_credit
        """
        cls._validate_entity_type(entity_type)

        if start_date > end_date:
            raise ValidationError(
                error_code=BusinessErrorCodes.INVALID_DATE_RANGE.code,
                message=f"开始日期不能晚于结束日期: {start_date} > {end_date}"
            )

        # 获取现有快照
        snapshots = BalanceSnapshot.get_entity_history(
            session=db,
            entity_type=entity_type,
            entity_id=entity_id,
            start_date=start_date,
            end_date=end_date
        )

        return [
            {
                "date": s.snapshot_date.isoformat(),
                "balance": float(s.balance),
                "total_debit": float(s.total_debit),
                "total_credit": float(s.total_credit),
                "currency": s.currency,
                "calculated_at": s.calculated_at.isoformat() if s.calculated_at else None
            }
            for s in snapshots
        ]

    @classmethod
    def validate_balance_consistency(
        cls,
        entity_type: str,
        entity_id: str,
        expected_balance: Decimal,
        db: Session,
        tolerance: Decimal = Decimal("0.01")
    ) -> Dict[str, Any]:
        """
        验证余额一致性

        比较实体的当前余额与 ledger 聚合计算的余额是否一致。

        Args:
            entity_type: 实体类型
            entity_id: 实体ID
            expected_balance: 期望余额 (来自 entity.balance 字段)
            db: 数据库会话
            tolerance: 容差 (默认 0.01)

        Returns:
            Dict: {
                "consistent": bool,
                "expected_balance": Decimal,
                "calculated_balance": Decimal,
                "difference": Decimal,
                "within_tolerance": bool
            }

        SoT Reference:
        - LEDGER_SOT.md v1.1 §2.4: 余额一致性保证
        """
        cls._validate_entity_type(entity_type)

        # 从 ledger 计算当前余额
        balance_data = cls.calculate_balance_from_ledger(
            entity_type=entity_type,
            entity_id=entity_id,
            as_of_date=date.today(),
            db=db
        )

        calculated_balance = balance_data["balance"]
        difference = abs(expected_balance - calculated_balance)
        within_tolerance = difference <= tolerance
        consistent = within_tolerance

        result = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "consistent": consistent,
            "expected_balance": float(expected_balance),
            "calculated_balance": float(calculated_balance),
            "difference": float(difference),
            "within_tolerance": within_tolerance,
            "tolerance": float(tolerance),
            "total_debit": float(balance_data["total_debit"]),
            "total_credit": float(balance_data["total_credit"])
        }

        if not consistent:
            logger.warning(
                f"Balance inconsistency detected for {entity_type}:{entity_id}: "
                f"expected={expected_balance}, calculated={calculated_balance}, diff={difference}"
            )

        return result

    @classmethod
    def batch_validate_consistency(
        cls,
        entities: List[Tuple[str, str, Decimal]],
        db: Session,
        tolerance: Decimal = Decimal("0.01")
    ) -> Dict[str, Any]:
        """
        批量验证余额一致性

        Args:
            entities: 实体列表，每项为 (entity_type, entity_id, expected_balance)
            db: 数据库会话
            tolerance: 容差

        Returns:
            Dict: {
                "total": int,
                "consistent": int,
                "inconsistent": int,
                "details": [...]
            }
        """
        results = {
            "total": len(entities),
            "consistent": 0,
            "inconsistent": 0,
            "details": []
        }

        for entity_type, entity_id, expected_balance in entities:
            try:
                validation = cls.validate_balance_consistency(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    expected_balance=expected_balance,
                    db=db,
                    tolerance=tolerance
                )
                if validation["consistent"]:
                    results["consistent"] += 1
                else:
                    results["inconsistent"] += 1
                results["details"].append(validation)
            except Exception as e:
                results["inconsistent"] += 1
                results["details"].append({
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "consistent": False,
                    "error": str(e)
                })

        return results

    @classmethod
    def fill_missing_snapshots(
        cls,
        entity_type: str,
        entity_id: str,
        start_date: date,
        end_date: date,
        db: Session,
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """
        填充缺失的快照

        为指定日期范围内缺失的日期创建快照。

        Args:
            entity_type: 实体类型
            entity_id: 实体ID
            start_date: 开始日期
            end_date: 结束日期
            db: 数据库会话
            currency: 币种

        Returns:
            Dict: {
                "total_days": int,
                "existing": int,
                "created": int,
                "failed": int
            }
        """
        cls._validate_entity_type(entity_type)

        if start_date > end_date:
            raise ValidationError(
                error_code=BusinessErrorCodes.INVALID_DATE_RANGE.code,
                message=f"开始日期不能晚于结束日期"
            )

        if end_date > date.today():
            end_date = date.today()

        # 获取现有快照日期
        existing_snapshots = BalanceSnapshot.get_entity_history(
            session=db,
            entity_type=entity_type,
            entity_id=entity_id,
            start_date=start_date,
            end_date=end_date
        )
        existing_dates = {s.snapshot_date for s in existing_snapshots}

        # 生成所有日期
        all_dates = []
        current_date = start_date
        while current_date <= end_date:
            all_dates.append(current_date)
            current_date += timedelta(days=1)

        results = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_days": len(all_dates),
            "existing": len(existing_dates),
            "created": 0,
            "failed": 0
        }

        # 填充缺失日期
        for d in all_dates:
            if d not in existing_dates:
                try:
                    cls.create_daily_snapshot(
                        entity_type=entity_type,
                        entity_id=entity_id,
                        snapshot_date=d,
                        db=db,
                        currency=currency
                    )
                    results["created"] += 1
                except Exception as e:
                    results["failed"] += 1
                    logger.warning(f"Failed to create snapshot for {d}: {e}")

        if results["created"] > 0:
            db.commit()

        return results

    # ========== 内部方法 ==========

    @classmethod
    def _validate_entity_type(cls, entity_type: str) -> None:
        """验证实体类型"""
        valid_types = [et.value for et in EntityType]
        if entity_type not in valid_types:
            raise ValidationError(
                error_code=BusinessErrorCodes.INVALID_STATUS.code,
                message=f"无效的实体类型: {entity_type}，有效值: {valid_types}"
            )

    @classmethod
    def _get_entities_with_ledger(
        cls,
        db: Session,
        entity_types: List[str],
        as_of_date: date
    ) -> List[Tuple[str, str]]:
        """
        获取有 ledger 记录的所有实体

        Returns:
            List of (entity_type, entity_id) tuples
        """
        end_of_day = datetime.combine(as_of_date, datetime.max.time())

        # 查询所有有记录的实体
        entities = db.query(
            LedgerEntry.entity_type,
            LedgerEntry.entity_id
        ).filter(
            and_(
                LedgerEntry.entity_type.in_(entity_types),
                LedgerEntry.entity_type.isnot(None),
                LedgerEntry.entity_id.isnot(None),
                LedgerEntry.entry_date <= end_of_day
            )
        ).distinct().all()

        return [(e.entity_type, e.entity_id) for e in entities]

    @classmethod
    def _calculate_balance_from_snapshot(
        cls,
        base_snapshot: BalanceSnapshot,
        target_date: date,
        db: Session
    ) -> Decimal:
        """
        从快照基础上增量计算余额

        Args:
            base_snapshot: 基准快照
            target_date: 目标日期
            db: 数据库会话

        Returns:
            Decimal: 目标日期的余额
        """
        if base_snapshot.snapshot_date >= target_date:
            return base_snapshot.balance

        # 计算快照日期到目标日期的增量
        start_of_next_day = datetime.combine(
            base_snapshot.snapshot_date + timedelta(days=1),
            datetime.min.time()
        )
        end_of_target_day = datetime.combine(target_date, datetime.max.time())

        # 聚合增量
        result = db.query(
            func.coalesce(
                func.sum(
                    case(
                        (LedgerEntry.direction == 'DEBIT', -func.abs(LedgerEntry.amount)),
                        (LedgerEntry.direction == 'CREDIT', LedgerEntry.amount),
                        else_=Decimal('0')
                    )
                ),
                Decimal('0')
            ).label('delta')
        ).filter(
            and_(
                LedgerEntry.entity_type == base_snapshot.entity_type,
                LedgerEntry.entity_id == base_snapshot.entity_id,
                LedgerEntry.entry_date >= start_of_next_day,
                LedgerEntry.entry_date <= end_of_target_day
            )
        ).first()

        delta = result.delta if result and result.delta else Decimal('0')

        return base_snapshot.balance + delta


# ========== 便捷函数 ==========

def create_daily_snapshot(
    entity_type: str,
    entity_id: str,
    snapshot_date: date,
    db: Session,
    currency: str = "USD"
) -> BalanceSnapshot:
    """创建每日快照的便捷函数"""
    return BalanceSnapshotService.create_daily_snapshot(
        entity_type=entity_type,
        entity_id=entity_id,
        snapshot_date=snapshot_date,
        db=db,
        currency=currency
    )


def get_balance_at_date(
    entity_type: str,
    entity_id: str,
    as_of_date: date,
    db: Session
) -> Optional[Decimal]:
    """获取历史余额的便捷函数"""
    return BalanceSnapshotService.get_balance_at_date(
        entity_type=entity_type,
        entity_id=entity_id,
        as_of_date=as_of_date,
        db=db
    )
