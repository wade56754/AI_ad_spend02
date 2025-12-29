"""
阶梯定价计算服务

参考文档:
- CORE_MODULES.md §4.5 阶梯价格规则
- LEDGER_SOT.md §7 PROJECT REVENUE 计算

业务规则:
- BR-PRJ-002: 阶梯价格按进粉数累计计算

Version: 1.0
Author: Claude Code
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from backend.models.core.project import Project


def calculate_revenue(
    conversions: int,
    price_rules: Optional[Dict[str, Any]],
    unit_price: Decimal
) -> Decimal:
    """
    计算收入

    Args:
        conversions: 进粉数量
        price_rules: 价格规则 JSON
        unit_price: 固定单价（fallback）

    Returns:
        计算后的收入金额

    Examples:
        >>> calculate_revenue(34, {"type": "tiered", "tiers": [
        ...     {"min": 0, "max": 15, "price": 100},
        ...     {"min": 16, "max": 30, "price": 120},
        ...     {"min": 31, "max": None, "price": 130}
        ... ]}, Decimal("0"))
        Decimal('3820.00')
    """
    if conversions <= 0:
        return Decimal("0.00")

    # 无阶梯规则，使用固定单价
    if not price_rules:
        return (Decimal(conversions) * unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    rule_type = price_rules.get("type", "fixed")

    if rule_type == "fixed":
        price = Decimal(str(price_rules.get("price", unit_price)))
        return (Decimal(conversions) * price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    elif rule_type == "tiered":
        return _calculate_tiered_revenue(conversions, price_rules.get("tiers", []))

    else:
        # 未知类型，回退到固定单价
        return (Decimal(conversions) * unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _calculate_tiered_revenue(conversions: int, tiers: List[Dict[str, Any]]) -> Decimal:
    """
    阶梯定价计算

    算法:
    1. 按阶梯从低到高遍历
    2. 每个阶梯计算该阶梯内的数量 × 单价
    3. 累加所有阶梯金额

    示例（加拿大TK规则）:
    - 0-15: $100
    - 16-30: $120
    - 31+: $130

    34个进粉 = 15*100 + 15*120 + 4*130 = 1500 + 1800 + 520 = $3820

    注意：阶梯是"累进"计算，不是"全额"计算
    即：34个进粉的收入是分段计算的，不是34*130
    """
    if not tiers:
        return Decimal("0.00")

    # 按 min 排序
    sorted_tiers = sorted(tiers, key=lambda t: t.get("min", 0))

    total = Decimal("0.00")
    remaining = conversions

    for tier in sorted_tiers:
        tier_min = tier.get("min", 0)
        tier_max = tier.get("max")  # None 表示无上限
        tier_price = Decimal(str(tier.get("price", 0)))

        if remaining <= 0:
            break

        # 计算该阶梯的数量上限
        if tier_max is None:
            tier_count = remaining
        else:
            tier_range = tier_max - tier_min + 1
            tier_count = min(remaining, tier_range)

        # 累加金额
        total += Decimal(tier_count) * tier_price
        remaining -= tier_count

    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_cost(
    real_spend: Decimal,
    fee_rate: Decimal
) -> Decimal:
    """
    计算成本（含手续费）

    公式: cost = real_spend × (1 + fee_rate)

    Args:
        real_spend: 真实消耗
        fee_rate: 手续费率（如 0.08 = 8%）

    Returns:
        总成本

    Examples:
        >>> calculate_cost(Decimal("1000.00"), Decimal("0.08"))
        Decimal('1080.00')
    """
    if real_spend <= 0:
        return Decimal("0.00")

    cost = real_spend * (1 + fee_rate)
    return cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_profit(
    revenue: Decimal,
    cost: Decimal
) -> Decimal:
    """
    计算利润

    公式: profit = revenue - cost

    Args:
        revenue: 收入
        cost: 成本（含手续费）

    Returns:
        利润金额（可能为负数）
    """
    return (revenue - cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_profit_margin(
    revenue: Decimal,
    cost: Decimal
) -> Decimal:
    """
    计算利润率

    公式: profit_margin = (revenue - cost) / revenue * 100

    Args:
        revenue: 收入
        cost: 成本

    Returns:
        利润率百分比（如 25.00 表示 25%）
    """
    if revenue <= 0:
        return Decimal("0.00")

    profit = revenue - cost
    margin = (profit / revenue) * 100
    return margin.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_project_price_info(db: Session, project_id: int) -> Dict[str, Any]:
    """
    获取项目定价信息

    Returns:
        {
            "unit_price": Decimal,
            "price_rules": dict or None,
            "currency": str
        }
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    return {
        "unit_price": project.unit_price or Decimal("0.00"),
        "price_rules": project.price_rules,
        "currency": getattr(project, 'default_currency', None) or "USD"
    }


def calculate_daily_report_financials(
    conversions: int,
    real_spend: Decimal,
    price_rules: Optional[Dict[str, Any]],
    unit_price: Decimal,
    fee_rate: Decimal
) -> Dict[str, Decimal]:
    """
    计算日报的财务指标

    Args:
        conversions: 进粉数量
        real_spend: 真实消耗
        price_rules: 价格规则 JSON
        unit_price: 固定单价
        fee_rate: 手续费率

    Returns:
        {
            "revenue": 收入,
            "cost": 成本（含手续费）,
            "profit": 利润,
            "profit_margin": 利润率
        }
    """
    revenue = calculate_revenue(conversions, price_rules, unit_price)
    cost = calculate_cost(real_spend, fee_rate)
    profit = calculate_profit(revenue, cost)
    profit_margin = calculate_profit_margin(revenue, cost)

    return {
        "revenue": revenue,
        "cost": cost,
        "profit": profit,
        "profit_margin": profit_margin
    }
