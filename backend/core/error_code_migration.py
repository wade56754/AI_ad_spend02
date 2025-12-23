"""
错误码迁移映射
Version: 1.0
Author: Claude协作开发

此文件定义了旧错误码到新标准错误码的映射关系。
用于批量迁移遗留代码中的非标准错误码。
"""

from typing import Dict

# ==============================================
# 旧错误码 → 新标准错误码映射
# ==============================================

# 格式: "旧错误码" → "新标准错误码"
# 标准前缀: AUTH_, BIZ_, SYS_, DB_, VALIDATION_, STATE_, TREND_, PROFIT_
#
# 注意: SYS_003, SYS_004, SYS_005 在新旧标准中含义不同，需要人工审查:
# - 旧: SYS_003=权限不足, SYS_004=资源不存在, SYS_005=资源冲突
# - 新: SYS_003=请求超时, SYS_004=请求过于频繁
# 这些代码不自动迁移，需要逐个审查上下文

ERROR_CODE_MIGRATION_MAP: Dict[str, str] = {
    # =====================
    # 非标准通用错误码 (明确需要迁移)
    # =====================
    "SYS_429": "SYS_004",        # 限流 → SYS_004
    "SYS_503": "SYS_002",        # 服务不可用 → SYS_002
    "SYS_CONFIG": "SYS_001",     # 配置错误 → SYS_001
    "SEC_ERROR": "AUTH_500",     # 安全错误 → AUTH_500
    "BIZ_ERROR": "BIZ_001",      # 业务错误 → BIZ_001

    # =====================
    # 非标准验证错误码
    # =====================
    "VAL_001": "VALIDATION_001",      # 必填字段缺失
    "VAL_002": "VALIDATION_002",      # 格式无效
    "VAL_003": "VALIDATION_003",      # 邮箱格式无效
    "VAL_004": "VALIDATION_004",      # 电话格式无效
    "VAL_005": "VALIDATION_005",      # 值超出范围
    "VAL-001": "VALIDATION_001",      # 连字符格式也需要映射
    "VAL-002": "VALIDATION_002",
    "VAL-003": "VALIDATION_003",
    "VAL-004": "VALIDATION_004",
    "VAL-005": "VALIDATION_005",

    # =====================
    # 非标准状态错误码
    # =====================
    "STATE_001": "STATE_400",         # 非法状态流转
    "STATE-001": "STATE_400",
    "STATE_002": "STATE_400",         # 非法状态流转
    "STATE-002": "STATE_400",

    # =====================
    # 非标准内部错误码
    # =====================
    "INTERNAL_001": "SYS_001",        # 内部错误
    "INTERNAL_ERROR": "SYS_001",
    "INTERNAL-ERROR": "SYS_001",

    # =====================
    # 已标准错误码 (保持不变)
    # =====================
    "AUTH_401": "AUTH_401",
    "AUTH_500": "AUTH_500",
}


# ==============================================
# 需要迁移的非标准错误码
# ==============================================

DEPRECATED_ERROR_CODES = [
    # 可自动迁移
    "SYS_429",      # 应使用 RateLimitError + SYS_004
    "SYS_503",      # 应使用 ExternalServiceError + SYS_002
    "SYS_CONFIG",   # 应使用 ConfigurationError + SYS_001
    "SEC_ERROR",    # 应使用 SecurityError + AUTH_500
    "BIZ_ERROR",    # 应使用 BusinessLogicError + 具体 BIZ_xxx
    "VAL_001",      # 应使用 ValidationError + VALIDATION_001
    "VAL_002",      # 应使用 ValidationError + VALIDATION_002
    "VAL-001",
    "VAL-002",
    "STATE_001",    # 应使用 StateTransitionError + STATE_400
    "STATE-001",
    "STATE_002",
    "STATE-002",
    "INTERNAL_001", # 应使用 SYS_001
    "INTERNAL_ERROR",
    "INTERNAL-ERROR",
]


# ==============================================
# 标准错误码前缀
# ==============================================

VALID_ERROR_CODE_PREFIXES = [
    "AUTH_",        # 认证/授权错误 (001-999)
    "BIZ_",         # 业务逻辑错误 (001-999)
    "SYS_",         # 系统错误 (001-004)
    "DB_",          # 数据库错误 (001-005)
    "VALIDATION_",  # 参数验证错误 (001-199)
    "STATE_",       # 状态机错误 (400-409)
    "TREND_",       # 趋势风控错误 (001-019)
    "PROFIT_",      # 利润报表错误 (001-008)
]


def migrate_error_code(old_code: str) -> str:
    """
    迁移旧错误码到新标准格式

    Args:
        old_code: 旧错误码

    Returns:
        新标准错误码
    """
    return ERROR_CODE_MIGRATION_MAP.get(old_code, old_code)


def is_standard_error_code(code: str) -> bool:
    """
    检查是否为标准错误码

    Args:
        code: 错误码字符串

    Returns:
        True 如果是标准格式
    """
    return any(code.startswith(prefix) for prefix in VALID_ERROR_CODE_PREFIXES)


def is_deprecated_error_code(code: str) -> bool:
    """
    检查是否为已废弃的错误码

    Args:
        code: 错误码字符串

    Returns:
        True 如果已废弃
    """
    return code in DEPRECATED_ERROR_CODES


def get_migration_suggestion(old_code: str) -> str:
    """
    获取错误码迁移建议

    Args:
        old_code: 旧错误码

    Returns:
        迁移建议字符串
    """
    if old_code in ERROR_CODE_MIGRATION_MAP:
        new_code = ERROR_CODE_MIGRATION_MAP[old_code]
        return f"请将 '{old_code}' 替换为 '{new_code}'"
    elif is_standard_error_code(old_code):
        return f"'{old_code}' 已是标准格式，无需迁移"
    else:
        return f"'{old_code}' 为未知错误码，请参考 ERROR_CODES_SOT.md 选择合适的标准错误码"
