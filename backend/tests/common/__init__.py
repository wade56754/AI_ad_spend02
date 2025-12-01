# -*- coding: utf-8 -*-
"""
backend/tests/common - 测试公共工具模块

本模块提供测试公共工具，包括：
- factories: 测试数据工厂函数
- state_asserts: 状态机断言辅助函数
- error_helpers: 错误码断言辅助函数

基准文档: AUTOMATION_TEST_SPEC_v1.4.md
SoT 依赖: STATE_MACHINE.md v2.6, ERROR_CODES_SOT.md v2.1, DATA_SCHEMA.md v5.2
"""

from .factories import (
    create_test_project,
    create_test_channel,
    create_test_ad_account,
    create_test_daily_report,
    create_test_topup_request,
)

from .state_asserts import (
    assert_daily_report_state,
    assert_topup_state,
    assert_reconciliation_state,
    assert_state_transition_valid,
)

from .error_helpers import (
    assert_error_code,
    assert_validation_error,
    assert_auth_error,
    assert_business_error,
)

__all__ = [
    # factories
    "create_test_project",
    "create_test_channel",
    "create_test_ad_account",
    "create_test_daily_report",
    "create_test_topup_request",
    # state_asserts
    "assert_daily_report_state",
    "assert_topup_state",
    "assert_reconciliation_state",
    "assert_state_transition_valid",
    # error_helpers
    "assert_error_code",
    "assert_validation_error",
    "assert_auth_error",
    "assert_business_error",
]
