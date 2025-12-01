# -*- coding: utf-8 -*-
"""
backend/tests/unit - L0 单元测试层

测试特征:
- 无外部依赖（数据库、网络、文件系统）
- 使用 mock 隔离依赖
- 执行速度 < 100ms/用例

pytest marker: @pytest.mark.unit
基准文档: AUTOMATION_TEST_SPEC_v1.4.md 第 2.1 节
"""
