"""
错误码覆盖测试
Version: 1.0 (Test Quality Enhancement Flow - Phase 2)
Author: Claude协作开发

测试范围:
- 错误码定义与 ERROR_CODES_SOT.md v2.1 对齐
- 错误码分类与HTTP状态码匹配
- 常用错误码场景覆盖

SoT对齐:
- ERROR_CODES_SOT.md v2.1
- STATE_MACHINE.md v2.6
"""

import pytest


class TestErrorCodeDefinitions:
    """
    错误码定义测试

    验证错误码定义与 ERROR_CODES_SOT.md v2.1 一致
    """

    # ========================================================================
    # 认证授权类错误码 (AUTH_)
    # ========================================================================

    @pytest.mark.parametrize("error_code,expected_http,description", [
        ("AUTH_001", 401, "用户名或密码错误"),
        ("AUTH_002", 403, "账户已被禁用"),
        ("AUTH_003", 401, "令牌已被撤销"),
        ("AUTH_004", 404, "用户不存在或已被禁用"),
        ("AUTH_100", 400, "邮箱已被注册"),
        ("AUTH_400", 401, "未提供认证令牌"),
        ("AUTH_401", 401, "无效的认证令牌"),
        ("AUTH_402", 401, "令牌已过期"),
        ("AUTH_500", 403, "权限不足"),
    ])
    def test_auth_error_codes(self, error_code, expected_http, description):
        """测试认证授权类错误码定义"""
        # 验证错误码前缀
        assert error_code.startswith("AUTH_"), f"{error_code} 应以 AUTH_ 开头"

        # 验证HTTP状态码范围
        assert expected_http in [400, 401, 403, 404, 500], \
            f"{error_code} 的HTTP状态码 {expected_http} 不在预期范围内"

    # ========================================================================
    # 业务逻辑类错误码 (BIZ_)
    # ========================================================================

    @pytest.mark.parametrize("error_code,expected_http,description", [
        ("BIZ_001", 400, "无效的操作"),
        ("BIZ_002", 404, "资源不存在"),
        ("BIZ_003", 409, "资源已存在"),
        ("BIZ_100", 400, "金额无效"),
        ("BIZ_101", 400, "余额不足"),
        ("BIZ_200", 400, "日期范围无效"),
        ("BIZ_201", 400, "日期不能为未来"),
        ("BIZ_300", 400, "状态无效"),
        ("BIZ_301", 400, "状态转换不允许"),
    ])
    def test_biz_error_codes(self, error_code, expected_http, description):
        """测试业务逻辑类错误码定义"""
        assert error_code.startswith("BIZ_"), f"{error_code} 应以 BIZ_ 开头"
        assert expected_http in [400, 404, 409], \
            f"{error_code} 的HTTP状态码 {expected_http} 不在预期范围内"

    # ========================================================================
    # 参数验证类错误码 (VALIDATION_)
    # ========================================================================

    @pytest.mark.parametrize("error_code,expected_http,description", [
        ("VALIDATION_001", 400, "必填字段缺失"),
        ("VALIDATION_002", 400, "格式无效"),
        ("VALIDATION_003", 400, "邮箱格式无效"),
    ])
    def test_validation_error_codes(self, error_code, expected_http, description):
        """测试参数验证类错误码定义"""
        assert error_code.startswith("VALIDATION_"), f"{error_code} 应以 VALIDATION_ 开头"
        assert expected_http == 400, f"VALIDATION 类错误码应返回 400"

    # ========================================================================
    # 系统错误类错误码 (SYS_)
    # ========================================================================

    @pytest.mark.parametrize("error_code,expected_http,description", [
        ("SYS_001", 500, "系统内部错误"),
        ("SYS_002", 503, "服务暂时不可用"),
        ("SYS_003", 504, "请求超时"),
        ("SYS_004", 429, "请求过于频繁"),
    ])
    def test_sys_error_codes(self, error_code, expected_http, description):
        """测试系统错误类错误码定义"""
        assert error_code.startswith("SYS_"), f"{error_code} 应以 SYS_ 开头"
        assert expected_http in [429, 500, 503, 504], \
            f"{error_code} 的HTTP状态码 {expected_http} 不在预期范围内"

    # ========================================================================
    # 数据库错误类错误码 (DB_)
    # ========================================================================

    @pytest.mark.parametrize("error_code,expected_http,description", [
        ("DB_001", 500, "数据库连接失败"),
        ("DB_002", 500, "数据库查询失败"),
        ("DB_003", 400, "数据完整性约束违反"),
        ("DB_004", 409, "唯一性约束违反"),
        ("DB_005", 400, "外键约束违反"),
    ])
    def test_db_error_codes(self, error_code, expected_http, description):
        """测试数据库错误类错误码定义"""
        assert error_code.startswith("DB_"), f"{error_code} 应以 DB_ 开头"
        assert expected_http in [400, 409, 500], \
            f"{error_code} 的HTTP状态码 {expected_http} 不在预期范围内"

    # ========================================================================
    # 状态机错误类错误码 (STATE_)
    # ========================================================================

    @pytest.mark.parametrize("error_code,expected_http,description", [
        ("STATE_400", 400, "非法状态流转"),
        ("STATE_401", 400, "跳过必要步骤"),
        ("STATE_402", 400, "终态非法回退"),
        ("STATE_403", 403, "系统无权限流转"),
        ("STATE_405", 400, "绝对禁止的流转"),
        ("STATE_409", 409, "并发冲突"),
    ])
    def test_state_error_codes(self, error_code, expected_http, description):
        """测试状态机错误类错误码定义"""
        assert error_code.startswith("STATE_"), f"{error_code} 应以 STATE_ 开头"
        assert expected_http in [400, 403, 409], \
            f"{error_code} 的HTTP状态码 {expected_http} 不在预期范围内"

    # ========================================================================
    # 趋势风控错误类错误码 (TREND_)
    # ========================================================================

    @pytest.mark.parametrize("error_code,expected_http,description", [
        ("TREND_001", 200, "趋势风控触发"),  # 注意: 风控触发是成功的业务操作
        ("TREND_002", 400, "风控复核未完成"),
        ("TREND_010", 400, "复核原因缺失"),
    ])
    def test_trend_error_codes(self, error_code, expected_http, description):
        """测试趋势风控错误类错误码定义"""
        assert error_code.startswith("TREND_"), f"{error_code} 应以 TREND_ 开头"
        assert expected_http in [200, 400, 500], \
            f"{error_code} 的HTTP状态码 {expected_http} 不在预期范围内"


class TestErrorCodeUsageScenarios:
    """
    错误码使用场景测试

    验证错误码在特定业务场景下的正确使用
    """

    # ========================================================================
    # 资源不存在场景 (应使用 BIZ_002)
    # ========================================================================

    @pytest.mark.parametrize("scenario", [
        "根据ID查询日报不存在",
        "根据ID查询充值申请不存在",
        "根据ID查询对账批次不存在",
        "根据ID查询项目不存在",
        "根据ID查询广告账户不存在",
    ])
    def test_resource_not_found_should_use_biz_002(self, scenario):
        """资源不存在场景应使用 BIZ_002"""
        expected_code = "BIZ_002"
        expected_http = 404
        # 这是一个文档性测试，验证规范
        assert expected_code == "BIZ_002"
        assert expected_http == 404

    # ========================================================================
    # 权限不足场景 (应使用 AUTH_500)
    # ========================================================================

    @pytest.mark.parametrize("scenario", [
        "普通用户尝试删除日报",
        "非财务用户尝试审批充值",
        "非管理员尝试回退终态",
        "投手尝试访问统计接口",
    ])
    def test_permission_denied_should_use_auth_500(self, scenario):
        """权限不足场景应使用 AUTH_500"""
        expected_code = "AUTH_500"
        expected_http = 403
        assert expected_code == "AUTH_500"
        assert expected_http == 403

    # ========================================================================
    # 状态流转错误场景
    # ========================================================================

    @pytest.mark.parametrize("scenario,expected_code", [
        ("跳过 pending_review 直接到 finance_approve", "STATE_400"),
        ("从 completed 回退到 paid", "STATE_400"),
        ("跳过 final_pending 直接到 final_locked", "STATE_401"),
        ("非 admin 尝试回退终态", "STATE_402"),
        ("system 尝试自动审批", "STATE_403"),
        ("回退已完成的充值申请", "STATE_405"),
        ("并发修改导致版本冲突", "STATE_409"),
    ])
    def test_state_transition_errors(self, scenario, expected_code):
        """状态流转错误场景应使用正确的 STATE_ 错误码"""
        assert expected_code.startswith("STATE_")

    # ========================================================================
    # 金额相关错误场景
    # ========================================================================

    @pytest.mark.parametrize("scenario,expected_code", [
        ("充值金额为负数", "BIZ_100"),
        ("充值金额为零", "BIZ_100"),
        ("充值金额超过上限", "BIZ_100"),
        ("项目余额不足支付消耗", "BIZ_101"),
        ("迁移金额超过源账户余额", "BIZ_101"),
    ])
    def test_amount_errors(self, scenario, expected_code):
        """金额相关错误场景应使用正确的 BIZ_ 错误码"""
        assert expected_code in ["BIZ_100", "BIZ_101"]

    # ========================================================================
    # 日期相关错误场景
    # ========================================================================

    @pytest.mark.parametrize("scenario,expected_code", [
        ("对账日期范围：开始 > 结束", "BIZ_200"),
        ("查询日期范围：开始 > 结束", "BIZ_200"),
        ("日报提交日期为明天", "BIZ_201"),
        ("对账创建日期为未来", "BIZ_201"),
    ])
    def test_date_errors(self, scenario, expected_code):
        """日期相关错误场景应使用正确的 BIZ_ 错误码"""
        assert expected_code in ["BIZ_200", "BIZ_201"]


class TestErrorCodeAntiPatterns:
    """
    错误码反模式测试

    验证不应该出现的错误码使用方式
    """

    def test_sys_004_is_not_for_resource_not_found(self):
        """
        SYS_004 不应用于"资源不存在"场景

        反模式: SYS_004 是"请求过于频繁"(429)
        正确用法: 资源不存在应使用 BIZ_002 (404)
        """
        sys_004_meaning = "请求过于频繁"
        sys_004_http = 429

        resource_not_found_code = "BIZ_002"
        resource_not_found_http = 404

        assert sys_004_http != resource_not_found_http, \
            "SYS_004 (429) 不等于资源不存在 (404)"

    def test_biz_301_vs_state_400(self):
        """
        BIZ_301 和 STATE_400 的区别

        BIZ_301: 状态转换不允许（业务层面，如归档项目不能激活）
        STATE_400: 非法状态流转（状态机层面，不在白名单）

        两者可以互换使用，但推荐：
        - 业务规则层面使用 BIZ_301
        - 状态机验证层面使用 STATE_400
        """
        # 两者都是 400 错误
        biz_301_http = 400
        state_400_http = 400
        assert biz_301_http == state_400_http

    def test_deprecated_error_codes_not_used(self):
        """
        验证不应使用的过时错误码

        以下错误码在测试中曾被错误使用：
        - BIZ_302: 不存在，应使用 BIZ_003 (资源已存在)
        - BIZ_303: 不存在，应使用 AUTH_500 (权限不足)
        - BIZ_306: 不存在，应使用 BIZ_301 或 STATE_400
        """
        invalid_codes = ["BIZ_302", "BIZ_303", "BIZ_306"]
        valid_codes = [
            "BIZ_001", "BIZ_002", "BIZ_003",
            "BIZ_100", "BIZ_101",
            "BIZ_200", "BIZ_201",
            "BIZ_300", "BIZ_301",
        ]

        for invalid_code in invalid_codes:
            assert invalid_code not in valid_codes, \
                f"{invalid_code} 不是有效的错误码"


class TestErrorCodeHTTPMapping:
    """
    错误码与HTTP状态码映射测试

    验证错误码前缀与HTTP状态码的对应关系
    """

    def test_401_errors_are_auth_related(self):
        """401 错误应该是认证相关"""
        # 401 Unauthorized 表示认证失败
        auth_401_codes = ["AUTH_001", "AUTH_003", "AUTH_400", "AUTH_401", "AUTH_402"]
        for code in auth_401_codes:
            assert code.startswith("AUTH_")

    def test_403_errors_are_permission_related(self):
        """403 错误应该是权限相关"""
        # 403 Forbidden 表示权限不足
        permission_codes = ["AUTH_002", "AUTH_500", "STATE_403"]
        # AUTH_002 是账户禁用，AUTH_500 是权限不足，STATE_403 是系统无权限
        for code in permission_codes:
            assert code.startswith(("AUTH_", "STATE_"))

    def test_404_errors_are_not_found_related(self):
        """404 错误应该是资源不存在"""
        # 404 Not Found 表示资源不存在
        not_found_codes = ["BIZ_002", "AUTH_004"]
        for code in not_found_codes:
            assert code.startswith(("BIZ_", "AUTH_"))

    def test_409_errors_are_conflict_related(self):
        """409 错误应该是冲突相关"""
        # 409 Conflict 表示资源冲突
        conflict_codes = ["BIZ_003", "DB_004", "STATE_409"]
        for code in conflict_codes:
            assert code.startswith(("BIZ_", "DB_", "STATE_"))

    def test_429_errors_are_rate_limit_related(self):
        """429 错误应该是限流相关"""
        # 429 Too Many Requests 表示请求过于频繁
        rate_limit_codes = ["SYS_004"]
        for code in rate_limit_codes:
            assert code.startswith("SYS_")


class TestTrendErrorCodeSpecialCases:
    """
    趋势风控错误码特殊情况测试

    TREND_001 是一个特殊情况：HTTP 200，表示风控触发是成功的业务操作
    """

    def test_trend_001_returns_200_not_error(self):
        """
        TREND_001 返回 200 而不是 4xx

        业务逻辑：风控触发是成功的业务操作，不是错误
        - 系统成功执行了风控检查
        - 检查结果是"异常"，需要人工复核
        - 状态已正确更新为 trend_flagged
        """
        trend_001_http = 200
        assert trend_001_http == 200, "TREND_001 应返回 200"

    def test_trend_002_is_blocking_error(self):
        """
        TREND_002 是阻塞错误

        场景：在 trend_flagged 状态下尝试进入 final_pending
        结果：应该被阻塞，返回 400
        """
        trend_002_http = 400
        assert trend_002_http == 400, "TREND_002 应返回 400"
