"""
Money/Decimal precision utilities.

解决问题: BE-P0-3 - Decimal/float 混用导致精度丢失
SoT: MASTER.md v4.9 - 资金计算必须使用 Decimal
SoT: BR-FIN-001 - 所有金额必须保留 2 位小数

使用示例:
    from backend.core.utils import money_subtract, to_display_float

    # 计算差额 (内部使用 Decimal)
    balance = money_subtract(total_topup, total_spend)

    # API 响应时转换
    response = {"balance": to_display_float(balance)}
"""
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Union, Optional

# 金额精度: 2 位小数
MONEY_PRECISION = Decimal("0.01")

# 百分比精度: 4 位小数
PERCENT_PRECISION = Decimal("0.0001")


def _to_decimal(value: Union[Decimal, float, int, str, None]) -> Decimal:
    """
    将值转换为 Decimal，处理各种输入类型。

    Args:
        value: 要转换的值

    Returns:
        Decimal 值

    Raises:
        ValueError: 无法转换的值
    """
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        # 使用字符串转换避免浮点精度问题
        return Decimal(str(value))
    if isinstance(value, str):
        try:
            return Decimal(value)
        except InvalidOperation:
            raise ValueError(f"Cannot convert '{value}' to Decimal")
    raise ValueError(f"Unsupported type for Decimal conversion: {type(value)}")


def money_add(*amounts: Union[Decimal, float, int, str, None]) -> Decimal:
    """
    安全相加金额，保持精度。

    Args:
        *amounts: 要相加的金额

    Returns:
        量化到 2 位小数的和

    Examples:
        >>> money_add(Decimal("100.10"), Decimal("50.25"))
        Decimal('150.35')
        >>> money_add(100.1, 50.25, 0.05)
        Decimal('150.40')
    """
    total = sum((_to_decimal(a) for a in amounts), Decimal("0"))
    return total.quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)


def money_subtract(
    a: Union[Decimal, float, int, str, None],
    b: Union[Decimal, float, int, str, None]
) -> Decimal:
    """
    安全相减金额，保持精度。

    Args:
        a: 被减数
        b: 减数

    Returns:
        量化到 2 位小数的差

    Examples:
        >>> money_subtract(Decimal("100.00"), Decimal("30.50"))
        Decimal('69.50')
        >>> money_subtract(100.1, 0.1)  # 避免浮点误差
        Decimal('100.00')
    """
    result = _to_decimal(a) - _to_decimal(b)
    return result.quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)


def money_multiply(
    amount: Union[Decimal, float, int, str, None],
    factor: Union[Decimal, float, int, str, None]
) -> Decimal:
    """
    金额乘法，保持精度。

    Args:
        amount: 金额
        factor: 乘数

    Returns:
        量化到 2 位小数的积

    Examples:
        >>> money_multiply(Decimal("100.00"), Decimal("1.05"))
        Decimal('105.00')
    """
    result = _to_decimal(amount) * _to_decimal(factor)
    return result.quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)


def money_divide(
    amount: Union[Decimal, float, int, str, None],
    divisor: Union[Decimal, float, int, str, None],
    default: Decimal = Decimal("0")
) -> Decimal:
    """
    金额除法，保持精度，处理除零。

    Args:
        amount: 被除数
        divisor: 除数
        default: 除数为零时的默认值

    Returns:
        量化到 2 位小数的商，或默认值

    Examples:
        >>> money_divide(Decimal("100.00"), Decimal("3"))
        Decimal('33.33')
        >>> money_divide(Decimal("100.00"), Decimal("0"))
        Decimal('0')
    """
    divisor_dec = _to_decimal(divisor)
    if divisor_dec == 0:
        return default
    result = _to_decimal(amount) / divisor_dec
    return result.quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)


def to_display_float(amount: Union[Decimal, float, int, str, None]) -> float:
    """
    将金额转换为用于 API 响应的 float。

    注意: 仅在需要 JSON 序列化时使用，内部计算应使用 Decimal。

    Args:
        amount: 金额

    Returns:
        float 值

    Examples:
        >>> to_display_float(Decimal("100.105"))
        100.11
    """
    quantized = _to_decimal(amount).quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)
    return float(quantized)


def calculate_percentage(
    part: Union[Decimal, float, int, str, None],
    total: Union[Decimal, float, int, str, None],
    default: Decimal = Decimal("0")
) -> Decimal:
    """
    计算百分比，保持精度。

    Args:
        part: 部分值
        total: 总值
        default: 总值为零时的默认值

    Returns:
        百分比值 (0-100)，4 位小数精度

    Examples:
        >>> calculate_percentage(Decimal("25"), Decimal("100"))
        Decimal('25.0000')
        >>> calculate_percentage(Decimal("1"), Decimal("3"))
        Decimal('33.3333')
    """
    total_dec = _to_decimal(total)
    if total_dec == 0:
        return default
    result = (_to_decimal(part) / total_dec) * Decimal("100")
    return result.quantize(PERCENT_PRECISION, rounding=ROUND_HALF_UP)


def safe_average(
    values: list,
    default: Decimal = Decimal("0")
) -> Decimal:
    """
    安全计算平均值。

    解决问题: FE-P0-1 对应的后端计算

    Args:
        values: 值列表
        default: 列表为空时的默认值

    Returns:
        平均值

    Examples:
        >>> safe_average([Decimal("10"), Decimal("20"), Decimal("30")])
        Decimal('20.00')
        >>> safe_average([])
        Decimal('0')
    """
    if not values:
        return default
    total = sum((_to_decimal(v) for v in values), Decimal("0"))
    return money_divide(total, len(values), default)


def format_currency(
    amount: Union[Decimal, float, int, str, None],
    currency: str = "CNY",
    show_symbol: bool = True
) -> str:
    """
    格式化金额为货币字符串。

    Args:
        amount: 金额
        currency: 货币代码
        show_symbol: 是否显示货币符号

    Returns:
        格式化的字符串

    Examples:
        >>> format_currency(Decimal("1234.56"))
        '¥1,234.56'
        >>> format_currency(Decimal("1234.56"), show_symbol=False)
        '1,234.56'
    """
    symbols = {"CNY": "¥", "USD": "$", "EUR": "€"}
    symbol = symbols.get(currency, currency + " ")

    quantized = _to_decimal(amount).quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)
    # 格式化为千位分隔
    formatted = f"{quantized:,.2f}"

    if show_symbol:
        return f"{symbol}{formatted}"
    return formatted
