# -*- coding: utf-8 -*-
"""
backend/tests/api - L2 API 测试层

测试特征:
- 使用 TestClient 测试 HTTP 接口
- 验证请求/响应格式
- 测试认证和权限
- 执行速度 < 1s/用例

pytest marker: @pytest.mark.api
基准文档: AUTOMATION_TEST_SPEC_v1.4.md 第 2.3 节
SoT 依赖: API_SOT.md v9.0
"""
