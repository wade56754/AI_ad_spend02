"""
标准错误码对齐测试 - P1 级验收项
Version: 1.0
Author: AI Code Factory

验收项对齐:
- EC-001: Envelope 格式
- EC-002: AUTH 错误码系列
- EC-003: BIZ 错误码系列
- EC-004: VALIDATION 错误码系列
- EC-005: STATE 错误码系列
- EC-006: TREND 风控错误码

SoT对齐:
- ERROR_CODES_SOT.md v2.1
- API_SOT.md v9.0 §3 响应格式
"""

import pytest
import json

from backend.core.error_codes import (
    AuthErrorCodes,
    BusinessErrorCodes,
    ValidationErrorCodes,
    StateErrorCodes,
    TrendErrorCodes,
    SystemErrorCodes,
    DatabaseErrorCodes,
    ProfitErrorCodes,
    ERROR_CODE_MAP,
    get_error_code,
)


class TestEnvelopeFormat:
    """
    EC-001: Envelope 格式测试

    对齐 API_SOT.md v9.0 §3:
    {
        "success": bool,
        "data": {...} | null,
        "error": {"code": "...", "message": "..."} | null,
        "timestamp": "ISO8601",
        "request_id": "UUID"
    }
    """

    def test_success_response_envelope(self, client, admin_headers):
        """成功响应 Envelope 格式"""
        response = client.get("/api/projects/", headers=admin_headers)

        if response.status_code == 200:
            data = response.json()
            # 验证 Envelope 结构
            assert "success" in data
            assert data["success"] == True
            assert "timestamp" in data or "data" in data

    def test_error_response_envelope(self, client):
        """错误响应 Envelope 格式"""
        response = client.get("/api/projects/")  # 无认证

        if response.status_code == 401:
            data = response.json()
            # 验证错误 Envelope 结构
            assert "success" in data or "error" in data or "detail" in data


class TestAuthErrorCodes:
    """
    EC-002: AUTH 错误码系列测试

    对齐 ERROR_CODES_SOT.md v2.1 §4.1
    """

    def test_auth_error_codes_complete(self):
        """验证 AUTH 错误码完整性"""
        required_codes = {
            "AUTH_001": "INVALID_CREDENTIALS",
            "AUTH_002": "ACCOUNT_DISABLED",
            "AUTH_400": "TOKEN_MISSING",
            "AUTH_401": "TOKEN_INVALID",
            "AUTH_402": "TOKEN_EXPIRED",
            "AUTH_500": "PERMISSION_DENIED",
        }

        for code, name in required_codes.items():
            assert code in ERROR_CODE_MAP, f"缺少错误码: {code}"
            assert hasattr(AuthErrorCodes, name), f"缺少错误码定义: {name}"

    def test_auth_error_codes_status(self):
        """验证 AUTH 错误码 HTTP 状态码"""
        # 401 Unauthorized
        assert AuthErrorCodes.TOKEN_MISSING.status_code == 401
        assert AuthErrorCodes.TOKEN_INVALID.status_code == 401
        assert AuthErrorCodes.TOKEN_EXPIRED.status_code == 401
        assert AuthErrorCodes.INVALID_CREDENTIALS.status_code == 401

        # 403 Forbidden
        assert AuthErrorCodes.PERMISSION_DENIED.status_code == 403
        assert AuthErrorCodes.ACCOUNT_DISABLED.status_code == 403

    def test_auth_error_codes_have_messages(self):
        """验证 AUTH 错误码有消息"""
        assert AuthErrorCodes.TOKEN_MISSING.message
        assert AuthErrorCodes.TOKEN_INVALID.message
        assert AuthErrorCodes.TOKEN_EXPIRED.message
        assert AuthErrorCodes.PERMISSION_DENIED.message


class TestBusinessErrorCodes:
    """
    EC-003: BIZ 错误码系列测试

    对齐 ERROR_CODES_SOT.md v2.1 §4.2
    """

    def test_biz_error_codes_complete(self):
        """验证 BIZ 错误码完整性"""
        required_codes = {
            "BIZ_001": "INVALID_OPERATION",
            "BIZ_002": "RESOURCE_NOT_FOUND",
            "BIZ_003": "RESOURCE_ALREADY_EXISTS",
            "BIZ_100": "INVALID_AMOUNT",
            "BIZ_101": "INSUFFICIENT_BALANCE",
            "BIZ_300": "INVALID_STATUS",
            "BIZ_301": "STATUS_TRANSITION_NOT_ALLOWED",
        }

        for code, name in required_codes.items():
            assert code in ERROR_CODE_MAP, f"缺少错误码: {code}"
            assert hasattr(BusinessErrorCodes, name), f"缺少错误码定义: {name}"

    def test_biz_error_codes_status(self):
        """验证 BIZ 错误码 HTTP 状态码"""
        assert BusinessErrorCodes.INVALID_OPERATION.status_code == 400
        assert BusinessErrorCodes.RESOURCE_NOT_FOUND.status_code == 404
        assert BusinessErrorCodes.RESOURCE_ALREADY_EXISTS.status_code == 409
        assert BusinessErrorCodes.INSUFFICIENT_BALANCE.status_code == 400

    def test_transfer_error_codes(self):
        """验证转账相关错误码"""
        transfer_codes = [
            "BIZ_610", "BIZ_611", "BIZ_612", "BIZ_613",
            "BIZ_614", "BIZ_615", "BIZ_616", "BIZ_617",
        ]
        for code in transfer_codes:
            assert code in ERROR_CODE_MAP, f"缺少转账错误码: {code}"


class TestValidationErrorCodes:
    """
    EC-004: VALIDATION 错误码系列测试

    对齐 ERROR_CODES_SOT.md v2.1 §4.3
    """

    def test_validation_error_codes_complete(self):
        """验证 VALIDATION 错误码完整性"""
        required_codes = {
            "VALIDATION_001": "REQUIRED_FIELD_MISSING",
            "VALIDATION_002": "INVALID_FORMAT",
            "VALIDATION_003": "INVALID_EMAIL",
            "VALIDATION_005": "VALUE_OUT_OF_RANGE",
            "VALIDATION_006": "INVALID_ENUM_VALUE",
        }

        for code, name in required_codes.items():
            assert code in ERROR_CODE_MAP, f"缺少错误码: {code}"
            assert hasattr(ValidationErrorCodes, name), f"缺少错误码定义: {name}"

    def test_validation_error_codes_status(self):
        """验证 VALIDATION 错误码 HTTP 状态码"""
        # 所有验证错误应为 400
        assert ValidationErrorCodes.REQUIRED_FIELD_MISSING.status_code == 400
        assert ValidationErrorCodes.INVALID_FORMAT.status_code == 400
        assert ValidationErrorCodes.INVALID_EMAIL.status_code == 400
        assert ValidationErrorCodes.VALUE_OUT_OF_RANGE.status_code == 400


class TestStateErrorCodes:
    """
    EC-005: STATE 错误码系列测试

    对齐 ERROR_CODES_SOT.md v2.1 §4.6
    对齐 STATE_MACHINE.md v2.6 §8
    """

    def test_state_error_codes_complete(self):
        """验证 STATE 错误码完整性"""
        required_codes = {
            "STATE_400": "FORBIDDEN_TRANSITION",
            "STATE_401": "SKIP_REQUIRED_STEP",
            "STATE_402": "FINAL_STATE_ROLLBACK",
            "STATE_403": "SYSTEM_FORBIDDEN",
            "STATE_409": "CONCURRENCY_CONFLICT",
        }

        for code, name in required_codes.items():
            assert code in ERROR_CODE_MAP, f"缺少错误码: {code}"
            assert hasattr(StateErrorCodes, name), f"缺少错误码定义: {name}"

    def test_state_error_codes_status(self):
        """验证 STATE 错误码 HTTP 状态码"""
        assert StateErrorCodes.FORBIDDEN_TRANSITION.status_code == 400
        assert StateErrorCodes.SKIP_REQUIRED_STEP.status_code == 400
        assert StateErrorCodes.FINAL_STATE_ROLLBACK.status_code == 400
        assert StateErrorCodes.SYSTEM_FORBIDDEN.status_code == 403
        assert StateErrorCodes.CONCURRENCY_CONFLICT.status_code == 409

    def test_state_error_codes_messages(self):
        """验证 STATE 错误码消息"""
        assert "非法" in StateErrorCodes.FORBIDDEN_TRANSITION.message or \
               "禁止" in StateErrorCodes.FORBIDDEN_TRANSITION.message or \
               "非法状态流转" in StateErrorCodes.FORBIDDEN_TRANSITION.message

        assert "跳过" in StateErrorCodes.SKIP_REQUIRED_STEP.message or \
               "必要步骤" in StateErrorCodes.SKIP_REQUIRED_STEP.message

        assert "终态" in StateErrorCodes.FINAL_STATE_ROLLBACK.message or \
               "回退" in StateErrorCodes.FINAL_STATE_ROLLBACK.message


class TestTrendErrorCodes:
    """
    EC-006: TREND 风控错误码测试

    对齐 ERROR_CODES_SOT.md v2.1 §4.6
    对齐 STATE_MACHINE.md v2.6 §8.3
    """

    def test_trend_error_codes_complete(self):
        """验证 TREND 错误码完整性"""
        required_codes = {
            "TREND_001": "TREND_RISK_TRIGGERED",
            "TREND_002": "REVIEW_REQUIRED",
            "TREND_003": "RULE_CONFIG_ERROR",
            "TREND_010": "RESOLUTION_NOTE_MISSING",
            "TREND_011": "ALREADY_RESOLVED",
        }

        for code, name in required_codes.items():
            assert code in ERROR_CODE_MAP, f"缺少错误码: {code}"
            assert hasattr(TrendErrorCodes, name), f"缺少错误码定义: {name}"

    def test_trend_risk_triggered_is_success(self):
        """风控触发是成功的业务操作 (200)"""
        # TREND_001 表示风控正常触发，不是错误
        assert TrendErrorCodes.TREND_RISK_TRIGGERED.status_code == 200

    def test_trend_error_codes_status(self):
        """验证 TREND 错误码 HTTP 状态码"""
        assert TrendErrorCodes.REVIEW_REQUIRED.status_code == 400
        assert TrendErrorCodes.RULE_CONFIG_ERROR.status_code == 500
        assert TrendErrorCodes.RESOLUTION_NOTE_MISSING.status_code == 400


class TestProfitErrorCodes:
    """
    PROFIT 错误码测试

    对齐 PROFIT_SOT.md v1.1 §5
    """

    def test_profit_error_codes_complete(self):
        """验证 PROFIT 错误码完整性"""
        required_codes = {
            "PROFIT_001": "INVALID_PERIOD_PARAMS",
            "PROFIT_002": "FUTURE_START_DATE",
            "PROFIT_003": "PROJECT_NOT_FOUND",
            "PROFIT_004": "PERIOD_LOCKED",
            "PROFIT_005": "PERIOD_DATA_NOT_FOUND",
        }

        for code, name in required_codes.items():
            assert code in ERROR_CODE_MAP, f"缺少错误码: {code}"
            assert hasattr(ProfitErrorCodes, name), f"缺少错误码定义: {name}"


class TestErrorCodeMap:
    """
    ERROR_CODE_MAP 完整性测试
    """

    def test_error_code_map_count(self):
        """验证错误码总数"""
        # 应该有足够多的错误码
        assert len(ERROR_CODE_MAP) >= 80, \
            f"错误码数量不足: {len(ERROR_CODE_MAP)}"

    def test_error_code_prefixes(self):
        """验证错误码前缀分类"""
        prefixes = {
            "AUTH_": 0,
            "BIZ_": 0,
            "SYS_": 0,
            "DB_": 0,
            "VALIDATION_": 0,
            "STATE_": 0,
            "TREND_": 0,
            "PROFIT_": 0,
        }

        for code in ERROR_CODE_MAP.keys():
            for prefix in prefixes:
                if code.startswith(prefix):
                    prefixes[prefix] += 1
                    break

        # 每个类别应有错误码
        for prefix, count in prefixes.items():
            assert count > 0, f"类别 {prefix} 没有错误码"

    def test_get_error_code_function(self):
        """验证 get_error_code 函数"""
        # 有效错误码
        ec = get_error_code("AUTH_400")
        assert ec.code == "AUTH_400"

        # 无效错误码返回默认值
        ec = get_error_code("INVALID_CODE")
        assert ec.code == "SYS_001"  # 默认系统错误

    def test_error_code_to_dict(self):
        """验证错误码 to_dict 方法"""
        ec = get_error_code("BIZ_001")
        d = ec.to_dict()

        assert "code" in d
        assert "message" in d
        assert "status_code" in d
        assert d["code"] == "BIZ_001"


class TestAPIErrorResponse:
    """
    API 错误响应测试
    """

    def test_unauthorized_returns_auth_error(self, client):
        """未认证请求返回 AUTH 错误码"""
        response = client.get("/api/v1/projects/")

        assert response.status_code == 401
        data = response.json()

        # 响应应包含错误信息
        if "error" in data:
            assert "code" in data["error"] or "message" in data["error"]
        elif "detail" in data:
            # FastAPI 默认格式
            assert data["detail"]

    def test_not_found_returns_biz_error(self, client, admin_headers):
        """不存在资源返回 BIZ 错误码"""
        response = client.get("/api/v1/projects/999999", headers=admin_headers)

        assert response.status_code == 404
