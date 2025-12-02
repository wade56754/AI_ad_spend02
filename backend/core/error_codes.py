"""
统一错误码定义
Version: 1.0
Author: Claude协作开发

错误码命名规则:
- AUTH_xxx: 认证/授权错误
- BIZ_xxx: 业务逻辑错误
- SYS_xxx: 系统错误
- DB_xxx: 数据库错误
- VALIDATION_xxx: 参数验证错误
"""

from typing import Dict, Any


class ErrorCode:
    """错误码基类"""
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "status_code": self.status_code
        }


# ============================================
# 认证错误码 (AUTH_xxx)
# ============================================

class AuthErrorCodes:
    """认证相关错误码"""

    # 登录相关 (001-099)
    INVALID_CREDENTIALS = ErrorCode(
        "AUTH_001",
        "用户名或密码错误",
        401
    )

    ACCOUNT_DISABLED = ErrorCode(
        "AUTH_002",
        "账户已被禁用",
        403
    )

    TOKEN_REVOKED = ErrorCode(
        "AUTH_003",
        "令牌已被撤销",
        401
    )

    USER_NOT_FOUND = ErrorCode(
        "AUTH_004",
        "用户不存在或已被禁用",
        404
    )

    TOKEN_REFRESH_FAILED = ErrorCode(
        "AUTH_005",
        "令牌刷新失败",
        401
    )

    # 注册相关 (100-199)
    EMAIL_ALREADY_EXISTS = ErrorCode(
        "AUTH_100",
        "邮箱已被注册",
        400
    )

    USERNAME_ALREADY_EXISTS = ErrorCode(
        "AUTH_101",
        "用户名已被使用",
        400
    )

    REGISTER_FAILED = ErrorCode(
        "AUTH_102",
        "注册失败，请稍后重试",
        500
    )

    # 密码相关 (200-299)
    PASSWORD_TOO_SHORT = ErrorCode(
        "AUTH_200",
        "密码长度至少8位",
        400
    )

    PASSWORD_MISSING_DIGIT = ErrorCode(
        "AUTH_201",
        "密码必须包含至少一个数字",
        400
    )

    PASSWORD_MISSING_LETTER = ErrorCode(
        "AUTH_202",
        "密码必须包含至少一个字母",
        400
    )

    PASSWORD_MISSING_SPECIAL = ErrorCode(
        "AUTH_203",
        "密码必须包含至少一个特殊字符",
        400
    )

    OLD_PASSWORD_WRONG = ErrorCode(
        "AUTH_204",
        "旧密码错误",
        400
    )

    RESET_TOKEN_INVALID = ErrorCode(
        "AUTH_205",
        "重置令牌无效或已过期",
        400
    )

    PASSWORD_CHANGE_FAILED = ErrorCode(
        "AUTH_206",
        "密码修改失败",
        500
    )

    # 邮箱验证 (300-399)
    EMAIL_NOT_VERIFIED = ErrorCode(
        "AUTH_300",
        "邮箱未验证",
        403
    )

    EMAIL_VERIFICATION_FAILED = ErrorCode(
        "AUTH_301",
        "邮箱验证失败",
        400
    )

    EMAIL_ALREADY_VERIFIED = ErrorCode(
        "AUTH_302",
        "邮箱已验证",
        400
    )

    # Token相关 (400-499)
    TOKEN_MISSING = ErrorCode(
        "AUTH_400",
        "未提供认证令牌",
        401
    )

    TOKEN_INVALID = ErrorCode(
        "AUTH_401",
        "无效的认证令牌",
        401
    )

    TOKEN_EXPIRED = ErrorCode(
        "AUTH_402",
        "令牌已过期",
        401
    )

    # 权限相关 (500-599)
    PERMISSION_DENIED = ErrorCode(
        "AUTH_500",
        "权限不足",
        403
    )

    ROLE_NOT_ALLOWED = ErrorCode(
        "AUTH_501",
        "角色权限不足",
        403
    )

    # 通用认证错误 (900-999)
    LOGIN_FAILED = ErrorCode(
        "AUTH_900",
        "登录失败，请稍后重试",
        500
    )

    LOGOUT_FAILED = ErrorCode(
        "AUTH_901",
        "登出失败",
        500
    )

    AUTHENTICATION_ERROR = ErrorCode(
        "AUTH_999",
        "认证失败",
        401
    )


# ============================================
# 业务错误码 (BIZ_xxx)
# ============================================

class BusinessErrorCodes:
    """业务逻辑错误码"""

    # 通用业务错误 (001-099)
    INVALID_OPERATION = ErrorCode(
        "BIZ_001",
        "无效的操作",
        400
    )

    RESOURCE_NOT_FOUND = ErrorCode(
        "BIZ_002",
        "资源不存在",
        404
    )

    RESOURCE_ALREADY_EXISTS = ErrorCode(
        "BIZ_003",
        "资源已存在",
        409
    )

    # 金额相关 (100-199)
    INVALID_AMOUNT = ErrorCode(
        "BIZ_100",
        "金额无效",
        400
    )

    INSUFFICIENT_BALANCE = ErrorCode(
        "BIZ_101",
        "余额不足",
        400
    )

    # 日期相关 (200-299)
    INVALID_DATE_RANGE = ErrorCode(
        "BIZ_200",
        "日期范围无效",
        400
    )

    DATE_IN_FUTURE = ErrorCode(
        "BIZ_201",
        "日期不能为未来",
        400
    )

    # 状态相关 (300-399)
    INVALID_STATUS = ErrorCode(
        "BIZ_300",
        "状态无效",
        400
    )

    STATUS_TRANSITION_NOT_ALLOWED = ErrorCode(
        "BIZ_301",
        "状态转换不允许",
        400
    )

    # 用户管理相关 (400-499)
    UPDATE_PROFILE_FAILED = ErrorCode(
        "BIZ_400",
        "更新用户资料失败",
        500
    )

    ACTIVATE_USER_FAILED = ErrorCode(
        "BIZ_401",
        "激活用户失败",
        500
    )

    DEACTIVATE_USER_FAILED = ErrorCode(
        "BIZ_402",
        "停用用户失败",
        500
    )

    # 通用业务操作失败 (900-999)
    OPERATION_FAILED = ErrorCode(
        "BIZ_900",
        "操作失败",
        500
    )

    GET_SESSIONS_FAILED = ErrorCode(
        "BIZ_901",
        "获取会话列表失败",
        500
    )

    REVOKE_SESSION_FAILED = ErrorCode(
        "BIZ_902",
        "撤销会话失败",
        500
    )

    REVOKE_SESSIONS_FAILED = ErrorCode(
        "BIZ_903",
        "撤销所有会话失败",
        500
    )

    # 文件操作相关 (500-599)
    INVALID_FILE_TYPE = ErrorCode(
        "BIZ_500",
        "文件类型无效",
        400
    )

    FILE_TOO_LARGE = ErrorCode(
        "BIZ_501",
        "文件过大",
        400
    )

    EXCEL_PARSE_ERROR = ErrorCode(
        "BIZ_502",
        "Excel解析失败",
        400
    )

    EMPTY_FILE = ErrorCode(
        "BIZ_503",
        "文件为空",
        400
    )

    MISSING_COLUMNS = ErrorCode(
        "BIZ_504",
        "缺少必要列",
        400
    )

    EXPORT_LIMIT_EXCEEDED = ErrorCode(
        "BIZ_505",
        "导出数量超限",
        400
    )

    NO_DATA = ErrorCode(
        "BIZ_506",
        "无数据",
        404
    )

    EXPORT_ERROR = ErrorCode(
        "BIZ_507",
        "导出失败",
        500
    )

    IMPORT_ERROR = ErrorCode(
        "BIZ_508",
        "导入失败",
        500
    )

    # 账本相关 (600-699)
    LEDGER_CREATE_ERROR = ErrorCode(
        "BIZ_600",
        "账本创建失败",
        500
    )

    LEDGER_QUERY_ERROR = ErrorCode(
        "BIZ_601",
        "账本查询失败",
        500
    )

    TRANSACTION_NOT_FOUND = ErrorCode(
        "BIZ_602",
        "交易记录不存在",
        404
    )

    LEDGER_UPDATE_ERROR = ErrorCode(
        "BIZ_603",
        "账本更新失败",
        500
    )

    BALANCE_QUERY_ERROR = ErrorCode(
        "BIZ_604",
        "余额查询失败",
        500
    )

    BUDGET_QUERY_ERROR = ErrorCode(
        "BIZ_605",
        "预算查询失败",
        500
    )

    BUDGET_CREATE_ERROR = ErrorCode(
        "BIZ_606",
        "预算创建失败",
        500
    )

    STATISTICS_QUERY_ERROR = ErrorCode(
        "BIZ_607",
        "统计查询失败",
        500
    )

    # 系统健康检查 (700-799)
    READY_CHECK_FAILED = ErrorCode(
        "BIZ_700",
        "服务就绪检查失败",
        503
    )


# ============================================
# 系统错误码 (SYS_xxx)
# ============================================

class SystemErrorCodes:
    """系统错误码"""

    INTERNAL_ERROR = ErrorCode(
        "SYS_001",
        "系统内部错误",
        500
    )

    SERVICE_UNAVAILABLE = ErrorCode(
        "SYS_002",
        "服务暂时不可用",
        503
    )

    TIMEOUT = ErrorCode(
        "SYS_003",
        "请求超时",
        504
    )

    RATE_LIMIT_EXCEEDED = ErrorCode(
        "SYS_004",
        "请求过于频繁",
        429
    )


# ============================================
# 数据库错误码 (DB_xxx)
# ============================================

class DatabaseErrorCodes:
    """数据库错误码"""

    CONNECTION_FAILED = ErrorCode(
        "DB_001",
        "数据库连接失败",
        500
    )

    QUERY_FAILED = ErrorCode(
        "DB_002",
        "数据库查询失败",
        500
    )

    CONSTRAINT_VIOLATION = ErrorCode(
        "DB_003",
        "数据完整性约束违反",
        400
    )

    UNIQUE_VIOLATION = ErrorCode(
        "DB_004",
        "唯一性约束违反",
        409
    )

    FOREIGN_KEY_VIOLATION = ErrorCode(
        "DB_005",
        "外键约束违反",
        400
    )


# ============================================
# 参数验证错误码 (VALIDATION_xxx)
# ============================================

class ValidationErrorCodes:
    """参数验证错误码"""

    REQUIRED_FIELD_MISSING = ErrorCode(
        "VALIDATION_001",
        "必填字段缺失",
        400
    )

    INVALID_FORMAT = ErrorCode(
        "VALIDATION_002",
        "格式无效",
        400
    )

    INVALID_EMAIL = ErrorCode(
        "VALIDATION_003",
        "邮箱格式无效",
        400
    )

    INVALID_PHONE = ErrorCode(
        "VALIDATION_004",
        "电话格式无效",
        400
    )

    VALUE_OUT_OF_RANGE = ErrorCode(
        "VALIDATION_005",
        "值超出范围",
        400
    )

    INVALID_ENUM_VALUE = ErrorCode(
        "VALIDATION_006",
        "枚举值无效",
        400
    )

    # 数据验证详细错误 (100-199)
    MISSING_REQUIRED_COLUMN = ErrorCode(
        "VALIDATION_100",
        "缺少必填列",
        400
    )

    EMPTY_REQUIRED_FIELD = ErrorCode(
        "VALIDATION_101",
        "必填字段为空",
        400
    )

    STRING_TOO_LONG = ErrorCode(
        "VALIDATION_102",
        "字符串过长",
        400
    )

    TYPE_CONVERSION_ERROR = ErrorCode(
        "VALIDATION_103",
        "类型转换错误",
        400
    )

    PARSE_ERROR = ErrorCode(
        "VALIDATION_104",
        "解析错误",
        400
    )

    VALIDATION_ERROR = ErrorCode(
        "VALIDATION_105",
        "验证错误",
        400
    )


# ============================================
# 利润报表错误码 (PROFIT_xxx)
# 对齐 PROFIT_SOT.md v1.1 §5
# ============================================

class ProfitErrorCodes:
    """利润报表错误码 (PROFIT_SOT.md v1.1)"""

    # 参数校验错误 (001-002)
    INVALID_PERIOD_PARAMS = ErrorCode(
        "PROFIT_001",
        "周期参数无效",
        400
    )

    FUTURE_START_DATE = ErrorCode(
        "PROFIT_002",
        "开始日期不能是未来",
        400
    )

    # 资源不存在 (003, 005, 007)
    PROJECT_NOT_FOUND = ErrorCode(
        "PROFIT_003",
        "项目不存在",
        404
    )

    PERIOD_DATA_NOT_FOUND = ErrorCode(
        "PROFIT_005",
        "指定周期无数据",
        404
    )

    ACCOUNT_NOT_FOUND = ErrorCode(
        "PROFIT_007",
        "账户不存在",
        404
    )

    # 冲突错误 (004)
    PERIOD_LOCKED = ErrorCode(
        "PROFIT_004",
        "周期已锁定，无法刷新",
        409
    )

    # 权限错误 (006)
    MANUAL_UPDATE_FORBIDDEN = ErrorCode(
        "PROFIT_006",
        "禁止手工修改聚合数据",
        403
    )

    # 范围限制 (008)
    DATE_RANGE_EXCEEDED = ErrorCode(
        "PROFIT_008",
        "日期范围超出限制",
        400
    )


# ============================================
# 错误码字典 (用于快速查找)
# ============================================

ERROR_CODE_MAP: Dict[str, ErrorCode] = {
    # 认证错误
    "AUTH_001": AuthErrorCodes.INVALID_CREDENTIALS,
    "AUTH_002": AuthErrorCodes.ACCOUNT_DISABLED,
    "AUTH_003": AuthErrorCodes.TOKEN_REVOKED,
    "AUTH_004": AuthErrorCodes.USER_NOT_FOUND,
    "AUTH_005": AuthErrorCodes.TOKEN_REFRESH_FAILED,
    "AUTH_100": AuthErrorCodes.EMAIL_ALREADY_EXISTS,
    "AUTH_101": AuthErrorCodes.USERNAME_ALREADY_EXISTS,
    "AUTH_102": AuthErrorCodes.REGISTER_FAILED,
    "AUTH_200": AuthErrorCodes.PASSWORD_TOO_SHORT,
    "AUTH_201": AuthErrorCodes.PASSWORD_MISSING_DIGIT,
    "AUTH_202": AuthErrorCodes.PASSWORD_MISSING_LETTER,
    "AUTH_203": AuthErrorCodes.PASSWORD_MISSING_SPECIAL,
    "AUTH_204": AuthErrorCodes.OLD_PASSWORD_WRONG,
    "AUTH_205": AuthErrorCodes.RESET_TOKEN_INVALID,
    "AUTH_206": AuthErrorCodes.PASSWORD_CHANGE_FAILED,
    "AUTH_300": AuthErrorCodes.EMAIL_NOT_VERIFIED,
    "AUTH_301": AuthErrorCodes.EMAIL_VERIFICATION_FAILED,
    "AUTH_302": AuthErrorCodes.EMAIL_ALREADY_VERIFIED,
    "AUTH_400": AuthErrorCodes.TOKEN_MISSING,
    "AUTH_401": AuthErrorCodes.TOKEN_INVALID,
    "AUTH_402": AuthErrorCodes.TOKEN_EXPIRED,
    "AUTH_500": AuthErrorCodes.PERMISSION_DENIED,
    "AUTH_501": AuthErrorCodes.ROLE_NOT_ALLOWED,
    "AUTH_900": AuthErrorCodes.LOGIN_FAILED,
    "AUTH_901": AuthErrorCodes.LOGOUT_FAILED,
    "AUTH_999": AuthErrorCodes.AUTHENTICATION_ERROR,

    # 业务错误
    "BIZ_001": BusinessErrorCodes.INVALID_OPERATION,
    "BIZ_002": BusinessErrorCodes.RESOURCE_NOT_FOUND,
    "BIZ_003": BusinessErrorCodes.RESOURCE_ALREADY_EXISTS,
    "BIZ_100": BusinessErrorCodes.INVALID_AMOUNT,
    "BIZ_101": BusinessErrorCodes.INSUFFICIENT_BALANCE,
    "BIZ_200": BusinessErrorCodes.INVALID_DATE_RANGE,
    "BIZ_201": BusinessErrorCodes.DATE_IN_FUTURE,
    "BIZ_300": BusinessErrorCodes.INVALID_STATUS,
    "BIZ_301": BusinessErrorCodes.STATUS_TRANSITION_NOT_ALLOWED,
    "BIZ_400": BusinessErrorCodes.UPDATE_PROFILE_FAILED,
    "BIZ_401": BusinessErrorCodes.ACTIVATE_USER_FAILED,
    "BIZ_402": BusinessErrorCodes.DEACTIVATE_USER_FAILED,
    "BIZ_900": BusinessErrorCodes.OPERATION_FAILED,
    "BIZ_901": BusinessErrorCodes.GET_SESSIONS_FAILED,
    "BIZ_902": BusinessErrorCodes.REVOKE_SESSION_FAILED,
    "BIZ_903": BusinessErrorCodes.REVOKE_SESSIONS_FAILED,
    "BIZ_500": BusinessErrorCodes.INVALID_FILE_TYPE,
    "BIZ_501": BusinessErrorCodes.FILE_TOO_LARGE,
    "BIZ_502": BusinessErrorCodes.EXCEL_PARSE_ERROR,
    "BIZ_503": BusinessErrorCodes.EMPTY_FILE,
    "BIZ_504": BusinessErrorCodes.MISSING_COLUMNS,
    "BIZ_505": BusinessErrorCodes.EXPORT_LIMIT_EXCEEDED,
    "BIZ_506": BusinessErrorCodes.NO_DATA,
    "BIZ_507": BusinessErrorCodes.EXPORT_ERROR,
    "BIZ_508": BusinessErrorCodes.IMPORT_ERROR,
    "BIZ_600": BusinessErrorCodes.LEDGER_CREATE_ERROR,
    "BIZ_601": BusinessErrorCodes.LEDGER_QUERY_ERROR,
    "BIZ_602": BusinessErrorCodes.TRANSACTION_NOT_FOUND,
    "BIZ_603": BusinessErrorCodes.LEDGER_UPDATE_ERROR,
    "BIZ_604": BusinessErrorCodes.BALANCE_QUERY_ERROR,
    "BIZ_605": BusinessErrorCodes.BUDGET_QUERY_ERROR,
    "BIZ_606": BusinessErrorCodes.BUDGET_CREATE_ERROR,
    "BIZ_607": BusinessErrorCodes.STATISTICS_QUERY_ERROR,
    "BIZ_700": BusinessErrorCodes.READY_CHECK_FAILED,

    # 系统错误
    "SYS_001": SystemErrorCodes.INTERNAL_ERROR,
    "SYS_002": SystemErrorCodes.SERVICE_UNAVAILABLE,
    "SYS_003": SystemErrorCodes.TIMEOUT,
    "SYS_004": SystemErrorCodes.RATE_LIMIT_EXCEEDED,

    # 数据库错误
    "DB_001": DatabaseErrorCodes.CONNECTION_FAILED,
    "DB_002": DatabaseErrorCodes.QUERY_FAILED,
    "DB_003": DatabaseErrorCodes.CONSTRAINT_VIOLATION,
    "DB_004": DatabaseErrorCodes.UNIQUE_VIOLATION,
    "DB_005": DatabaseErrorCodes.FOREIGN_KEY_VIOLATION,

    # 验证错误
    "VALIDATION_001": ValidationErrorCodes.REQUIRED_FIELD_MISSING,
    "VALIDATION_002": ValidationErrorCodes.INVALID_FORMAT,
    "VALIDATION_003": ValidationErrorCodes.INVALID_EMAIL,
    "VALIDATION_004": ValidationErrorCodes.INVALID_PHONE,
    "VALIDATION_005": ValidationErrorCodes.VALUE_OUT_OF_RANGE,
    "VALIDATION_006": ValidationErrorCodes.INVALID_ENUM_VALUE,
    "VALIDATION_100": ValidationErrorCodes.MISSING_REQUIRED_COLUMN,
    "VALIDATION_101": ValidationErrorCodes.EMPTY_REQUIRED_FIELD,
    "VALIDATION_102": ValidationErrorCodes.STRING_TOO_LONG,
    "VALIDATION_103": ValidationErrorCodes.TYPE_CONVERSION_ERROR,
    "VALIDATION_104": ValidationErrorCodes.PARSE_ERROR,
    "VALIDATION_105": ValidationErrorCodes.VALIDATION_ERROR,

    # 利润报表错误 (PROFIT_SOT.md v1.1)
    "PROFIT_001": ProfitErrorCodes.INVALID_PERIOD_PARAMS,
    "PROFIT_002": ProfitErrorCodes.FUTURE_START_DATE,
    "PROFIT_003": ProfitErrorCodes.PROJECT_NOT_FOUND,
    "PROFIT_004": ProfitErrorCodes.PERIOD_LOCKED,
    "PROFIT_005": ProfitErrorCodes.PERIOD_DATA_NOT_FOUND,
    "PROFIT_006": ProfitErrorCodes.MANUAL_UPDATE_FORBIDDEN,
    "PROFIT_007": ProfitErrorCodes.ACCOUNT_NOT_FOUND,
    "PROFIT_008": ProfitErrorCodes.DATE_RANGE_EXCEEDED,
}


def get_error_code(code: str) -> ErrorCode:
    """
    获取错误码对象

    Args:
        code: 错误码字符串

    Returns:
        ErrorCode对象
    """
    return ERROR_CODE_MAP.get(code, SystemErrorCodes.INTERNAL_ERROR)
