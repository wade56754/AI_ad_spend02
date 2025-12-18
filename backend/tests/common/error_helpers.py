# -*- coding: utf-8 -*-
"""
错误码断言辅助函数

提供错误码验证函数，确保测试符合 ERROR_CODES_SOT.md v2.1 规范。

基准文档: AUTOMATION_TEST_SPEC_v1.4.md 第 3.4 节
SoT 依赖: ERROR_CODES_SOT.md v2.1
"""

from typing import Any, Dict, Optional, Set
import re

# ============================================================================
# 错误码前缀定义
# SoT Ref: ERROR_CODES_SOT.md v2.1 第 2 章
# ============================================================================

ERROR_CODE_PREFIXES: Dict[str, str] = {
    "VAL": "验证错误 (Validation)",
    "AUTH": "认证错误 (Authentication)",
    "PERM": "权限错误 (Permission)",
    "BIZ": "业务错误 (Business)",
    "SYS": "系统错误 (System)",
    "DATA": "数据错误 (Data)",
    "EXT": "外部服务错误 (External)",
    "LED": "账本错误 (Ledger)",
    "RPT": "报表错误 (Report)",
    "TOP": "充值错误 (Topup)",
    "REC": "对账错误 (Reconciliation)",
}

# 错误码格式: PREFIX-NNN (3位数字)
ERROR_CODE_PATTERN = re.compile(r"^([A-Z]+)-(\d{3})$")

# ============================================================================
# 常用错误码
# SoT Ref: ERROR_CODES_SOT.md v2.1 第 3-6 章
# ============================================================================

VALIDATION_ERROR_CODES: Set[str] = {
    "VALIDATION_001",  # 必填字段缺失
    "VALIDATION_002",  # 字段格式错误
    "VALIDATION_003",  # 字段值超出范围
    "VALIDATION_004",  # 字段值不在枚举中
    "VALIDATION_005",  # 关联实体不存在
}

AUTH_ERROR_CODES: Set[str] = {
    "AUTH-001",  # Token 缺失
    "AUTH-002",  # Token 过期
    "AUTH-003",  # Token 无效
    "AUTH-004",  # 用户不存在
    "AUTH-005",  # 密码错误
}

PERM_ERROR_CODES: Set[str] = {
    "PERM-001",  # 无操作权限
    "PERM-002",  # 角色权限不足
    "PERM-003",  # 资源所有权验证失败
}

BUSINESS_ERROR_CODES: Set[str] = {
    "BIZ-001",  # 状态转换非法
    "BIZ-002",  # 金额超出限制
    "BIZ-003",  # 余额不足
    "BIZ-004",  # 重复操作
    "BIZ-005",  # 数据冲突
}


# ============================================================================
# 断言函数
# ============================================================================

def assert_error_code(
    response: Any,
    expected_code: str,
    msg: Optional[str] = None
) -> None:
    """
    断言响应包含预期错误码

    Args:
        response: API 响应对象或字典
        expected_code: 预期错误码 (如 "VALIDATION_001")
        msg: 自定义错误消息

    Raises:
        AssertionError: 错误码不匹配或格式无效

    SoT Ref: ERROR_CODES_SOT.md v2.1
    """
    # 验证错误码格式
    if not ERROR_CODE_PATTERN.match(expected_code):
        raise AssertionError(
            f"无效的错误码格式: {expected_code}。"
            f"期望格式: PREFIX-NNN (如 VAL-001)"
        )

    # 验证前缀有效性
    prefix = expected_code.split("-")[0]
    if prefix not in ERROR_CODE_PREFIXES:
        raise AssertionError(
            f"未知的错误码前缀: {prefix}。"
            f"有效前缀: {list(ERROR_CODE_PREFIXES.keys())}"
        )

    # 提取响应中的错误码
    actual_code = _extract_error_code(response)

    if actual_code != expected_code:
        error_msg = msg or (
            f"错误码断言失败: 期望 '{expected_code}'，实际 '{actual_code}'"
        )
        raise AssertionError(error_msg)


def assert_validation_error(
    response: Any,
    expected_code: Optional[str] = None,
    msg: Optional[str] = None
) -> None:
    """
    断言响应为验证错误 (VAL-xxx)

    Args:
        response: API 响应对象或字典
        expected_code: 预期的具体验证错误码（可选）
        msg: 自定义错误消息

    Raises:
        AssertionError: 不是验证错误或错误码不匹配

    SoT Ref: ERROR_CODES_SOT.md v2.1 第 3 章
    """
    actual_code = _extract_error_code(response)

    if not actual_code.startswith("VAL-"):
        error_msg = msg or (
            f"期望验证错误 (VAL-xxx)，实际: '{actual_code}'"
        )
        raise AssertionError(error_msg)

    if expected_code and actual_code != expected_code:
        error_msg = msg or (
            f"验证错误码不匹配: 期望 '{expected_code}'，实际 '{actual_code}'"
        )
        raise AssertionError(error_msg)


def assert_auth_error(
    response: Any,
    expected_code: Optional[str] = None,
    msg: Optional[str] = None
) -> None:
    """
    断言响应为认证错误 (AUTH-xxx)

    Args:
        response: API 响应对象或字典
        expected_code: 预期的具体认证错误码（可选）
        msg: 自定义错误消息

    Raises:
        AssertionError: 不是认证错误或错误码不匹配

    SoT Ref: ERROR_CODES_SOT.md v2.1 第 4 章
    """
    actual_code = _extract_error_code(response)

    if not actual_code.startswith("AUTH-"):
        error_msg = msg or (
            f"期望认证错误 (AUTH-xxx)，实际: '{actual_code}'"
        )
        raise AssertionError(error_msg)

    if expected_code and actual_code != expected_code:
        error_msg = msg or (
            f"认证错误码不匹配: 期望 '{expected_code}'，实际 '{actual_code}'"
        )
        raise AssertionError(error_msg)


def assert_business_error(
    response: Any,
    expected_code: Optional[str] = None,
    msg: Optional[str] = None
) -> None:
    """
    断言响应为业务错误 (BIZ-xxx)

    Args:
        response: API 响应对象或字典
        expected_code: 预期的具体业务错误码（可选）
        msg: 自定义错误消息

    Raises:
        AssertionError: 不是业务错误或错误码不匹配

    SoT Ref: ERROR_CODES_SOT.md v2.1 第 5 章
    """
    actual_code = _extract_error_code(response)

    if not actual_code.startswith("BIZ-"):
        error_msg = msg or (
            f"期望业务错误 (BIZ-xxx)，实际: '{actual_code}'"
        )
        raise AssertionError(error_msg)

    if expected_code and actual_code != expected_code:
        error_msg = msg or (
            f"业务错误码不匹配: 期望 '{expected_code}'，实际 '{actual_code}'"
        )
        raise AssertionError(error_msg)


def _extract_error_code(response: Any) -> str:
    """
    从响应中提取错误码

    支持的响应格式:
    1. httpx.Response: response.json()["code"]
    2. dict: response["code"] 或 response["error"]["code"]
    3. 其他: str(response)
    """
    # httpx.Response 或类似对象
    if hasattr(response, "json"):
        try:
            data = response.json()
            return _extract_code_from_dict(data)
        except Exception:
            pass

    # 字典
    if isinstance(response, dict):
        return _extract_code_from_dict(response)

    # 兜底
    return str(response)


def _extract_code_from_dict(data: Dict[str, Any]) -> str:
    """从字典中提取错误码"""
    # 直接 code 字段
    if "code" in data:
        return str(data["code"])

    # 嵌套 error.code
    if "error" in data and isinstance(data["error"], dict):
        if "code" in data["error"]:
            return str(data["error"]["code"])

    # detail.code (FastAPI 验证错误格式)
    if "detail" in data:
        detail = data["detail"]
        if isinstance(detail, dict) and "code" in detail:
            return str(detail["code"])
        if isinstance(detail, list) and detail:
            first = detail[0]
            if isinstance(first, dict) and "code" in first:
                return str(first["code"])

    return ""
