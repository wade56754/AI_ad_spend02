"""
error_response 集成测试

测试 Router 层 error_response 的使用是否正确
SoT: ERROR_CODES_SOT.md v2.1

测试覆盖:
1. error_response 函数返回格式
2. 异常类型到错误码的映射
3. HTTP 状态码正确性
4. Router 中异常处理模式
"""

import json
import pytest
from unittest.mock import Mock, patch

# 直接导入，不依赖 conftest.py
import sys
import os
# 添加项目根目录到 sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from backend.core.response import error_response, success_response
from backend.core.error_codes import (
    AuthErrorCodes,
    BusinessErrorCodes,
    SystemErrorCodes,
    ValidationErrorCodes,
    ErrorCode,
)
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError,
    StateTransitionError,
)


class TestErrorResponseFormat:
    """测试 error_response 返回格式"""

    def test_basic_error_response_structure(self):
        """测试基本错误响应结构"""
        response = error_response(
            message="测试错误消息",
            code="TEST_001",
            status_code=400
        )

        # 验证是 JSONResponse
        assert response.status_code == 400

        # 解析 body
        body = json.loads(response.body.decode())

        # 验证必需字段
        assert body["success"] is False
        assert body["data"] is None
        assert "error" in body
        assert body["error"]["code"] == "TEST_001"
        assert body["error"]["message"] == "测试错误消息"
        assert "request_id" in body
        assert "timestamp" in body

    def test_error_response_with_default_code(self):
        """测试默认错误码 SYS_001"""
        response = error_response(message="系统错误")

        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "SYS_001"
        assert response.status_code == 400

    def test_error_response_with_custom_status_code(self):
        """测试自定义 HTTP 状态码"""
        test_cases = [
            (400, "BIZ_001"),
            (401, "AUTH_401"),
            (403, "AUTH_500"),
            (404, "BIZ_002"),
            (409, "BIZ_003"),
            (500, "SYS_001"),
        ]

        for status_code, code in test_cases:
            response = error_response(
                message="测试",
                code=code,
                status_code=status_code
            )
            assert response.status_code == status_code, f"Failed for {code}"

    def test_error_response_with_extra_kwargs(self):
        """测试附加参数"""
        response = error_response(
            message="测试错误",
            code="TEST_001",
            status_code=400,
            details={"field": "name", "reason": "required"}
        )

        body = json.loads(response.body.decode())
        assert body["details"]["field"] == "name"
        assert body["details"]["reason"] == "required"


class TestErrorCodeMapping:
    """测试错误码映射"""

    def test_auth_error_codes(self):
        """测试认证错误码"""
        test_cases = [
            (AuthErrorCodes.INVALID_CREDENTIALS, 401, "AUTH_001"),
            (AuthErrorCodes.ACCOUNT_DISABLED, 403, "AUTH_002"),
            (AuthErrorCodes.TOKEN_EXPIRED, 401, "AUTH_402"),
            (AuthErrorCodes.PERMISSION_DENIED, 403, "AUTH_500"),
        ]

        for error_code, expected_status, expected_code in test_cases:
            assert error_code.code == expected_code
            assert error_code.status_code == expected_status

    def test_business_error_codes(self):
        """测试业务错误码"""
        test_cases = [
            (BusinessErrorCodes.INVALID_OPERATION, 400, "BIZ_001"),
            (BusinessErrorCodes.RESOURCE_NOT_FOUND, 404, "BIZ_002"),
            (BusinessErrorCodes.RESOURCE_ALREADY_EXISTS, 409, "BIZ_003"),
            (BusinessErrorCodes.INSUFFICIENT_BALANCE, 400, "BIZ_101"),
            (BusinessErrorCodes.STATUS_TRANSITION_NOT_ALLOWED, 400, "BIZ_301"),
        ]

        for error_code, expected_status, expected_code in test_cases:
            assert error_code.code == expected_code
            assert error_code.status_code == expected_status

    def test_system_error_codes(self):
        """测试系统错误码"""
        test_cases = [
            (SystemErrorCodes.INTERNAL_ERROR, 500, "SYS_001"),
            (SystemErrorCodes.SERVICE_UNAVAILABLE, 503, "SYS_002"),
            (SystemErrorCodes.TIMEOUT, 504, "SYS_003"),
            (SystemErrorCodes.RATE_LIMIT_EXCEEDED, 429, "SYS_004"),
        ]

        for error_code, expected_status, expected_code in test_cases:
            assert error_code.code == expected_code
            assert error_code.status_code == expected_status

    def test_validation_error_codes(self):
        """测试验证错误码"""
        test_cases = [
            (ValidationErrorCodes.REQUIRED_FIELD_MISSING, 400, "VALIDATION_001"),
            (ValidationErrorCodes.INVALID_FORMAT, 400, "VALIDATION_002"),
            (ValidationErrorCodes.INVALID_EMAIL, 400, "VALIDATION_003"),
            (ValidationErrorCodes.INVALID_PHONE, 400, "VALIDATION_004"),
            (ValidationErrorCodes.VALUE_OUT_OF_RANGE, 400, "VALIDATION_005"),
        ]

        for error_code, expected_status, expected_code in test_cases:
            assert error_code.code == expected_code
            assert error_code.status_code == expected_status


class TestExceptionToErrorMapping:
    """测试异常到 error_response 的映射模式"""

    def test_permission_denied_error_mapping(self):
        """测试 PermissionDeniedError 映射"""
        # 模拟 Router 中的异常处理
        try:
            raise PermissionDeniedError("权限不足")
        except PermissionDeniedError as e:
            response = error_response(
                code="AUTH_500",
                message=str(e),
                status_code=403
            )

        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "AUTH_500"
        assert response.status_code == 403

    def test_resource_not_found_error_mapping(self):
        """测试 ResourceNotFoundError 映射"""
        try:
            raise ResourceNotFoundError("资源不存在")
        except ResourceNotFoundError as e:
            response = error_response(
                code="SYS_004",
                message=str(e),
                status_code=404
            )

        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "SYS_004"
        assert response.status_code == 404

    def test_business_logic_error_mapping(self):
        """测试 BusinessLogicError 映射"""
        try:
            raise BusinessLogicError("业务规则违反")
        except BusinessLogicError as e:
            response = error_response(
                code="BIZ_001",
                message=str(e),
                status_code=400
            )

        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "BIZ_001"
        assert response.status_code == 400

    def test_resource_conflict_error_mapping(self):
        """测试 ResourceConflictError 映射"""
        try:
            raise ResourceConflictError("资源冲突")
        except ResourceConflictError as e:
            response = error_response(
                code="BIZ_003",
                message=str(e),
                status_code=409
            )

        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "BIZ_003"
        assert response.status_code == 409

    def test_state_transition_error_mapping(self):
        """测试 StateTransitionError 映射"""
        try:
            raise StateTransitionError(message="状态转换不允许: draft -> completed")
        except StateTransitionError as e:
            response = error_response(
                code="STATE_400",
                message=str(e),
                status_code=400
            )

        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "STATE_400"
        assert response.status_code == 400

    def test_generic_exception_mapping(self):
        """测试通用 Exception 映射"""
        try:
            raise Exception("未知错误")
        except Exception as e:
            response = error_response(
                code=SystemErrorCodes.INTERNAL_ERROR.code,
                message=f"系统错误: {str(e)}",
                status_code=500
            )

        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "SYS_001"
        assert response.status_code == 500


class TestRouterErrorPatterns:
    """测试 Router 中常见的 error_response 使用模式"""

    def test_create_endpoint_error_pattern(self):
        """测试创建端点的错误处理模式"""
        # 模拟创建端点的异常处理
        exception_mappings = [
            (PermissionDeniedError("无权限"), "AUTH_500", 403),
            (ResourceNotFoundError("关联资源不存在"), "SYS_004", 404),
            (BusinessLogicError("业务规则违反"), "BIZ_001", 400),
            (ValueError("参数无效"), "VALIDATION_001", 400),
        ]

        for exception, expected_code, expected_status in exception_mappings:
            try:
                raise exception
            except PermissionDeniedError:
                response = error_response(code="AUTH_500", message=str(exception), status_code=403)
            except ResourceNotFoundError:
                response = error_response(code="SYS_004", message=str(exception), status_code=404)
            except BusinessLogicError:
                response = error_response(code="BIZ_001", message=str(exception), status_code=400)
            except ValueError:
                response = error_response(code="VALIDATION_001", message=str(exception), status_code=400)

            body = json.loads(response.body.decode())
            assert body["error"]["code"] == expected_code
            assert response.status_code == expected_status

    def test_update_endpoint_error_pattern(self):
        """测试更新端点的错误处理模式"""
        # 更新通常会有状态转换错误
        try:
            raise StateTransitionError(message="不允许跳过 approved 状态: pending -> completed")
        except StateTransitionError as e:
            response = error_response(
                code="STATE_400",
                message=str(e),
                status_code=400
            )

        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "STATE_400"
        assert "不允许" in body["error"]["message"]

    def test_delete_endpoint_error_pattern(self):
        """测试删除端点的错误处理模式"""
        # 删除不存在的资源
        try:
            raise ResourceNotFoundError("记录不存在或已被删除")
        except ResourceNotFoundError as e:
            response = error_response(
                code="SYS_004",
                message=str(e),
                status_code=404
            )

        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "SYS_004"
        assert response.status_code == 404

    def test_list_endpoint_error_pattern(self):
        """测试列表端点的错误处理模式"""
        # 列表端点通常捕获通用异常
        try:
            raise Exception("数据库连接失败")
        except Exception as e:
            response = error_response(
                code=SystemErrorCodes.INTERNAL_ERROR.code,
                message=f"获取列表失败: {str(e)}",
                status_code=500
            )

        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "SYS_001"
        assert response.status_code == 500


class TestSuccessResponseComparison:
    """测试 success_response 与 error_response 的对比"""

    def test_success_vs_error_structure(self):
        """测试成功和错误响应的结构差异"""
        success = success_response(data={"id": 1}, message="操作成功")
        error = error_response(message="操作失败", code="BIZ_001")

        success_body = json.loads(success.body.decode())
        error_body = json.loads(error.body.decode())

        # 成功响应
        assert success_body["success"] is True
        assert success_body["data"] == {"id": 1}
        assert "error" not in success_body or success_body.get("error") is None

        # 错误响应
        assert error_body["success"] is False
        assert error_body["data"] is None
        assert "error" in error_body
        assert error_body["error"]["code"] == "BIZ_001"

    def test_both_have_request_id_and_timestamp(self):
        """测试两者都有 request_id 和 timestamp"""
        success = success_response(data={})
        error = error_response(message="错误")

        for response in [success, error]:
            body = json.loads(response.body.decode())
            assert "request_id" in body
            assert "timestamp" in body
            assert len(body["request_id"]) == 36  # UUID 格式


class TestErrorCodeClass:
    """测试 ErrorCode 类"""

    def test_error_code_to_dict(self):
        """测试 to_dict 方法"""
        error = ErrorCode("TEST_001", "测试消息", 400)
        result = error.to_dict()

        assert result["code"] == "TEST_001"
        assert result["message"] == "测试消息"
        assert result["status_code"] == 400

    def test_error_code_default_status(self):
        """测试默认状态码"""
        error = ErrorCode("TEST_002", "测试")
        assert error.status_code == 400

    def test_error_code_attributes(self):
        """测试属性访问"""
        error = ErrorCode("TEST_003", "测试消息", 500)
        assert error.code == "TEST_003"
        assert error.message == "测试消息"
        assert error.status_code == 500


# ============================================
# 独立运行入口
# ============================================

if __name__ == "__main__":
    """独立运行测试"""
    import traceback

    test_classes = [
        TestErrorResponseFormat,
        TestErrorCodeMapping,
        TestExceptionToErrorMapping,
        TestRouterErrorPatterns,
        TestSuccessResponseComparison,
        TestErrorCodeClass,
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    print("=" * 60)
    print("ERROR_RESPONSE INTEGRATION TEST SUITE")
    print("=" * 60)

    for test_class in test_classes:
        print(f"\n{test_class.__name__}")
        print("-" * 40)

        instance = test_class()
        test_methods = [m for m in dir(instance) if m.startswith("test_")]

        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(instance, method_name)
                method()
                print(f"  [PASS] {method_name}")
                passed_tests += 1
            except Exception as e:
                print(f"  [FAIL] {method_name}: {str(e)}")
                failed_tests.append((test_class.__name__, method_name, str(e)))

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed_tests}/{total_tests} passed")
    print("=" * 60)

    if failed_tests:
        print("\nFailed tests:")
        for cls, method, error in failed_tests:
            print(f"  - {cls}.{method}: {error}")
        sys.exit(1)
    else:
        print("\n[SUCCESS] All tests passed!")
        sys.exit(0)
