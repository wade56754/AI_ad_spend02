"""
Core utilities for safe operations.

SoT: MASTER.md v4.9 - 通用工具模块
"""
from .safe_access import safe_get, safe_getattr, safe_call, coalesce, safe_dict_get
from .money import (
    money_add,
    money_subtract,
    money_multiply,
    money_divide,
    to_display_float,
    calculate_percentage,
    safe_average,
    format_currency,
    MONEY_PRECISION,
)
from .db_locks import (
    lock_for_update,
    lock_multiple_for_update,
    lock_with_retry,
    ensure_locked,
)

__all__ = [
    # Safe access
    "safe_get",
    "safe_getattr",
    "safe_call",
    "coalesce",
    "safe_dict_get",
    # Money utilities
    "money_add",
    "money_subtract",
    "money_multiply",
    "money_divide",
    "to_display_float",
    "calculate_percentage",
    "safe_average",
    "format_currency",
    "MONEY_PRECISION",
    # Database locks
    "lock_for_update",
    "lock_multiple_for_update",
    "lock_with_retry",
    "ensure_locked",
]
