"""
项目模板服务测试模块
测试 backend/services/project_template_service.py 的模板管理功能

状态: 暂时禁用
原因: ProjectTemplate 模型未实现
TODO: 实现 backend/models/core/project_template.py 后启用此测试
"""

import pytest

# 暂时跳过所有测试，因为 ProjectTemplate 模型未实现
# 注意: skip marker 必须在 imports 之前，否则 import 错误会先触发
pytestmark = pytest.mark.skip(reason="ProjectTemplate 模型未实现，待补充实现")
