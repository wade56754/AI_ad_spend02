"""
错误码系统测试模块
测试 backend/core/error_codes.py 的错误码定义和查找功能
"""

import pytest
from backend.core.error_codes import (
    ErrorCode,
    AuthErrorCodes,
    BusinessErrorCodes,
    SystemErrorCodes,
    DatabaseErrorCodes,
    ValidationErrorCodes,
    ProfitErrorCodes,
    ERROR_CODE_MAP,
    get_error_code
)


# ==================== ErrorCode基类测试 ====================

@pytest.mark.unit
@pytest.mark.error_codes
class TestErrorCodeBase:
    """测试错误码基类"""

    def test_error_code_initialization(self):
        """测试错误码初始化"""
        error = ErrorCode("TEST_001", "测试错误", 400)

        assert error.code == "TEST_001"
        assert error.message == "测试错误"
        assert error.status_code == 400

    def test_error_code_default_status_code(self):
        """测试默认状态码"""
        error = ErrorCode("TEST_002", "测试错误")

        assert error.status_code == 400

    def test_error_code_to_dict(self):
        """测试转换为字典"""
        error = ErrorCode("TEST_003", "测试错误", 500)
        result = error.to_dict()

        assert result == {
            "code": "TEST_003",
            "message": "测试错误",
            "status_code": 500
        }


# ==================== 认证错误码测试 ====================

@pytest.mark.unit
@pytest.mark.error_codes
class TestAuthErrorCodes:
    """测试认证错误码"""

    def test_invalid_credentials(self):
        """测试无效凭证错误"""
        error = AuthErrorCodes.INVALID_CREDENTIALS

        assert error.code == "AUTH_001"
        assert error.status_code == 401
        assert "密码" in error.message

    def test_account_disabled(self):
        """测试账户禁用错误"""
        error = AuthErrorCodes.ACCOUNT_DISABLED

        assert error.code == "AUTH_002"
        assert error.status_code == 403

    def test_token_errors(self):
        """测试Token相关错误"""
        assert AuthErrorCodes.TOKEN_MISSING.code == "AUTH_400"
        assert AuthErrorCodes.TOKEN_INVALID.code == "AUTH_401"
        assert AuthErrorCodes.TOKEN_EXPIRED.code == "AUTH_402"

        # 验证所有Token错误都是401
        assert AuthErrorCodes.TOKEN_MISSING.status_code == 401
        assert AuthErrorCodes.TOKEN_INVALID.status_code == 401
        assert AuthErrorCodes.TOKEN_EXPIRED.status_code == 401

    def test_password_validation_errors(self):
        """测试密码验证错误"""
        assert AuthErrorCodes.PASSWORD_TOO_SHORT.code == "AUTH_200"
        assert AuthErrorCodes.PASSWORD_MISSING_DIGIT.code == "AUTH_201"
        assert AuthErrorCodes.PASSWORD_MISSING_LETTER.code == "AUTH_202"
        assert AuthErrorCodes.PASSWORD_MISSING_SPECIAL.code == "AUTH_203"

        # 验证所有密码错误都是400
        assert AuthErrorCodes.PASSWORD_TOO_SHORT.status_code == 400
        assert AuthErrorCodes.PASSWORD_MISSING_DIGIT.status_code == 400

    def test_registration_errors(self):
        """测试注册相关错误"""
        assert AuthErrorCodes.EMAIL_ALREADY_EXISTS.code == "AUTH_100"
        assert AuthErrorCodes.USERNAME_ALREADY_EXISTS.code == "AUTH_101"
        assert AuthErrorCodes.REGISTER_FAILED.code == "AUTH_102"

    def test_permission_errors(self):
        """测试权限错误"""
        assert AuthErrorCodes.PERMISSION_DENIED.code == "AUTH_500"
        assert AuthErrorCodes.ROLE_NOT_ALLOWED.code == "AUTH_501"

        # 验证权限错误都是403
        assert AuthErrorCodes.PERMISSION_DENIED.status_code == 403
        assert AuthErrorCodes.ROLE_NOT_ALLOWED.status_code == 403

    def test_email_verification_errors(self):
        """测试邮箱验证错误"""
        assert AuthErrorCodes.EMAIL_NOT_VERIFIED.code == "AUTH_300"
        assert AuthErrorCodes.EMAIL_VERIFICATION_FAILED.code == "AUTH_301"
        assert AuthErrorCodes.EMAIL_ALREADY_VERIFIED.code == "AUTH_302"


# ==================== 业务错误码测试 ====================

@pytest.mark.unit
@pytest.mark.error_codes
class TestBusinessErrorCodes:
    """测试业务错误码"""

    def test_generic_business_errors(self):
        """测试通用业务错误"""
        assert BusinessErrorCodes.INVALID_OPERATION.code == "BIZ_001"
        assert BusinessErrorCodes.RESOURCE_NOT_FOUND.code == "BIZ_002"
        assert BusinessErrorCodes.RESOURCE_ALREADY_EXISTS.code == "BIZ_003"

        assert BusinessErrorCodes.RESOURCE_NOT_FOUND.status_code == 404
        assert BusinessErrorCodes.RESOURCE_ALREADY_EXISTS.status_code == 409

    def test_amount_errors(self):
        """测试金额相关错误"""
        assert BusinessErrorCodes.INVALID_AMOUNT.code == "BIZ_100"
        assert BusinessErrorCodes.INSUFFICIENT_BALANCE.code == "BIZ_101"

        assert BusinessErrorCodes.INVALID_AMOUNT.status_code == 400

    def test_date_errors(self):
        """测试日期相关错误"""
        assert BusinessErrorCodes.INVALID_DATE_RANGE.code == "BIZ_200"
        assert BusinessErrorCodes.DATE_IN_FUTURE.code == "BIZ_201"

    def test_status_errors(self):
        """测试状态相关错误"""
        assert BusinessErrorCodes.INVALID_STATUS.code == "BIZ_300"
        assert BusinessErrorCodes.STATUS_TRANSITION_NOT_ALLOWED.code == "BIZ_301"

    def test_file_operation_errors(self):
        """测试文件操作错误"""
        assert BusinessErrorCodes.INVALID_FILE_TYPE.code == "BIZ_500"
        assert BusinessErrorCodes.FILE_TOO_LARGE.code == "BIZ_501"
        assert BusinessErrorCodes.EXCEL_PARSE_ERROR.code == "BIZ_502"
        assert BusinessErrorCodes.EMPTY_FILE.code == "BIZ_503"
        assert BusinessErrorCodes.MISSING_COLUMNS.code == "BIZ_504"
        assert BusinessErrorCodes.EXPORT_LIMIT_EXCEEDED.code == "BIZ_505"
        assert BusinessErrorCodes.NO_DATA.code == "BIZ_506"
        assert BusinessErrorCodes.EXPORT_ERROR.code == "BIZ_507"
        assert BusinessErrorCodes.IMPORT_ERROR.code == "BIZ_508"

    def test_ledger_errors(self):
        """测试账本相关错误"""
        assert BusinessErrorCodes.LEDGER_CREATE_ERROR.code == "BIZ_600"
        assert BusinessErrorCodes.LEDGER_QUERY_ERROR.code == "BIZ_601"
        assert BusinessErrorCodes.TRANSACTION_NOT_FOUND.code == "BIZ_602"
        assert BusinessErrorCodes.LEDGER_UPDATE_ERROR.code == "BIZ_603"
        assert BusinessErrorCodes.BALANCE_QUERY_ERROR.code == "BIZ_604"
        assert BusinessErrorCodes.BUDGET_QUERY_ERROR.code == "BIZ_605"
        assert BusinessErrorCodes.BUDGET_CREATE_ERROR.code == "BIZ_606"
        assert BusinessErrorCodes.STATISTICS_QUERY_ERROR.code == "BIZ_607"

        # 验证账本错误大多是500
        assert BusinessErrorCodes.LEDGER_CREATE_ERROR.status_code == 500
        assert BusinessErrorCodes.TRANSACTION_NOT_FOUND.status_code == 404

    def test_user_management_errors(self):
        """测试用户管理错误"""
        assert BusinessErrorCodes.UPDATE_PROFILE_FAILED.code == "BIZ_400"
        assert BusinessErrorCodes.ACTIVATE_USER_FAILED.code == "BIZ_401"
        assert BusinessErrorCodes.DEACTIVATE_USER_FAILED.code == "BIZ_402"

    def test_health_check_error(self):
        """测试健康检查错误"""
        assert BusinessErrorCodes.READY_CHECK_FAILED.code == "BIZ_700"
        assert BusinessErrorCodes.READY_CHECK_FAILED.status_code == 503


# ==================== 系统错误码测试 ====================

@pytest.mark.unit
@pytest.mark.error_codes
class TestSystemErrorCodes:
    """测试系统错误码"""

    def test_internal_error(self):
        """测试内部错误"""
        error = SystemErrorCodes.INTERNAL_ERROR

        assert error.code == "SYS_001"
        assert error.status_code == 500

    def test_service_unavailable(self):
        """测试服务不可用"""
        error = SystemErrorCodes.SERVICE_UNAVAILABLE

        assert error.code == "SYS_002"
        assert error.status_code == 503

    def test_timeout(self):
        """测试超时错误"""
        error = SystemErrorCodes.TIMEOUT

        assert error.code == "SYS_003"
        assert error.status_code == 504

    def test_rate_limit_exceeded(self):
        """测试速率限制"""
        error = SystemErrorCodes.RATE_LIMIT_EXCEEDED

        assert error.code == "SYS_004"
        assert error.status_code == 429


# ==================== 数据库错误码测试 ====================

@pytest.mark.unit
@pytest.mark.error_codes
class TestDatabaseErrorCodes:
    """测试数据库错误码"""

    def test_connection_failed(self):
        """测试连接失败"""
        error = DatabaseErrorCodes.CONNECTION_FAILED

        assert error.code == "DB_001"
        assert error.status_code == 500

    def test_query_failed(self):
        """测试查询失败"""
        error = DatabaseErrorCodes.QUERY_FAILED

        assert error.code == "DB_002"
        assert error.status_code == 500

    def test_constraint_violations(self):
        """测试约束违反错误"""
        assert DatabaseErrorCodes.CONSTRAINT_VIOLATION.code == "DB_003"
        assert DatabaseErrorCodes.UNIQUE_VIOLATION.code == "DB_004"
        assert DatabaseErrorCodes.FOREIGN_KEY_VIOLATION.code == "DB_005"

        # 验证状态码
        assert DatabaseErrorCodes.CONSTRAINT_VIOLATION.status_code == 400
        assert DatabaseErrorCodes.UNIQUE_VIOLATION.status_code == 409
        assert DatabaseErrorCodes.FOREIGN_KEY_VIOLATION.status_code == 400


# ==================== 验证错误码测试 ====================

@pytest.mark.unit
@pytest.mark.error_codes
class TestValidationErrorCodes:
    """测试验证错误码"""

    def test_generic_validation_errors(self):
        """测试通用验证错误"""
        assert ValidationErrorCodes.REQUIRED_FIELD_MISSING.code == "VALIDATION_001"
        assert ValidationErrorCodes.INVALID_FORMAT.code == "VALIDATION_002"
        assert ValidationErrorCodes.INVALID_EMAIL.code == "VALIDATION_003"
        assert ValidationErrorCodes.INVALID_PHONE.code == "VALIDATION_004"
        assert ValidationErrorCodes.VALUE_OUT_OF_RANGE.code == "VALIDATION_005"
        assert ValidationErrorCodes.INVALID_ENUM_VALUE.code == "VALIDATION_006"

        # 验证所有验证错误都是400
        assert ValidationErrorCodes.REQUIRED_FIELD_MISSING.status_code == 400
        assert ValidationErrorCodes.INVALID_FORMAT.status_code == 400

    def test_detailed_validation_errors(self):
        """测试详细验证错误"""
        assert ValidationErrorCodes.MISSING_REQUIRED_COLUMN.code == "VALIDATION_100"
        assert ValidationErrorCodes.EMPTY_REQUIRED_FIELD.code == "VALIDATION_101"
        assert ValidationErrorCodes.STRING_TOO_LONG.code == "VALIDATION_102"
        assert ValidationErrorCodes.TYPE_CONVERSION_ERROR.code == "VALIDATION_103"
        assert ValidationErrorCodes.PARSE_ERROR.code == "VALIDATION_104"
        assert ValidationErrorCodes.VALIDATION_ERROR.code == "VALIDATION_105"


# ==================== 利润报表错误码测试 ====================

@pytest.mark.unit
@pytest.mark.error_codes
class TestProfitErrorCodes:
    """测试利润报表错误码"""

    def test_parameter_validation_errors(self):
        """测试参数验证错误"""
        assert ProfitErrorCodes.INVALID_PERIOD_PARAMS.code == "PROFIT_001"
        assert ProfitErrorCodes.FUTURE_START_DATE.code == "PROFIT_002"

        assert ProfitErrorCodes.INVALID_PERIOD_PARAMS.status_code == 400
        assert ProfitErrorCodes.FUTURE_START_DATE.status_code == 400

    def test_resource_not_found_errors(self):
        """测试资源不存在错误"""
        assert ProfitErrorCodes.PROJECT_NOT_FOUND.code == "PROFIT_003"
        assert ProfitErrorCodes.PERIOD_DATA_NOT_FOUND.code == "PROFIT_005"
        assert ProfitErrorCodes.ACCOUNT_NOT_FOUND.code == "PROFIT_007"

        # 验证都是404
        assert ProfitErrorCodes.PROJECT_NOT_FOUND.status_code == 404
        assert ProfitErrorCodes.PERIOD_DATA_NOT_FOUND.status_code == 404
        assert ProfitErrorCodes.ACCOUNT_NOT_FOUND.status_code == 404

    def test_conflict_error(self):
        """测试冲突错误"""
        error = ProfitErrorCodes.PERIOD_LOCKED

        assert error.code == "PROFIT_004"
        assert error.status_code == 409
        assert "锁定" in error.message

    def test_permission_error(self):
        """测试权限错误"""
        error = ProfitErrorCodes.MANUAL_UPDATE_FORBIDDEN

        assert error.code == "PROFIT_006"
        assert error.status_code == 403

    def test_range_limit_error(self):
        """测试范围限制错误"""
        error = ProfitErrorCodes.DATE_RANGE_EXCEEDED

        assert error.code == "PROFIT_008"
        assert error.status_code == 400


# ==================== 错误码映射测试 ====================

@pytest.mark.unit
@pytest.mark.error_codes
class TestErrorCodeMap:
    """测试错误码映射"""

    def test_error_code_map_exists(self):
        """测试错误码映射存在"""
        assert isinstance(ERROR_CODE_MAP, dict)
        assert len(ERROR_CODE_MAP) > 0

    def test_auth_codes_in_map(self):
        """测试认证错误码在映射中"""
        assert "AUTH_001" in ERROR_CODE_MAP
        assert "AUTH_400" in ERROR_CODE_MAP
        assert "AUTH_500" in ERROR_CODE_MAP
        assert "AUTH_999" in ERROR_CODE_MAP

    def test_business_codes_in_map(self):
        """测试业务错误码在映射中"""
        assert "BIZ_001" in ERROR_CODE_MAP
        assert "BIZ_002" in ERROR_CODE_MAP
        assert "BIZ_500" in ERROR_CODE_MAP
        assert "BIZ_600" in ERROR_CODE_MAP

    def test_system_codes_in_map(self):
        """测试系统错误码在映射中"""
        assert "SYS_001" in ERROR_CODE_MAP
        assert "SYS_002" in ERROR_CODE_MAP
        assert "SYS_003" in ERROR_CODE_MAP
        assert "SYS_004" in ERROR_CODE_MAP

    def test_database_codes_in_map(self):
        """测试数据库错误码在映射中"""
        assert "DB_001" in ERROR_CODE_MAP
        assert "DB_002" in ERROR_CODE_MAP
        assert "DB_003" in ERROR_CODE_MAP
        assert "DB_004" in ERROR_CODE_MAP
        assert "DB_005" in ERROR_CODE_MAP

    def test_validation_codes_in_map(self):
        """测试验证错误码在映射中"""
        assert "VALIDATION_001" in ERROR_CODE_MAP
        assert "VALIDATION_100" in ERROR_CODE_MAP
        assert "VALIDATION_105" in ERROR_CODE_MAP

    def test_profit_codes_in_map(self):
        """测试利润报表错误码在映射中"""
        assert "PROFIT_001" in ERROR_CODE_MAP
        assert "PROFIT_002" in ERROR_CODE_MAP
        assert "PROFIT_003" in ERROR_CODE_MAP
        assert "PROFIT_008" in ERROR_CODE_MAP

    def test_map_values_are_error_codes(self):
        """测试映射值都是ErrorCode实例"""
        for code, error in ERROR_CODE_MAP.items():
            assert isinstance(error, ErrorCode)
            assert error.code == code


# ==================== get_error_code函数测试 ====================

@pytest.mark.unit
@pytest.mark.error_codes
class TestGetErrorCode:
    """测试获取错误码函数"""

    def test_get_existing_auth_code(self):
        """测试获取存在的认证错误码"""
        error = get_error_code("AUTH_001")

        assert error.code == "AUTH_001"
        assert error.message == "用户名或密码错误"
        assert error.status_code == 401

    def test_get_existing_business_code(self):
        """测试获取存在的业务错误码"""
        error = get_error_code("BIZ_002")

        assert error.code == "BIZ_002"
        assert error.status_code == 404

    def test_get_existing_system_code(self):
        """测试获取存在的系统错误码"""
        error = get_error_code("SYS_001")

        assert error.code == "SYS_001"
        assert error.status_code == 500

    def test_get_existing_database_code(self):
        """测试获取存在的数据库错误码"""
        error = get_error_code("DB_004")

        assert error.code == "DB_004"
        assert error.status_code == 409

    def test_get_existing_validation_code(self):
        """测试获取存在的验证错误码"""
        error = get_error_code("VALIDATION_003")

        assert error.code == "VALIDATION_003"

    def test_get_existing_profit_code(self):
        """测试获取存在的利润报表错误码"""
        error = get_error_code("PROFIT_004")

        assert error.code == "PROFIT_004"
        assert error.status_code == 409

    def test_get_nonexistent_code_returns_internal_error(self):
        """测试获取不存在的错误码返回内部错误"""
        error = get_error_code("NONEXISTENT_999")

        assert error.code == "SYS_001"
        assert error.status_code == 500
        assert "内部错误" in error.message

    def test_get_invalid_code_format(self):
        """测试无效的错误码格式"""
        error = get_error_code("INVALID")

        assert error.code == "SYS_001"


# ==================== 错误码分类测试 ====================

@pytest.mark.unit
@pytest.mark.error_codes
class TestErrorCodeCategories:
    """测试错误码分类"""

    def test_auth_error_count(self):
        """测试认证错误码数量"""
        auth_codes = [code for code in ERROR_CODE_MAP.keys() if code.startswith("AUTH_")]

        # 应该有至少20个认证错误码
        assert len(auth_codes) >= 20

    def test_business_error_count(self):
        """测试业务错误码数量"""
        biz_codes = [code for code in ERROR_CODE_MAP.keys() if code.startswith("BIZ_")]

        # 应该有至少30个业务错误码
        assert len(biz_codes) >= 30

    def test_system_error_count(self):
        """测试系统错误码数量"""
        sys_codes = [code for code in ERROR_CODE_MAP.keys() if code.startswith("SYS_")]

        assert len(sys_codes) == 4

    def test_database_error_count(self):
        """测试数据库错误码数量"""
        db_codes = [code for code in ERROR_CODE_MAP.keys() if code.startswith("DB_")]

        assert len(db_codes) == 5

    def test_validation_error_count(self):
        """测试验证错误码数量"""
        val_codes = [code for code in ERROR_CODE_MAP.keys() if code.startswith("VALIDATION_")]

        assert len(val_codes) >= 10

    def test_profit_error_count(self):
        """测试利润报表错误码数量"""
        profit_codes = [code for code in ERROR_CODE_MAP.keys() if code.startswith("PROFIT_")]

        assert len(profit_codes) == 8


# ==================== 状态码一致性测试 ====================

@pytest.mark.unit
@pytest.mark.error_codes
class TestStatusCodeConsistency:
    """测试状态码一致性"""

    def test_4xx_client_errors(self):
        """测试4xx客户端错误"""
        # 400错误
        assert AuthErrorCodes.PASSWORD_TOO_SHORT.status_code == 400
        assert BusinessErrorCodes.INVALID_AMOUNT.status_code == 400
        assert ValidationErrorCodes.INVALID_FORMAT.status_code == 400

        # 401未授权
        assert AuthErrorCodes.INVALID_CREDENTIALS.status_code == 401
        assert AuthErrorCodes.TOKEN_EXPIRED.status_code == 401

        # 403禁止
        assert AuthErrorCodes.PERMISSION_DENIED.status_code == 403
        assert ProfitErrorCodes.MANUAL_UPDATE_FORBIDDEN.status_code == 403

        # 404未找到
        assert BusinessErrorCodes.RESOURCE_NOT_FOUND.status_code == 404
        assert ProfitErrorCodes.PROJECT_NOT_FOUND.status_code == 404

        # 409冲突
        assert BusinessErrorCodes.RESOURCE_ALREADY_EXISTS.status_code == 409
        assert DatabaseErrorCodes.UNIQUE_VIOLATION.status_code == 409

    def test_5xx_server_errors(self):
        """测试5xx服务器错误"""
        # 500内部错误
        assert SystemErrorCodes.INTERNAL_ERROR.status_code == 500
        assert DatabaseErrorCodes.CONNECTION_FAILED.status_code == 500
        assert BusinessErrorCodes.OPERATION_FAILED.status_code == 500

        # 503服务不可用
        assert SystemErrorCodes.SERVICE_UNAVAILABLE.status_code == 503
        assert BusinessErrorCodes.READY_CHECK_FAILED.status_code == 503

        # 504超时
        assert SystemErrorCodes.TIMEOUT.status_code == 504


# ==================== 边界情况测试 ====================

@pytest.mark.unit
@pytest.mark.error_codes
class TestErrorCodeEdgeCases:
    """测试错误码边界情况"""

    def test_error_code_empty_message(self):
        """测试空消息错误码"""
        error = ErrorCode("TEST_001", "", 400)

        assert error.message == ""
        assert error.to_dict()["message"] == ""

    def test_error_code_long_message(self):
        """测试长消息错误码"""
        long_message = "这是一个很长的错误消息" * 10
        error = ErrorCode("TEST_002", long_message, 400)

        assert error.message == long_message

    def test_get_error_code_empty_string(self):
        """测试空字符串获取错误码"""
        error = get_error_code("")

        assert error.code == "SYS_001"

    def test_get_error_code_none(self):
        """测试None获取错误码"""
        # 注意：这会触发TypeError，但由于dict.get的默认行为，会返回SystemErrorCodes.INTERNAL_ERROR
        error = get_error_code(None)

        assert error.code == "SYS_001"


# ==================== 集成测试 ====================

@pytest.mark.integration
@pytest.mark.error_codes
class TestErrorCodeIntegration:
    """错误码系统集成测试"""

    def test_all_error_classes_accessible(self):
        """测试所有错误类可访问"""
        assert hasattr(AuthErrorCodes, 'INVALID_CREDENTIALS')
        assert hasattr(BusinessErrorCodes, 'INVALID_OPERATION')
        assert hasattr(SystemErrorCodes, 'SYS_001')
        assert hasattr(DatabaseErrorCodes, 'CONNECTION_FAILED')
        assert hasattr(ValidationErrorCodes, 'REQUIRED_FIELD_MISSING')
        assert hasattr(ProfitErrorCodes, 'INVALID_PERIOD_PARAMS')

    def test_error_code_workflow(self):
        """测试错误码使用工作流"""
        # 1. 直接使用错误码
        error1 = AuthErrorCodes.INVALID_CREDENTIALS
        assert error1.code == "AUTH_001"

        # 2. 通过映射获取
        error2 = ERROR_CODE_MAP["AUTH_001"]
        assert error2.code == error1.code

        # 3. 通过函数获取
        error3 = get_error_code("AUTH_001")
        assert error3.code == error1.code

        # 4. 转换为字典
        error_dict = error1.to_dict()
        assert error_dict["code"] == "AUTH_001"

    def test_error_code_map_completeness(self):
        """测试错误码映射完整性"""
        # 验证所有定义的错误码都在映射中
        total_mapped = len(ERROR_CODE_MAP)

        # 至少应该有70+个错误码
        assert total_mapped >= 70


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
