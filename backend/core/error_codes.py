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

from typing import Dict, Any, Union


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
            "status_code": self.status_code,
        }


# ============================================
# 认证错误码 (AUTH_xxx)
# ============================================


class AuthErrorCodes:
    """认证相关错误码"""

    # 登录相关 (001-099)
    INVALID_CREDENTIALS = ErrorCode("AUTH_001", "用户名或密码错误", 401)

    ACCOUNT_DISABLED = ErrorCode("AUTH_002", "账户已被禁用", 403)

    TOKEN_REVOKED = ErrorCode("AUTH_003", "令牌已被撤销", 401)

    USER_NOT_FOUND = ErrorCode("AUTH_004", "用户不存在或已被禁用", 404)

    TOKEN_REFRESH_FAILED = ErrorCode("AUTH_005", "令牌刷新失败", 401)

    # 注册相关 (100-199)
    EMAIL_ALREADY_EXISTS = ErrorCode("AUTH_100", "邮箱已被注册", 400)

    USERNAME_ALREADY_EXISTS = ErrorCode("AUTH_101", "用户名已被使用", 400)

    REGISTER_FAILED = ErrorCode("AUTH_102", "注册失败，请稍后重试", 500)

    # 密码相关 (200-299)
    PASSWORD_TOO_SHORT = ErrorCode("AUTH_200", "密码长度至少8位", 400)

    PASSWORD_MISSING_DIGIT = ErrorCode("AUTH_201", "密码必须包含至少一个数字", 400)

    PASSWORD_MISSING_LETTER = ErrorCode("AUTH_202", "密码必须包含至少一个字母", 400)

    PASSWORD_MISSING_SPECIAL = ErrorCode("AUTH_203", "密码必须包含至少一个特殊字符", 400)

    OLD_PASSWORD_WRONG = ErrorCode("AUTH_204", "旧密码错误", 400)

    RESET_TOKEN_INVALID = ErrorCode("AUTH_205", "重置令牌无效或已过期", 400)

    PASSWORD_CHANGE_FAILED = ErrorCode("AUTH_206", "密码修改失败", 500)

    # 邮箱验证 (300-399)
    EMAIL_NOT_VERIFIED = ErrorCode("AUTH_300", "邮箱未验证", 403)

    EMAIL_VERIFICATION_FAILED = ErrorCode("AUTH_301", "邮箱验证失败", 400)

    EMAIL_ALREADY_VERIFIED = ErrorCode("AUTH_302", "邮箱已验证", 400)

    # Token相关 (400-499)
    TOKEN_MISSING = ErrorCode("AUTH_400", "未提供认证令牌", 401)

    TOKEN_INVALID = ErrorCode("AUTH_401", "无效的认证令牌", 401)

    TOKEN_EXPIRED = ErrorCode("AUTH_402", "令牌已过期", 401)

    # 权限相关 (500-599)
    PERMISSION_DENIED = ErrorCode("AUTH_500", "权限不足", 403)

    ROLE_NOT_ALLOWED = ErrorCode("AUTH_501", "角色权限不足", 403)

    # 通用认证错误 (900-999)
    LOGIN_FAILED = ErrorCode("AUTH_900", "登录失败，请稍后重试", 500)

    LOGOUT_FAILED = ErrorCode("AUTH_901", "登出失败", 500)

    AUTHENTICATION_ERROR = ErrorCode("AUTH_999", "认证失败", 401)


# ============================================
# 业务错误码 (BIZ_xxx)
# ============================================


class BusinessErrorCodes:
    """业务逻辑错误码"""

    # 通用业务错误 (001-099)
    INVALID_OPERATION = ErrorCode("BIZ_001", "无效的操作", 400)

    RESOURCE_NOT_FOUND = ErrorCode("BIZ_002", "资源不存在", 404)

    RESOURCE_ALREADY_EXISTS = ErrorCode("BIZ_003", "资源已存在", 409)

    RESOURCE_HAS_DEPENDENCIES = ErrorCode("BIZ_004", "资源有关联数据，无法删除", 409)

    # 金额相关 (100-199)
    INVALID_AMOUNT = ErrorCode("BIZ_100", "金额无效", 400)

    INSUFFICIENT_BALANCE = ErrorCode("BIZ_101", "余额不足", 400)

    # 日期相关 (200-299)
    INVALID_DATE_RANGE = ErrorCode("BIZ_200", "日期范围无效", 400)

    DATE_IN_FUTURE = ErrorCode("BIZ_201", "日期不能为未来", 400)

    # 状态相关 (300-399)
    INVALID_STATUS = ErrorCode("BIZ_300", "状态无效", 400)

    STATUS_TRANSITION_NOT_ALLOWED = ErrorCode("BIZ_301", "状态转换不允许", 400)

    # 用户管理相关 (400-499)
    UPDATE_PROFILE_FAILED = ErrorCode("BIZ_400", "更新用户资料失败", 500)

    ACTIVATE_USER_FAILED = ErrorCode("BIZ_401", "激活用户失败", 500)

    DEACTIVATE_USER_FAILED = ErrorCode("BIZ_402", "停用用户失败", 500)

    # 通用业务操作失败 (900-999)
    OPERATION_FAILED = ErrorCode("BIZ_900", "操作失败", 500)

    GET_SESSIONS_FAILED = ErrorCode("BIZ_901", "获取会话列表失败", 500)

    REVOKE_SESSION_FAILED = ErrorCode("BIZ_902", "撤销会话失败", 500)

    REVOKE_SESSIONS_FAILED = ErrorCode("BIZ_903", "撤销所有会话失败", 500)

    # 文件操作相关 (500-599)
    INVALID_FILE_TYPE = ErrorCode("BIZ_500", "文件类型无效", 400)

    FILE_TOO_LARGE = ErrorCode("BIZ_501", "文件过大", 400)

    EXCEL_PARSE_ERROR = ErrorCode("BIZ_502", "Excel解析失败", 400)

    EMPTY_FILE = ErrorCode("BIZ_503", "文件为空", 400)

    MISSING_COLUMNS = ErrorCode("BIZ_504", "缺少必要列", 400)

    EXPORT_LIMIT_EXCEEDED = ErrorCode("BIZ_505", "导出数量超限", 400)

    NO_DATA = ErrorCode("BIZ_506", "无数据", 404)

    EXPORT_ERROR = ErrorCode("BIZ_507", "导出失败", 500)

    IMPORT_ERROR = ErrorCode("BIZ_508", "导入失败", 500)

    # 账本相关 (600-699)
    LEDGER_CREATE_ERROR = ErrorCode("BIZ_600", "账本创建失败", 500)

    LEDGER_QUERY_ERROR = ErrorCode("BIZ_601", "账本查询失败", 500)

    TRANSACTION_NOT_FOUND = ErrorCode("BIZ_602", "交易记录不存在", 404)

    LEDGER_UPDATE_ERROR = ErrorCode("BIZ_603", "账本更新失败", 500)

    BALANCE_QUERY_ERROR = ErrorCode("BIZ_604", "余额查询失败", 500)

    BUDGET_QUERY_ERROR = ErrorCode("BIZ_605", "预算查询失败", 500)

    BUDGET_CREATE_ERROR = ErrorCode("BIZ_606", "预算创建失败", 500)

    STATISTICS_QUERY_ERROR = ErrorCode("BIZ_607", "统计查询失败", 500)

    # 余额迁移相关 (610-619)
    TRANSFER_DUPLICATE_REQUEST = ErrorCode("BIZ_610", "迁移申请单号已存在", 409)

    TRANSFER_SAME_ACCOUNT = ErrorCode("BIZ_611", "源账户和目标账户不能相同", 400)

    TRANSFER_SOURCE_NOT_DEAD = ErrorCode("BIZ_612", "源账户状态必须为 dead", 400)

    TRANSFER_TARGET_NOT_ACTIVE = ErrorCode("BIZ_613", "目标账户状态必须为 active", 400)

    TRANSFER_CROSS_SUPPLIER = ErrorCode("BIZ_614", "禁止跨供应商迁移余额", 400)

    TRANSFER_ALREADY_PROCESSED = ErrorCode("BIZ_615", "迁移申请已处理", 409)

    TRANSFER_INSUFFICIENT_BALANCE = ErrorCode("BIZ_616", "余额不足", 400)

    TRANSFER_INVALID_AMOUNT = ErrorCode("BIZ_617", "迁移金额无效", 400)

    TRANSFER_LEDGER_ERROR = ErrorCode("BIZ_618", "账本记录生成失败", 500)

    TRANSFER_STATE_ERROR = ErrorCode("BIZ_619", "迁移状态错误", 409)

    # 系统健康检查 (700-799)
    READY_CHECK_FAILED = ErrorCode("BIZ_700", "服务就绪检查失败", 503)


# ============================================
# 系统错误码 (SYS_xxx)
# ============================================


class SystemErrorCodes:
    """系统错误码"""

    INTERNAL_ERROR = ErrorCode("SYS_001", "系统内部错误", 500)

    SERVICE_UNAVAILABLE = ErrorCode("SYS_002", "服务暂时不可用", 503)

    TIMEOUT = ErrorCode("SYS_003", "请求超时", 504)

    RATE_LIMIT_EXCEEDED = ErrorCode("SYS_004", "请求过于频繁", 429)


# ============================================
# 数据库错误码 (DB_xxx)
# ============================================


class DatabaseErrorCodes:
    """数据库错误码"""

    CONNECTION_FAILED = ErrorCode("DB_001", "数据库连接失败", 500)

    QUERY_FAILED = ErrorCode("DB_002", "数据库查询失败", 500)

    CONSTRAINT_VIOLATION = ErrorCode("DB_003", "数据完整性约束违反", 400)

    UNIQUE_VIOLATION = ErrorCode("DB_004", "唯一性约束违反", 409)

    FOREIGN_KEY_VIOLATION = ErrorCode("DB_005", "外键约束违反", 400)


# ============================================
# 参数验证错误码 (VALIDATION_xxx)
# ============================================


class ValidationErrorCodes:
    """参数验证错误码"""

    REQUIRED_FIELD_MISSING = ErrorCode("VALIDATION_001", "必填字段缺失", 400)

    INVALID_FORMAT = ErrorCode("VALIDATION_002", "格式无效", 400)

    INVALID_EMAIL = ErrorCode("VALIDATION_003", "邮箱格式无效", 400)

    INVALID_PHONE = ErrorCode("VALIDATION_004", "电话格式无效", 400)

    VALUE_OUT_OF_RANGE = ErrorCode("VALIDATION_005", "值超出范围", 400)

    INVALID_ENUM_VALUE = ErrorCode("VALIDATION_006", "枚举值无效", 400)

    # 数据验证详细错误 (100-199)
    MISSING_REQUIRED_COLUMN = ErrorCode("VALIDATION_100", "缺少必填列", 400)

    EMPTY_REQUIRED_FIELD = ErrorCode("VALIDATION_101", "必填字段为空", 400)

    STRING_TOO_LONG = ErrorCode("VALIDATION_102", "字符串过长", 400)

    TYPE_CONVERSION_ERROR = ErrorCode("VALIDATION_103", "类型转换错误", 400)

    PARSE_ERROR = ErrorCode("VALIDATION_104", "解析错误", 400)

    VALIDATION_ERROR = ErrorCode("VALIDATION_105", "验证错误", 400)


# ============================================
# 利润报表错误码 (PROFIT_xxx)
# 对齐 PROFIT_SOT.md v1.1 §5
# ============================================


class ProfitErrorCodes:
    """利润报表错误码 (PROFIT_SOT.md v1.1)"""

    # 参数校验错误 (001-002)
    INVALID_PERIOD_PARAMS = ErrorCode("PROFIT_001", "周期参数无效", 400)

    FUTURE_START_DATE = ErrorCode("PROFIT_002", "开始日期不能是未来", 400)

    # 资源不存在 (003, 005, 007)
    PROJECT_NOT_FOUND = ErrorCode("PROFIT_003", "项目不存在", 404)

    PERIOD_DATA_NOT_FOUND = ErrorCode("PROFIT_005", "指定周期无数据", 404)

    ACCOUNT_NOT_FOUND = ErrorCode("PROFIT_007", "账户不存在", 404)

    # 冲突错误 (004)
    PERIOD_LOCKED = ErrorCode("PROFIT_004", "周期已锁定，无法刷新", 409)

    # 权限错误 (006)
    MANUAL_UPDATE_FORBIDDEN = ErrorCode("PROFIT_006", "禁止手工修改聚合数据", 403)

    # 范围限制 (008)
    DATE_RANGE_EXCEEDED = ErrorCode("PROFIT_008", "日期范围超出限制", 400)


# ============================================
# 状态机错误码 (STATE_xxx)
# 对齐 STATE_MACHINE.md v2.6 §8
# ============================================


class StateErrorCodes:
    """状态机错误码 (STATE_MACHINE.md v2.6)"""

    # 状态流转错误 (400-409)
    FORBIDDEN_TRANSITION = ErrorCode("STATE_400", "非法状态流转", 400)

    SKIP_REQUIRED_STEP = ErrorCode("STATE_401", "跳过必要步骤", 400)

    FINAL_STATE_ROLLBACK = ErrorCode("STATE_402", "终态非法回退", 400)

    SYSTEM_FORBIDDEN = ErrorCode("STATE_403", "系统无权限流转", 403)

    ABSOLUTELY_FORBIDDEN = ErrorCode("STATE_405", "绝对禁止的流转", 400)

    CONCURRENCY_CONFLICT = ErrorCode("STATE_409", "并发冲突，版本不一致", 409)


# ============================================
# 趋势风控错误码 (TREND_xxx)
# 对齐 STATE_MACHINE.md v2.6 第8.3节
# ============================================


class TrendErrorCodes:
    """趋势风控错误码 (STATE_MACHINE.md v2.6 §8.3)"""

    # 风控触发 (001-003)
    TREND_RISK_TRIGGERED = ErrorCode("TREND_001", "趋势风控触发", 200)  # 注意: 风控触发是成功的业务操作

    REVIEW_REQUIRED = ErrorCode("TREND_002", "风控复核未完成", 400)

    RULE_CONFIG_ERROR = ErrorCode("TREND_003", "风控规则配置错误", 500)

    # 复核操作 (010-019)
    RESOLUTION_NOTE_MISSING = ErrorCode("TREND_010", "复核原因缺失", 400)

    ALREADY_RESOLVED = ErrorCode("TREND_011", "已完成复核，无需重复操作", 400)

    INVALID_RESOLUTION_ACTION = ErrorCode("TREND_012", "无效的复核操作", 400)


# ============================================
# 对账错误码 (RECON_xxx)
# 对齐 STATE_MACHINE.md v2.6 §14.4
# ============================================


class ReconciliationErrorCodes:
    """对账错误码 (STATE_MACHINE.md v2.6 §14.4)"""

    # 批次完成前置条件错误 (001-009)
    PENDING_DETAILS_EXIST = ErrorCode("RECON_001", "存在未处理的对账明细", 400)

    ADJUSTMENT_NO_LEDGER = ErrorCode("RECON_002", "调整未生成账本分录", 400)

    REPORT_NOT_GENERATED = ErrorCode("RECON_003", "对账报告未生成", 400)

    # Invariants 校验错误 (010-019)
    DEBIT_CREDIT_IMBALANCE = ErrorCode("RECON_010", "借贷不平衡", 400)

    SUPPLIER_NEGATIVE_BALANCE = ErrorCode("RECON_011", "代理商余额为负", 400)

    ORPHAN_LEDGER_ENTRIES = ErrorCode("RECON_012", "存在孤立分录", 400)

    CONFIRMED_EVENT_NOT_POSTED = ErrorCode("RECON_013", "已确认事件未入账", 400)

    BALANCE_LEDGER_MISMATCH = ErrorCode("RECON_014", "余额字段与账本不一致", 400)

    # 对账操作错误 (020-029)
    BATCH_NOT_FOUND = ErrorCode("RECON_020", "对账批次不存在", 404)

    DETAIL_NOT_FOUND = ErrorCode("RECON_021", "对账明细不存在", 404)

    ADJUSTMENT_NOT_FOUND = ErrorCode("RECON_022", "调整记录不存在", 404)

    BATCH_ALREADY_COMPLETED = ErrorCode("RECON_023", "对账批次已完成", 400)

    # Excel 对比错误 (030-039)
    EXCEL_COMPARISON_FAILED = ErrorCode("RECON_030", "Excel对比失败", 400)

    SUPPLIER_NOT_FOUND = ErrorCode("RECON_031", "供应商不存在", 404)

    SNAPSHOT_NOT_FOUND = ErrorCode("RECON_032", "余额快照不存在", 404)


# ============================================
# 手续费错误码 (FEE_xxx)
# ============================================


class FeeErrorCodes:
    """手续费相关错误码 (FINANCIAL_REFACTOR_PLAN.md Phase 4)"""

    # 供应商费率错误 (001-009)
    SUPPLIER_NOT_FOUND = ErrorCode("FEE_001", "供应商不存在", 404)

    INVALID_FEE_RATE = ErrorCode("FEE_002", "费率无效，必须在0-1之间", 400)

    INVALID_FEE_TYPE = ErrorCode("FEE_003", "费率类型无效，必须是PERCENTAGE或FIXED", 400)

    FEE_RATE_NOT_CONFIGURED = ErrorCode("FEE_004", "供应商未配置费率", 400)

    # 计算错误 (010-019)
    CALCULATION_ERROR = ErrorCode("FEE_010", "手续费计算失败", 500)

    NEGATIVE_SPEND_AMOUNT = ErrorCode("FEE_011", "消耗金额不能为负数", 400)

    OVERFLOW_ERROR = ErrorCode("FEE_012", "金额计算溢出", 400)

    # 费率更新错误 (020-029)
    UPDATE_FAILED = ErrorCode("FEE_020", "费率更新失败", 500)

    PERMISSION_DENIED = ErrorCode("FEE_021", "无权更新费率", 403)

    EFFECTIVE_DATE_INVALID = ErrorCode("FEE_022", "生效日期无效", 400)


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
    "BIZ_004": BusinessErrorCodes.RESOURCE_HAS_DEPENDENCIES,
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
    "BIZ_610": BusinessErrorCodes.TRANSFER_DUPLICATE_REQUEST,
    "BIZ_611": BusinessErrorCodes.TRANSFER_SAME_ACCOUNT,
    "BIZ_612": BusinessErrorCodes.TRANSFER_SOURCE_NOT_DEAD,
    "BIZ_613": BusinessErrorCodes.TRANSFER_TARGET_NOT_ACTIVE,
    "BIZ_614": BusinessErrorCodes.TRANSFER_CROSS_SUPPLIER,
    "BIZ_615": BusinessErrorCodes.TRANSFER_ALREADY_PROCESSED,
    "BIZ_616": BusinessErrorCodes.TRANSFER_INSUFFICIENT_BALANCE,
    "BIZ_617": BusinessErrorCodes.TRANSFER_INVALID_AMOUNT,
    "BIZ_618": BusinessErrorCodes.TRANSFER_LEDGER_ERROR,
    "BIZ_619": BusinessErrorCodes.TRANSFER_STATE_ERROR,
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
    # 状态机错误 (STATE_MACHINE.md v2.6)
    "STATE_400": StateErrorCodes.FORBIDDEN_TRANSITION,
    "STATE_401": StateErrorCodes.SKIP_REQUIRED_STEP,
    "STATE_402": StateErrorCodes.FINAL_STATE_ROLLBACK,
    "STATE_403": StateErrorCodes.SYSTEM_FORBIDDEN,
    "STATE_405": StateErrorCodes.ABSOLUTELY_FORBIDDEN,
    "STATE_409": StateErrorCodes.CONCURRENCY_CONFLICT,
    # 趋势风控错误 (STATE_MACHINE.md v2.6 §8.3)
    "TREND_001": TrendErrorCodes.TREND_RISK_TRIGGERED,
    "TREND_002": TrendErrorCodes.REVIEW_REQUIRED,
    "TREND_003": TrendErrorCodes.RULE_CONFIG_ERROR,
    "TREND_010": TrendErrorCodes.RESOLUTION_NOTE_MISSING,
    "TREND_011": TrendErrorCodes.ALREADY_RESOLVED,
    "TREND_012": TrendErrorCodes.INVALID_RESOLUTION_ACTION,
    # 对账错误 (STATE_MACHINE.md v2.6 §14.4)
    "RECON_001": ReconciliationErrorCodes.PENDING_DETAILS_EXIST,
    "RECON_002": ReconciliationErrorCodes.ADJUSTMENT_NO_LEDGER,
    "RECON_003": ReconciliationErrorCodes.REPORT_NOT_GENERATED,
    "RECON_010": ReconciliationErrorCodes.DEBIT_CREDIT_IMBALANCE,
    "RECON_011": ReconciliationErrorCodes.SUPPLIER_NEGATIVE_BALANCE,
    "RECON_012": ReconciliationErrorCodes.ORPHAN_LEDGER_ENTRIES,
    "RECON_013": ReconciliationErrorCodes.CONFIRMED_EVENT_NOT_POSTED,
    "RECON_014": ReconciliationErrorCodes.BALANCE_LEDGER_MISMATCH,
    "RECON_020": ReconciliationErrorCodes.BATCH_NOT_FOUND,
    "RECON_021": ReconciliationErrorCodes.DETAIL_NOT_FOUND,
    "RECON_022": ReconciliationErrorCodes.ADJUSTMENT_NOT_FOUND,
    "RECON_023": ReconciliationErrorCodes.BATCH_ALREADY_COMPLETED,
    "RECON_030": ReconciliationErrorCodes.EXCEL_COMPARISON_FAILED,
    "RECON_031": ReconciliationErrorCodes.SUPPLIER_NOT_FOUND,
    "RECON_032": ReconciliationErrorCodes.SNAPSHOT_NOT_FOUND,
    # 手续费错误 (FINANCIAL_REFACTOR_PLAN.md Phase 4)
    "FEE_001": FeeErrorCodes.SUPPLIER_NOT_FOUND,
    "FEE_002": FeeErrorCodes.INVALID_FEE_RATE,
    "FEE_003": FeeErrorCodes.INVALID_FEE_TYPE,
    "FEE_004": FeeErrorCodes.FEE_RATE_NOT_CONFIGURED,
    "FEE_010": FeeErrorCodes.CALCULATION_ERROR,
    "FEE_011": FeeErrorCodes.NEGATIVE_SPEND_AMOUNT,
    "FEE_012": FeeErrorCodes.OVERFLOW_ERROR,
    "FEE_020": FeeErrorCodes.UPDATE_FAILED,
    "FEE_021": FeeErrorCodes.PERMISSION_DENIED,
    "FEE_022": FeeErrorCodes.EFFECTIVE_DATE_INVALID,
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


# ============================================
# 统一错误码枚举 (ErrorCodes)
# SoT Reference: ERROR_CODES_SOT.md v2.1
# ============================================

from enum import Enum


class ErrorCategory(str, Enum):
    """错误码类别"""

    VAL = "VALIDATION"  # 参数验证错误
    AUTH = "AUTH"  # 认证错误
    PERM = "PERM"  # 权限错误 (AUTH_500+)
    RES = "RESOURCE"  # 资源错误 (BIZ_002, BIZ_003)
    STATE = "STATE"  # 状态机错误
    BIZ = "BIZ"  # 业务逻辑错误
    SYS = "SYS"  # 系统错误
    DB = "DB"  # 数据库错误
    TREND = "TREND"  # 趋势风控错误
    PROFIT = "PROFIT"  # 利润统计错误
    RECON = "RECON"  # 对账错误
    FEE = "FEE"  # 手续费错误


class ErrorCodes(str, Enum):
    """
    统一错误码枚举

    提供所有错误码的统一访问入口，支持按类别分组。

    使用示例:
        from backend.core.error_codes import ErrorCodes, get_http_status, get_message_template

        code = ErrorCodes.AUTH_INVALID_TOKEN
        status = get_http_status(code)  # 401
        message = get_message_template(code)  # "无效的认证令牌"

    类别映射:
        VAL   - VALIDATION_xxx (参数验证)
        AUTH  - AUTH_xxx (认证)
        PERM  - AUTH_500+ (权限)
        RES   - BIZ_002, BIZ_003 (资源)
        STATE - STATE_xxx (状态机)
        BIZ   - BIZ_xxx (业务)
        SYS   - SYS_xxx (系统)
    """

    # ========== VAL: 参数验证错误 ==========
    VAL_REQUIRED_FIELD = "VALIDATION_001"
    VAL_INVALID_FORMAT = "VALIDATION_002"
    VAL_INVALID_EMAIL = "VALIDATION_003"
    VAL_INVALID_PHONE = "VALIDATION_004"
    VAL_OUT_OF_RANGE = "VALIDATION_005"
    VAL_INVALID_ENUM = "VALIDATION_006"
    VAL_MISSING_COLUMN = "VALIDATION_100"
    VAL_EMPTY_FIELD = "VALIDATION_101"
    VAL_STRING_TOO_LONG = "VALIDATION_102"
    VAL_TYPE_ERROR = "VALIDATION_103"
    VAL_PARSE_ERROR = "VALIDATION_104"
    VAL_VALIDATION_ERROR = "VALIDATION_105"

    # ========== AUTH: 认证错误 ==========
    AUTH_INVALID_CREDENTIALS = "AUTH_001"
    AUTH_ACCOUNT_DISABLED = "AUTH_002"
    AUTH_TOKEN_REVOKED = "AUTH_003"
    AUTH_USER_NOT_FOUND = "AUTH_004"
    AUTH_REFRESH_FAILED = "AUTH_005"
    AUTH_EMAIL_EXISTS = "AUTH_100"
    AUTH_USERNAME_EXISTS = "AUTH_101"
    AUTH_REGISTER_FAILED = "AUTH_102"
    AUTH_TOKEN_MISSING = "AUTH_400"
    AUTH_INVALID_TOKEN = "AUTH_401"
    AUTH_TOKEN_EXPIRED = "AUTH_402"
    AUTH_LOGIN_FAILED = "AUTH_900"
    AUTH_LOGOUT_FAILED = "AUTH_901"
    AUTH_GENERIC_ERROR = "AUTH_999"

    # ========== PERM: 权限错误 ==========
    PERM_DENIED = "AUTH_500"
    PERM_ROLE_NOT_ALLOWED = "AUTH_501"

    # ========== RES: 资源错误 ==========
    RES_NOT_FOUND = "BIZ_002"
    RES_ALREADY_EXISTS = "BIZ_003"

    # ========== STATE: 状态机错误 ==========
    STATE_FORBIDDEN_TRANSITION = "STATE_400"
    STATE_SKIP_REQUIRED_STEP = "STATE_401"
    STATE_FINAL_ROLLBACK = "STATE_402"
    STATE_SYSTEM_FORBIDDEN = "STATE_403"
    STATE_ABSOLUTELY_FORBIDDEN = "STATE_405"
    STATE_CONCURRENCY_CONFLICT = "STATE_409"

    # ========== BIZ: 业务逻辑错误 ==========
    BIZ_INVALID_OPERATION = "BIZ_001"
    BIZ_INVALID_AMOUNT = "BIZ_100"
    BIZ_INSUFFICIENT_BALANCE = "BIZ_101"
    BIZ_INVALID_DATE_RANGE = "BIZ_200"
    BIZ_DATE_IN_FUTURE = "BIZ_201"
    BIZ_INVALID_STATUS = "BIZ_300"
    BIZ_STATUS_TRANSITION_NOT_ALLOWED = "BIZ_301"
    BIZ_UPDATE_PROFILE_FAILED = "BIZ_400"
    BIZ_INVALID_FILE_TYPE = "BIZ_500"
    BIZ_FILE_TOO_LARGE = "BIZ_501"
    BIZ_EXCEL_PARSE_ERROR = "BIZ_502"
    BIZ_EMPTY_FILE = "BIZ_503"
    BIZ_MISSING_COLUMNS = "BIZ_504"
    BIZ_LEDGER_CREATE_ERROR = "BIZ_600"
    BIZ_LEDGER_QUERY_ERROR = "BIZ_601"
    BIZ_TRANSACTION_NOT_FOUND = "BIZ_602"
    BIZ_READY_CHECK_FAILED = "BIZ_700"

    # ========== SYS: 系统错误 ==========
    SYS_INTERNAL_ERROR = "SYS_001"
    SYS_SERVICE_UNAVAILABLE = "SYS_002"
    SYS_TIMEOUT = "SYS_003"
    SYS_RATE_LIMIT = "SYS_004"

    # ========== DB: 数据库错误 ==========
    DB_CONNECTION_FAILED = "DB_001"
    DB_QUERY_FAILED = "DB_002"
    DB_CONSTRAINT_VIOLATION = "DB_003"
    DB_UNIQUE_VIOLATION = "DB_004"
    DB_FOREIGN_KEY_VIOLATION = "DB_005"

    # ========== TREND: 趋势风控错误 ==========
    TREND_RISK_TRIGGERED = "TREND_001"
    TREND_REVIEW_REQUIRED = "TREND_002"
    TREND_RULE_CONFIG_ERROR = "TREND_003"
    TREND_RESOLUTION_NOTE_MISSING = "TREND_010"
    TREND_ALREADY_RESOLVED = "TREND_011"

    # ========== PROFIT: 利润统计错误 ==========
    PROFIT_INVALID_PERIOD = "PROFIT_001"
    PROFIT_FUTURE_DATE = "PROFIT_002"
    PROFIT_PROJECT_NOT_FOUND = "PROFIT_003"
    PROFIT_PERIOD_LOCKED = "PROFIT_004"
    PROFIT_NO_DATA = "PROFIT_005"

    @property
    def category(self) -> ErrorCategory:
        """获取错误码类别"""
        prefix = self.value.split("_")[0]
        category_map = {
            "VALIDATION": ErrorCategory.VAL,
            "AUTH": ErrorCategory.AUTH
            if int(self.value.split("_")[1]) < 500
            else ErrorCategory.PERM,
            "STATE": ErrorCategory.STATE,
            "BIZ": ErrorCategory.BIZ,
            "SYS": ErrorCategory.SYS,
            "DB": ErrorCategory.DB,
            "TREND": ErrorCategory.TREND,
            "PROFIT": ErrorCategory.PROFIT,
            "RECON": ErrorCategory.RECON,
            "FEE": ErrorCategory.FEE,
        }
        return category_map.get(prefix, ErrorCategory.SYS)

    @property
    def http_status(self) -> int:
        """获取 HTTP 状态码"""
        return get_http_status(self.value)

    @property
    def message(self) -> str:
        """获取错误消息模板"""
        return get_message_template(self.value)


# ============================================
# 辅助函数
# ============================================


def get_http_status(code: Union[str, "ErrorCodes"]) -> int:
    """
    获取错误码对应的 HTTP 状态码

    Args:
        code: 错误码字符串或 ErrorCodes 枚举

    Returns:
        HTTP 状态码 (如 400, 401, 404, 500)

    使用示例:
        status = get_http_status("AUTH_401")  # 401
        status = get_http_status(ErrorCodes.AUTH_INVALID_TOKEN)  # 401
    """
    if isinstance(code, ErrorCodes):
        code = code.value

    error = ERROR_CODE_MAP.get(code)
    if error:
        return error.status_code

    # 默认根据前缀推断
    prefix = code.split("_")[0] if "_" in code else code
    default_status = {
        "AUTH": 401,
        "VALIDATION": 400,
        "BIZ": 400,
        "STATE": 400,
        "SYS": 500,
        "DB": 500,
        "TREND": 400,
        "PROFIT": 400,
        "RECON": 400,
        "FEE": 400,
    }
    return default_status.get(prefix, 500)


def get_message_template(code: Union[str, "ErrorCodes"]) -> str:
    """
    获取错误码对应的消息模板

    Args:
        code: 错误码字符串或 ErrorCodes 枚举

    Returns:
        错误消息模板 (中文)

    使用示例:
        message = get_message_template("AUTH_401")  # "无效的认证令牌"
        message = get_message_template(ErrorCodes.RES_NOT_FOUND)  # "资源不存在"
    """
    if isinstance(code, ErrorCodes):
        code = code.value

    error = ERROR_CODE_MAP.get(code)
    if error:
        return error.message

    # 默认消息
    return f"错误码 {code} 未定义消息模板"


def get_category(code: Union[str, "ErrorCodes"]) -> ErrorCategory:
    """
    获取错误码类别

    Args:
        code: 错误码字符串或 ErrorCodes 枚举

    Returns:
        ErrorCategory 枚举

    使用示例:
        category = get_category("AUTH_401")  # ErrorCategory.AUTH
        category = get_category("AUTH_500")  # ErrorCategory.PERM
    """
    if isinstance(code, ErrorCodes):
        return code.category

    prefix = code.split("_")[0] if "_" in code else code

    # AUTH_500+ 是权限错误
    if prefix == "AUTH":
        try:
            num = int(code.split("_")[1])
            if num >= 500:
                return ErrorCategory.PERM
        except (ValueError, IndexError):
            pass
        return ErrorCategory.AUTH

    category_map = {
        "VALIDATION": ErrorCategory.VAL,
        "STATE": ErrorCategory.STATE,
        "BIZ": ErrorCategory.BIZ,
        "SYS": ErrorCategory.SYS,
        "DB": ErrorCategory.DB,
        "TREND": ErrorCategory.TREND,
        "PROFIT": ErrorCategory.PROFIT,
        "RECON": ErrorCategory.RECON,
        "FEE": ErrorCategory.FEE,
    }
    return category_map.get(prefix, ErrorCategory.SYS)


def is_client_error(code: Union[str, "ErrorCodes"]) -> bool:
    """判断是否为客户端错误 (4xx)"""
    return 400 <= get_http_status(code) < 500


def is_server_error(code: Union[str, "ErrorCodes"]) -> bool:
    """判断是否为服务端错误 (5xx)"""
    return get_http_status(code) >= 500


# ============================================
# 导出列表
# ============================================

__all__ = [
    # 基础类
    "ErrorCode",
    "ErrorCategory",
    "ErrorCodes",
    # 错误码类
    "AuthErrorCodes",
    "BusinessErrorCodes",
    "SystemErrorCodes",
    "DatabaseErrorCodes",
    "ValidationErrorCodes",
    "StateErrorCodes",
    "TrendErrorCodes",
    "ProfitErrorCodes",
    "ReconciliationErrorCodes",
    "FeeErrorCodes",
    # 映射表
    "ERROR_CODE_MAP",
    # 辅助函数
    "get_error_code",
    "get_http_status",
    "get_message_template",
    "get_category",
    "is_client_error",
    "is_server_error",
]
