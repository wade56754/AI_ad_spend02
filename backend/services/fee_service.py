"""
FeeService - 手续费计算服务
Version: 1.0 (Financial SoT Phase 4)
Author: Claude协作开发

SoT 对齐:
- FINANCIAL_REFACTOR_PLAN.md Phase 4
- LEDGER_SOT.md v1.1: cost = real_spend + fee
- DAILY_REPORT_SOT.md: fee = real_spend × fee_rate

核心功能:
1. 手续费计算 (PERCENTAGE/FIXED)
2. 含费金额计算 (gross_amount)
3. 费率配置管理
4. 历史费率查询 (预留扩展)
"""

from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Dict, Optional, Any, Tuple
from uuid import UUID
import logging

from sqlalchemy.orm import Session

from backend.models.finance.supplier import Supplier
from backend.core.error_codes import FeeErrorCodes
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class FeeType:
    """费率类型常量"""
    PERCENTAGE = "PERCENTAGE"  # 百分比 (fee = spend × fee_rate)
    FIXED = "FIXED"           # 固定金额 (fee = fee_rate)


class FeeService:
    """
    手续费计算服务

    核心职责:
    - 计算消耗手续费 (PERCENTAGE 或 FIXED)
    - 计算含费金额 (gross_amount = spend + fee)
    - 管理供应商费率配置
    - 提供历史费率查询能力 (预留)

    SoT Ref:
    - FINANCIAL_REFACTOR_PLAN.md Phase 4
    - LEDGER_SOT.md v1.1 §2.2.2: cost = real_spend + fee
    """

    # 精度配置
    DECIMAL_PLACES = 2  # 金额保留2位小数
    RATE_DECIMAL_PLACES = 4  # 费率保留4位小数

    # 默认费率
    DEFAULT_FEE_RATE = Decimal("0.10")  # 10%
    DEFAULT_FEE_TYPE = FeeType.PERCENTAGE

    # 费率范围
    MIN_FEE_RATE = Decimal("0")
    MAX_FEE_RATE = Decimal("1")  # 100%

    def __init__(self, db: Session):
        self.db = db

    # ========== 手续费计算 ==========

    def calculate_fee(
        self,
        spend_amount: Decimal,
        supplier_id: int,
        event_date: Optional[date] = None
    ) -> Decimal:
        """
        计算手续费

        Args:
            spend_amount: 消耗金额
            supplier_id: 供应商ID
            event_date: 事件日期 (用于获取历史费率，可选)

        Returns:
            Decimal: 手续费金额

        Raises:
            ResourceNotFoundError: 供应商不存在
            ValidationError: 消耗金额无效

        SoT Ref: DAILY_REPORT_SOT.md - fee = real_spend × fee_rate
        """
        # 验证消耗金额
        if spend_amount < 0:
            raise ValidationError(
                message="消耗金额不能为负数",
                error=FeeErrorCodes.NEGATIVE_SPEND_AMOUNT
            )

        # 获取供应商
        supplier = self.db.query(Supplier).filter(
            Supplier.id == supplier_id
        ).first()

        if not supplier:
            raise ResourceNotFoundError(
                message="供应商不存在",
                error=FeeErrorCodes.SUPPLIER_NOT_FOUND
            )

        # 获取费率配置
        fee_rate = self._get_effective_fee_rate(supplier, event_date)
        fee_type = supplier.fee_type or self.DEFAULT_FEE_TYPE

        # 计算手续费
        try:
            if fee_type == FeeType.PERCENTAGE:
                fee = spend_amount * fee_rate
            elif fee_type == FeeType.FIXED:
                fee = fee_rate
            else:
                # 默认使用百分比
                fee = spend_amount * fee_rate

            # 四舍五入到2位小数
            return fee.quantize(
                Decimal(f"0.{'0' * self.DECIMAL_PLACES}"),
                rounding=ROUND_HALF_UP
            )
        except (InvalidOperation, OverflowError) as e:
            logger.error(f"手续费计算失败: spend={spend_amount}, rate={fee_rate}, error={e}")
            raise BusinessLogicError(
                message="手续费计算失败",
                error=FeeErrorCodes.CALCULATION_ERROR
            )

    def calculate_fee_by_rate(
        self,
        spend_amount: Decimal,
        fee_rate: Decimal,
        fee_type: str = FeeType.PERCENTAGE
    ) -> Decimal:
        """
        根据指定费率计算手续费 (不查询数据库)

        Args:
            spend_amount: 消耗金额
            fee_rate: 费率
            fee_type: 费率类型 (PERCENTAGE/FIXED)

        Returns:
            Decimal: 手续费金额

        Raises:
            ValidationError: 参数无效
        """
        # 验证消耗金额
        if spend_amount < 0:
            raise ValidationError(
                message="消耗金额不能为负数",
                error=FeeErrorCodes.NEGATIVE_SPEND_AMOUNT
            )

        # 验证费率类型 (先验证类型，再验证范围)
        if fee_type not in [FeeType.PERCENTAGE, FeeType.FIXED]:
            raise ValidationError(
                message="费率类型无效，必须是PERCENTAGE或FIXED",
                error=FeeErrorCodes.INVALID_FEE_TYPE
            )

        # 验证费率
        # PERCENTAGE: 0-1 (0%-100%)
        # FIXED: >= 0 (固定金额)
        if fee_type == FeeType.PERCENTAGE:
            if fee_rate < self.MIN_FEE_RATE or fee_rate > self.MAX_FEE_RATE:
                raise ValidationError(
                    message=f"费率无效，必须在{self.MIN_FEE_RATE}-{self.MAX_FEE_RATE}之间",
                    error=FeeErrorCodes.INVALID_FEE_RATE
                )
        else:  # FIXED
            if fee_rate < Decimal("0"):
                raise ValidationError(
                    message="固定费用不能为负数",
                    error=FeeErrorCodes.INVALID_FEE_RATE
                )

        try:
            if fee_type == FeeType.PERCENTAGE:
                fee = spend_amount * fee_rate
            else:
                fee = fee_rate

            return fee.quantize(
                Decimal(f"0.{'0' * self.DECIMAL_PLACES}"),
                rounding=ROUND_HALF_UP
            )
        except (InvalidOperation, OverflowError) as e:
            logger.error(f"手续费计算失败: {e}")
            raise BusinessLogicError(
                message="手续费计算失败",
                error=FeeErrorCodes.CALCULATION_ERROR
            )

    def calculate_gross_amount(
        self,
        spend_amount: Decimal,
        fee_amount: Decimal
    ) -> Decimal:
        """
        计算含费金额 (gross_amount)

        Args:
            spend_amount: 消耗金额
            fee_amount: 手续费金额

        Returns:
            Decimal: 含费金额 (spend + fee)

        SoT Ref: LEDGER_SOT.md v1.1 - gross_amount = amount + fee_amount
        """
        try:
            gross = spend_amount + fee_amount
            return gross.quantize(
                Decimal(f"0.{'0' * self.DECIMAL_PLACES}"),
                rounding=ROUND_HALF_UP
            )
        except (InvalidOperation, OverflowError) as e:
            logger.error(f"含费金额计算失败: {e}")
            raise BusinessLogicError(
                message="含费金额计算失败",
                error=FeeErrorCodes.CALCULATION_ERROR
            )

    def calculate_cost(
        self,
        real_spend: Decimal,
        supplier_id: int,
        event_date: Optional[date] = None
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        计算成本 (一站式方法)

        Args:
            real_spend: 真实消耗
            supplier_id: 供应商ID
            event_date: 事件日期

        Returns:
            Tuple[Decimal, Decimal, Decimal]: (fee, cost, fee_rate)
            - fee: 手续费
            - cost: 总成本 (real_spend + fee)
            - fee_rate: 使用的费率

        SoT Ref: LEDGER_SOT.md v1.1 §2.2.2 - cost = real_spend + fee
        """
        # 获取供应商
        supplier = self.db.query(Supplier).filter(
            Supplier.id == supplier_id
        ).first()

        if not supplier:
            raise ResourceNotFoundError(
                message="供应商不存在",
                error=FeeErrorCodes.SUPPLIER_NOT_FOUND
            )

        # 获取费率
        fee_rate = self._get_effective_fee_rate(supplier, event_date)

        # 计算手续费
        fee = self.calculate_fee_by_rate(
            spend_amount=real_spend,
            fee_rate=fee_rate,
            fee_type=supplier.fee_type or self.DEFAULT_FEE_TYPE
        )

        # 计算成本
        cost = self.calculate_gross_amount(real_spend, fee)

        return fee, cost, fee_rate

    # ========== 费率管理 ==========

    def get_effective_fee_rate(
        self,
        supplier_id: int,
        as_of_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取生效费率

        Args:
            supplier_id: 供应商ID
            as_of_date: 截止日期 (可选，默认当天)

        Returns:
            Dict: 费率信息
        """
        supplier = self.db.query(Supplier).filter(
            Supplier.id == supplier_id
        ).first()

        if not supplier:
            raise ResourceNotFoundError(
                message="供应商不存在",
                error=FeeErrorCodes.SUPPLIER_NOT_FOUND
            )

        fee_rate = self._get_effective_fee_rate(supplier, as_of_date)

        return {
            "supplier_id": supplier_id,
            "supplier_name": supplier.name,
            "fee_rate": str(fee_rate),
            "fee_type": supplier.fee_type or self.DEFAULT_FEE_TYPE,
            "platform": supplier.platform,
            "as_of_date": (as_of_date or date.today()).isoformat(),
            "is_default": supplier.fee_rate is None
        }

    def update_fee_rate(
        self,
        supplier_id: int,
        new_rate: Decimal,
        fee_type: Optional[str] = None,
        user_id: Optional[UUID] = None,
        effective_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        更新供应商费率

        Args:
            supplier_id: 供应商ID
            new_rate: 新费率
            fee_type: 费率类型 (可选，不传则保持原值)
            user_id: 操作用户ID
            effective_date: 生效日期 (预留，当前立即生效)

        Returns:
            Dict: 更新结果

        Raises:
            ResourceNotFoundError: 供应商不存在
            ValidationError: 费率无效
        """
        # 验证费率
        if new_rate < self.MIN_FEE_RATE or new_rate > self.MAX_FEE_RATE:
            raise ValidationError(
                message=f"费率无效，必须在{self.MIN_FEE_RATE}-{self.MAX_FEE_RATE}之间",
                error=FeeErrorCodes.INVALID_FEE_RATE
            )

        # 验证费率类型
        if fee_type and fee_type not in [FeeType.PERCENTAGE, FeeType.FIXED]:
            raise ValidationError(
                message="费率类型无效，必须是PERCENTAGE或FIXED",
                error=FeeErrorCodes.INVALID_FEE_TYPE
            )

        # 获取供应商
        supplier = self.db.query(Supplier).filter(
            Supplier.id == supplier_id
        ).first()

        if not supplier:
            raise ResourceNotFoundError(
                message="供应商不存在",
                error=FeeErrorCodes.SUPPLIER_NOT_FOUND
            )

        # 记录旧值
        old_rate = supplier.fee_rate
        old_type = supplier.fee_type

        try:
            # 更新费率
            supplier.fee_rate = new_rate
            if fee_type:
                supplier.fee_type = fee_type

            self.db.commit()
            self.db.refresh(supplier)

            logger.info(
                f"费率更新成功: supplier_id={supplier_id}, "
                f"old_rate={old_rate} -> new_rate={new_rate}, "
                f"old_type={old_type} -> new_type={fee_type or old_type}, "
                f"user_id={user_id}"
            )

            return {
                "supplier_id": supplier_id,
                "supplier_name": supplier.name,
                "old_fee_rate": str(old_rate) if old_rate else None,
                "new_fee_rate": str(new_rate),
                "old_fee_type": old_type,
                "new_fee_type": fee_type or supplier.fee_type,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "updated_by": str(user_id) if user_id else None
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"费率更新失败: {e}")
            raise BusinessLogicError(
                message="费率更新失败",
                error=FeeErrorCodes.UPDATE_FAILED
            )

    # ========== 批量计算 ==========

    def batch_calculate_fees(
        self,
        items: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        """
        批量计算手续费

        Args:
            items: 计算项列表，每项包含:
                - spend_amount: Decimal
                - supplier_id: int
                - event_date: Optional[date]

        Returns:
            list[Dict]: 计算结果列表
        """
        results = []

        for item in items:
            try:
                spend_amount = Decimal(str(item.get("spend_amount", 0)))
                supplier_id = item.get("supplier_id")
                event_date = item.get("event_date")

                fee, cost, fee_rate = self.calculate_cost(
                    real_spend=spend_amount,
                    supplier_id=supplier_id,
                    event_date=event_date
                )

                results.append({
                    "supplier_id": supplier_id,
                    "spend_amount": str(spend_amount),
                    "fee_amount": str(fee),
                    "cost": str(cost),
                    "fee_rate": str(fee_rate),
                    "success": True,
                    "error": None
                })

            except Exception as e:
                results.append({
                    "supplier_id": item.get("supplier_id"),
                    "spend_amount": str(item.get("spend_amount", 0)),
                    "fee_amount": None,
                    "cost": None,
                    "fee_rate": None,
                    "success": False,
                    "error": str(e)
                })

        return results

    # ========== 私有方法 ==========

    def _get_effective_fee_rate(
        self,
        supplier: Supplier,
        as_of_date: Optional[date] = None
    ) -> Decimal:
        """
        获取供应商的生效费率

        当前实现: 直接返回 supplier.fee_rate
        未来扩展: 支持按日期查询历史费率表

        Args:
            supplier: 供应商对象
            as_of_date: 截止日期 (预留)

        Returns:
            Decimal: 费率
        """
        # 当前简单实现: 直接返回配置的费率或默认值
        # TODO: 未来可扩展为按日期查询历史费率表
        if supplier.fee_rate is not None:
            return Decimal(str(supplier.fee_rate))
        return self.DEFAULT_FEE_RATE


# ========== 便捷函数 ==========

def get_fee_service(db: Session) -> FeeService:
    """获取 FeeService 实例"""
    return FeeService(db)


def calculate_fee(
    db: Session,
    spend_amount: Decimal,
    supplier_id: int,
    event_date: Optional[date] = None
) -> Decimal:
    """计算手续费 (便捷函数)"""
    service = FeeService(db)
    return service.calculate_fee(spend_amount, supplier_id, event_date)


def calculate_cost(
    db: Session,
    real_spend: Decimal,
    supplier_id: int,
    event_date: Optional[date] = None
) -> Tuple[Decimal, Decimal, Decimal]:
    """计算成本 (便捷函数)"""
    service = FeeService(db)
    return service.calculate_cost(real_spend, supplier_id, event_date)
