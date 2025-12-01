# -*- coding: utf-8 -*-
"""
backend/tests/integration - L1 集成测试层

测试特征:
- 使用测试数据库（SQLite in-memory）
- 测试服务层与数据层交互
- 执行速度 < 500ms/用例

pytest marker: @pytest.mark.integration
基准文档: AUTOMATION_TEST_SPEC_v1.4.md 第 2.2 节
"""
